import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests, base64

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# NHÃN CỘT - Phải khớp chính xác 100% với dòng 1 của Google Sheets
L_DATE = "Ngày lên hàng"
L_LH = "Loại hình"
L_PK = "Phân khu"
L_MA = "Mã căn"
L_DT = "Diện tích"
L_TANG = "Khoảng tầng"
L_NT = "Nội thất"
L_HBC = "Hướng BC"
L_GIA = "Giá bán"
L_HT = "Hiện trạng"
L_TT = "Trạng thái"
L_IMG = "Link ảnh"
L_TYPE = "Phân loại"
L_GC = "Ghi chú"

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
        s = st.secrets["gcp_service_account"]
        sc = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        c = ServiceAccountCredentials.from_json_keyfile_dict(s, sc)
        g = gspread.authorize(c)
        ss = g.open_by_key("19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk")
        sh = ss.get_worksheet(0)
        r = sh.get_all_values()
        if not r or len(r) < 1: return pd.DataFrame(), sh
        # Làm sạch tiêu đề (xóa khoảng trắng thừa)
        cols = [h.strip() for h in r[0]]
        df = pd.DataFrame(r[1:], columns=cols)
        df[L_GIA] = pd.to_numeric(df[L_GIA], errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except: return pd.DataFrame(), None

df_raw, sh_obj = load_data()
if 'is_login' not in st.session_state: st.session_state.is_login = False

# --- HEADER & ADMIN LOGIN ---
h1, h2 = st.columns([7, 3])
with h1: st.title("🏢 Vinhomes Manager")
with h2:
    if not st.session_state.is_login:
        p = st.text_input("Pass...", type="password", label_visibility="collapsed")
        if p == "admin123": st.session_state.is_login = True; st.rerun()
    else:
        c_adm1, c_adm2 = st.columns([4, 1])
        with c_adm1: st.write("✅ Admin")
        with c_adm2:
            if st.button("❌", help="Đăng xuất"): 
                st.session_state.is_login = False
                st.cache_resource.clear()
                st.rerun()

is_adm = st.session_state.is_login

if sh_obj is not None:
    t1, t2, t3 = st.tabs(["🔴 Chuyển nhượng", "🟢 Cho thuê", "➕ Thêm hàng"])
    
    def draw(df_in, ks):
        # Lọc trạng thái (Chỉ lấy căn chưa chốt)
        df_a = df_in[~df_in[L_TT].astype(str).str.contains("Đã", na=False)]
        if df_a.empty:
            st.info("Trống."); return

        # --- BỘ LỌC ---
        c1, c2, c3 = st.columns([3, 3, 4])
        with c1: pk = st.multiselect("Phân khu", sorted(df_in[L_PK].unique()), key=f"p{ks}")
        with c2: lh = st.multiselect("Loại hình", sorted(df_in[L_LH].unique()), key=f"l{ks}")
        with c3:
            min_v = float(df_in[L_GIA].min())
            max_v = float(df_in[L_GIA].max())
            r_gia = st.slider("Giá (Tỷ)", min_v, max_v, (min_v, max_v), key=f"g{ks}")
        
        if pk: df_a = df_a[df_a[L_PK].isin(pk)]
        if lh: df_a = df_a[df_a[L_LH].isin(lh)]
        df_a = df_a[(df_a[L_GIA] >= r_gia[0]) & (df_a[L_GIA] <= r_gia[1])]

        st.write(f"Có {len(df_a)} căn")
        v_cols = [L_DATE, L_LH, L_PK, L_MA, L_DT, L_TANG, L_NT, L_HBC, L_GIA, L_HT, L_TT]
        if not is_adm: v_cols.remove(L_MA)
        
        sel = st.dataframe(df_a[v_cols], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key=f"d{ks}")

        @st.dialog("Chi tiết căn hộ")
        def show_dt(row):
            cl1, cl2 = st.columns([1.2, 1])
            with cl1:
                imgs = str(row.get(L_IMG, "")).split(',') if row.get(L_IMG) else []
                if imgs and imgs[0]:
                    if 'ci' not in st.session_state: st.session_state.ci = 0
                    ix = st.session_state.ci % len(imgs); st.image(imgs[ix], use_container_width=True)
                    if len(imgs) > 1:
                        b1, b2 = st.columns(2)
                        with b1: 
                            if st.button("⬅️", key=f"prev{ks}"): st.session_state.ci -= 1; st.rerun()
                        with b2:
                            if st.button("➡️", key=f"next{ks}"): st.session_state.ci += 1; st.rerun()
                else: st.info("Không ảnh")
            with cl2:
                st.subheader(f"{row[L_LH]} - {row[L_PK]}")
                st.success(f"Giá: {row[L_GIA]} Tỷ")
                st.write(f"Mã căn: {row[L_MA]}")
                if is_adm:
                    st.divider()
                    ck = f"cf_{row[L_MA]}"
                    if ck not in st.session_state: st.session_state[ck] = False
                    if not st.session_state[ck]:
                        if st.button("✅ CHỐT CĂN", use_container_width=True, type="primary", key=f"bc{ks}"):
                            st.session_state[ck] = True; st.rerun()
                    else:
                        st.warning("Xác nhận chốt?")
                        cy, cn = st.columns(2)
                        with cy:
                            if st.button("OK", use_container_width=True, type="primary", key=f"y{ks}"):
                                try:
                                    # Lấy tiêu đề thực tế từ Sheets để tìm chỉ số cột
                                    header_row = sh_obj.row_values(1)
                                    header_cleaned = [h.strip() for h in header_row]
                                    
                                    # Tìm vị trí cột Mã căn và Trạng thái
                                    idx_ma = header_cleaned.index(L_MA) + 1
                                    idx_tt = header_cleaned.index(L_TT) + 1
                                    
                                    # Tìm số hàng của căn hộ dựa trên mã căn
                                    all_ma = sh_obj.col_values(idx_ma)
                                    row_num = all_ma.index(str(row[L_MA])) + 1
                                    
                                    # Cập nhật trạng thái
                                    new_val = "Đã bán" if ks == "B" else "Đã thuê"
                                    sh_obj.update_cell(row_num, idx_tt, new_val)
                                    
                                    st.session_state[ck] = False
                                    st.cache_resource.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Lỗi Sheets: {str(e)}")
                        with cn:
                            if st.button("Hủy", use_container_width=True, key=f"n{ks}"):
                                st.session_state[ck] = False; st.rerun()
                st.code(f"Phân khu: {row[L_PK]}\nLoại hình: {row[L_LH]}\nHướng: {row[L_HBC]}")

        if sel and sel.selection.rows:
            st.session_state.ci = 0
            show_dt(df_a.iloc[sel.selection.rows[0]])

    with t1: draw(df_raw[df_raw[L_TYPE].str.contains("Bán|Ban", na=False)], "B")
    with t2: draw(df_raw[df_raw[L_TYPE].str.contains("thuê|thue", na=False, case=False)], "T")
    with t3:
        if is_adm:
            with st.form("f_add", clear_on_submit=True):
                tp = st.radio("Loại", ["Bán", "Cho thuê"], horizontal=True)
                i1, i2, i3 = st.columns(3)
                with i1:
                    v_lh = st.selectbox(L_LH, ["Studio", "1PN+", "2PN", "2PN+", "3N"])
                    v_pk = st.selectbox(L_PK, ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
                    v_ma = st.text_input(L_MA)
                with i2:
                    v_dt = st.number_input(L_DT, 0.0)
                    v_tg = st.selectbox(L_TANG, ["Thấp", "Trung", "Cao"])
                    v_hb = st.selectbox(L_HBC, ["Đông", "Tây", "Nam", "Bắc", "ĐB", "ĐN", "TB", "TN"])
                with i3:
                    v_nt = st.selectbox(L_NT, ["Nguyên bản", "Cơ bản", "Full đồ"])
                    v_gi = st.number_input(L_GIA, step=0.1)
                    v_ht = st.selectbox(L_HT, ["Đang ở", "Để trống", "Cho thuê"])
                v_gc = st.text_input(L_GC)
                up = st.file_uploader("Ảnh", accept_multiple_files=True)
                if st.form_submit_button("🚀 ĐĂNG CĂN"):
                    imgs = up_img(up)
                    try:
                        header = [h.strip() for h in sh_obj.row_values(1)]
                        new_row = [""] * len(header)
                        data_map = {
                            L_TYPE: tp, 
                            L_DATE: str(pd.Timestamp.now().date()), 
                            L_LH: v_lh, L_PK: v_pk, L_MA: v_ma, 
                            L_DT: v_dt, L_TANG: v_tg, L_HBC: v_hb, 
                            L_NT: v_nt, L_GIA: v_gi, L_HT: v_ht, 
                            L_GC: v_gc, L_TT: "Đang bán"
                        }
                        for i, col in enumerate(header):
                            if col in data_map: new_row[i] = data_map[col]
                        sh_obj.append_row(new_row)
                        st.success("Đăng thành công!"); st.cache_resource.clear(); st.rerun()
                    except Exception as e: st.error(f"Lỗi: {str(e)}")
        else: st.warning("Đăng nhập Admin để dùng tính năng này")
