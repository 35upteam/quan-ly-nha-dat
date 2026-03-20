import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests, base64

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# Khai báo nhãn khớp chính xác với tiêu đề cột trong ảnh của bạn
L_DATE, L_LH, L_PK, L_MA = "Ngày lên hàng", "Loại hình", "Phân khu", "Mã căn"
L_DT, L_TANG, L_NT, L_HBC = "Diện tích", "Khoảng tầng", "Nội thất", "Hướng BC"
L_GIA, L_HT, L_TT, L_IMG, L_TYPE = "Giá bán", "Hiện trạng", "Trạng thái", "Link ảnh", "Phân loại"

def up_img(fs):
    if not fs: return ""
    try:
        ak = st.secrets.get("imgbb_api_key") or st.secrets.get("gcp_service_account", {}).get("imgbb_api_key")
        res = []
        for f in fs:
            f.seek(0); b6 = base64.b64encode(f.read()).decode('utf-8')
            r = requests.post("https://api.imgbb.com/1/upload", {"key": ak, "image": b6}, timeout=20)
            if r.status_code == 200: res.append(r.json()['data']['thumb']['url']) 
        return ",".join(res)
    except: return ""

@st.cache_resource
def load_data():
    try:
        s = st.secrets["gcp_service_account"]; sc = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        c = ServiceAccountCredentials.from_json_keyfile_dict(s, sc); g = gspread.authorize(c)
        ss = g.open_by_key("19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk"); sh = ss.get_worksheet(0); r = sh.get_all_values()
        if not r or len(r) < 1: return pd.DataFrame(), sh
        df = pd.DataFrame(r[1:], columns=[h.strip() for h in r[0]])
        # Đảm bảo các cột số được định dạng đúng để lọc giá
        df[L_GIA] = pd.to_numeric(df[L_GIA], errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except: return pd.DataFrame(), None

df_raw, sh_obj = load_data()
if 'is_login' not in st.session_state: st.session_state.is_login = False

# --- GIAO DIỆN HEADER ---
col1, col2 = st.columns([8, 2])
with col1: st.title("🏢 Vinhomes Manager")
with col2:
    if not st.session_state.is_login:
        p = st.text_input("Pass...", type="password", label_visibility="collapsed")
        if p == "admin123": st.session_state.is_login = True; st.rerun()
    else:
        st.write("✅ Admin Mode")
        if st.button("🔄 Làm mới"): st.cache_resource.clear(); st.rerun()

is_adm = st.session_state.is_login

if sh_obj is not None:
    t1, t2, t3 = st.tabs(["🔴 Chuyển nhượng", "🟢 Cho thuê", "➕ Thêm hàng"])
    
    def draw(df_in, ks):
        # Lọc bỏ hàng đã chốt
        df_a = df_in[~df_in[L_TT].astype(str).str.contains("Đã", na=False)]
        if df_a.empty:
            st.info("Hiện không có hàng trong mục này."); return

        # --- BỘ LỌC ---
        c1, c2, c3 = st.columns([3, 3, 4])
        with c1: pk = st.multiselect("Phân khu", sorted(df_in[L_PK].unique()), key=f"p{ks}")
        with c2: lh = st.multiselect("Loại hình", sorted(df_in[L_LH].unique()), key=f"l{ks}")
        with c3:
            min_g, max_g = float(df_in[L_GIA].min()), float(df_in[L_GIA].max())
            r_gia = st.slider("Giá bán (Tỷ)", min_g, max_g, (min_g, max_g), key=f"g{ks}")
        
        if pk: df_a = df_a[df_a[L_PK].isin(pk)]
        if lh: df_a = df_a[df_a[L_LH].isin(lh)]
        df_a = df_a[(df_a[L_GIA] >= r_gia[0]) & (df_a[L_GIA] <= r_gia[1])]

        st.write(f"Tìm thấy {len(df_a)} căn")
        # Ẩn cột kỹ thuật đối với khách
        v_cols = [L_DATE, L_LH, L_PK, L_MA, L_DT, L_TANG, L_NT, L_HBC, L_GIA, L_HT, L_TT]
        if not is_adm: v_cols.remove(L_MA) # Khách không xem được mã căn
        
        sel = st.dataframe(df_a[v_cols], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key=f"d{ks}")

        @st.dialog("Chi tiết căn hộ")
        def show_dt(row):
            cl1, cl2 = st.columns([1.2, 1])
            with cl1:
                imgs = str(row.get(L_IMG, "")).split(',') if row.get(L_IMG) else []
                if imgs and imgs[0]:
                    if 'ci' not in st.session_state: st.session_state.ci = 0
                    idx = st.session_state.ci % len(imgs)
                    st.image(imgs[idx], use_container_width=True)
                    if len(imgs) > 1:
                        b1, b2 = st.columns(2)
                        with b1: 
                            if st.button("⬅️", key=f"prev{ks}"): st.session_state.ci -= 1; st.rerun()
                        with b2:
                            if st.button("➡️", key=f"next{ks}"): st.session_state.ci += 1; st.rerun()
                else: st.info("Không có ảnh")
            with cl2:
                st.subheader(f"{row[L_LH]} - {row[L_PK]}")
                st.write(f"**Giá:** {row[L_GIA]} Tỷ")
                st.write(f"**Hướng:** {row[L_HBC]} | **Tầng:** {row[L_TANG]}")
                st.write(f"**Nội thất:** {row[L_NT]}")
                if is_adm:
                    st.divider()
                    ck = f"cf_{row[L_MA]}"
                    if ck not in st.session_state: st.session_state[ck] = False
                    if not st.session_state[ck]:
                        if st.button("✅ ĐÃ CHỐT CĂN", use_container_width=True, type="primary", key=f"bc{ks}"):
                            st.session_state[ck] = True; st.rerun()
                    else:
                        st.warning("Xác nhận chốt căn này?")
                        cy, cn = st.columns(2)
                        with cy:
                            if st.button("Xác nhận", use_container_width=True, type="primary", key=f"y{ks}"):
                                try:
                                    h = [x.strip() for x in sh_obj.row_values(1)]
                                    ids = sh_obj.col_values(h.index(L_MA)+1)
                                    ridx = ids.index(row[L_MA])+1
                                    nv = "Đã bán" if ks == "B" else "Đã thuê"
                                    sh_obj.update_cell(ridx, h.index(L_TT)+1, nv)
                                    st.session_state[ck] = False; st.cache_resource.clear(); st.rerun()
                                except: st.error("Lỗi cập nhật Sheets")
                        with cn:
                            if st.button("Hủy", use_container_width=True, key=f"n{ks}"):
                                st.session_state[ck] = False; st.rerun()

        if sel and sel.selection.rows:
            st.session_state.ci = 0
            show_dt(df_a.iloc[sel.selection.rows[0]])

    with t1: draw(df_raw[df_raw[L_TYPE].str.contains("Bán|Ban", na=False)], "B")
