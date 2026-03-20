import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests, base64, time

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# --- NHÃN CỘT ---
L_DATE, L_LH, L_PK, L_MA = "Ngày lên hàng", "Loại hình", "Phân khu", "Mã căn"
L_DT, L_TANG, L_NT, L_HBC = "Diện tích", "Khoảng tầng", "Nội thất", "Hướng BC"
L_GIA, L_HT, L_TT, L_IMG = "Giá bán", "Hiện trạng", "Trạng thái", "Link ảnh"
L_TYPE, L_GC = "Phân loại", "Ghi chú"
V_SOLD, V_RENT = "Đã bán", "Đã thuê"

# --- HÀM XỬ LÝ CHUYỂN ẢNH (CALLBACK) ---
def change_img(step, total):
    st.session_state.ci = (st.session_state.get('ci', 0) + step) % total

@st.cache_resource
def load_data():
    try:
        s = st.secrets["gcp_service_account"]
        sc = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        c = ServiceAccountCredentials.from_json_keyfile_dict(s, sc); g = gspread.authorize(c)
        ss = g.open_by_key("19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk")
        sh = ss.get_worksheet(0); r = sh.get_all_values()
        if not r: return pd.DataFrame(), None
        h = [x.strip() for x in r[0]]; df = pd.DataFrame(r[1:], columns=h)
        df['sheet_row'] = range(2, len(df) + 2)
        df[L_GIA] = pd.to_numeric(df[L_GIA], errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except: return pd.DataFrame(), None

df_raw, sh_obj = load_data()
if 'is_login' not in st.session_state: st.session_state.is_login = False
is_adm = st.session_state.is_login

# --- DIALOG CHI TIẾT ---
@st.dialog("Chi tiết căn hộ")
def show_dt(row, ks):
    mid = str(row.get(L_MA, "0"))
    cl1, cl2 = st.columns([1.2, 1])
    with cl1:
        imgs = str(row.get(L_IMG, "")).split(',') if row.get(L_IMG) else []
        if imgs and imgs[0]:
            if 'ci' not in st.session_state: st.session_state.ci = 0
            total = len(imgs)
            ix = st.session_state.ci % total
            st.image(imgs[ix], use_container_width=True, caption=f"Ảnh {ix+1}/{total}")
            
            if total > 1:
                b1, b2 = st.columns(2)
                with b1:
                    st.button("⬅️ Trước", key=f"p_{mid}", on_click=change_img, args=(-1, total))
                with b2:
                    st.button("Sau ➡️", key=f"n_{mid}", on_click=change_img, args=(1, total))
        else: st.info("Không có ảnh")
    with cl2:
        st.subheader(f"{row[L_LH]} - {row[L_PK]}")
        st.success(f"💰 Giá: {row[L_GIA]} Tỷ")
        st.write(f"📐 **Diện tích:** {row[L_DT]}m²")
        st.write(f"🧭 **Hướng BC:** {row[L_HBC]}")
        st.write(f"🧱 **Tầng:** {row[L_TANG]} | **Nội thất:** {row[L_NT]}")
        st.write(f"🚧 **Hiện trạng:** {row[L_HT]}")
        if row.get(L_GC): st.info(f"Ghi chú: {row[L_GC]}")
        
        if is_adm:
            st.divider(); ck = f"ck_{mid}"
            if not st.session_state.get(ck, False):
                if st.button("✅ ĐÃ CHỐT", use_container_width=True, type="primary", key=f"bt_{mid}"):
                    st.session_state[ck] = True; st.rerun()
            else:
                st.warning("Xác nhận chốt?"); cy, cn = st.columns(2)
                with cy:
                    if st.button("OK", type="primary", use_container_width=True, key=f"ok_{mid}"):
                        c_idx = list(df_raw.columns).index(L_TT) + 1
                        sh_obj.update_cell(int(row['sheet_row']), c_idx, V_SOLD if ks=="B" else V_RENT)
                        st.session_state[ck] = False; st.cache_resource.clear(); st.rerun()
                with cn:
                    if st.button("Hủy", use_container_width=True, key=f"no_{mid}"):
                        st.session_state[ck] = False; st.rerun()
        st.code(f"Mã: {mid if is_adm else 'Ẩn'}")

# --- GIAO DIỆN CHÍNH ---
h1, h2 = st.columns([7, 3])
with h1: st.title("🏢 Vinhomes Manager")
with h2:
    if not is_adm:
        p = st.text_input("Admin", type="password", label_visibility="collapsed", key="login_pass")
        if p == "admin123": st.session_state.is_login = True; st.rerun()
    else:
        st.info("✅ Admin")
        ca1, ca2 = st.columns(2)
        with ca1:
            if st.button("Ref", key="btn_ref"): st.cache_resource.clear(); st.rerun()
        with ca2:
            if st.button("Out", key="btn_out"): st.session_state.is_login = False; st.rerun()

if sh_obj is not None and not df_raw.empty:
    t1, t2, t3 = st.tabs(["🔴 Chuyển nhượng", "🟢 Cho thuê", "➕ Thêm hàng"])
    
    def draw(df_in, ks):
        df_a = df_in[~df_in[L_TT].astype(str).str.contains("Đã", na=False)]
        c1, c2, c3 = st.columns([3, 3, 4])
        with c1: pk = st.multiselect("Phân khu", sorted(df_in[L_PK].unique()), key=f"p{ks}")
        with c2: lh = st.multiselect("Loại hình", sorted(df_in[L_LH].unique()), key=f"l{ks}")
        with c3:
            mi, ma = float(df_in[L_GIA].min()), float(df_in[L_GIA].max())
            r_gia = st.slider("Giá (Tỷ)", mi, ma, (mi, ma), key=f"g{ks}")
        
        if pk: df_a = df_a[df_a[L_PK].isin(pk)]
        if lh: df_a = df_a[df_a[L_LH].isin(lh)]
        df_a = df_a[(df_a[L_GIA] >= r_gia[0]) & (df_a[L_GIA] <= r_gia[1])]
        
        v_cols = [L_DATE, L_LH, L_PK, L_DT, L_GIA, L_TT]
        if is_adm: v_cols.append(L_MA)
        sel = st.dataframe(df_a[v_cols], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key=f"df{ks}")
        if sel and sel.selection.rows:
            # Reset index ảnh về 0 khi chọn căn mới
            row_sel = df_a.iloc[sel.selection.rows[0]]
            if st.session_state.get('last_ma') != row_sel[L_MA]:
                st.session_state.ci = 0
                st.session_state.last_ma = row_sel[L_MA]
            show_dt(row_sel, ks)

    with t1: draw(df_raw[df_raw[L_TYPE].astype(str).str.contains("Bán|Ban", na=False)], "B")
    with t2: draw(df_raw[df_raw[L_TYPE].astype(str).str.contains("Thuê|Thue", na=False)], "T")
    with t3:
        if is_adm:
            with st.form("f_add", clear_on_submit=True):
                tp = st.radio("Loại", ["Bán", "Cho thuê"], horizontal=True)
                i1, i2, i3 = st.columns(3)
                with i1:
                    v_lh = st.selectbox(L_LH, ["Studio", "1PN+", "2PN", "2PN+", "3N"])
                    v_ma = st.text_input(L_MA)
                with i2:
                    v_pk = st.selectbox(L_PK, ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
                    v_dt = st.number_input(L_DT, 0.0)
                with i3:
                    v_gi = st.number_input(L_GIA, step=0.1)
                    v_ht = st.selectbox(L_HT, ["Đang ở", "Để trống", "Cho thuê"])
                v_gc = st.text_input(L_GC); up = st.file_uploader("Ảnh", accept_multiple_files=True)
                if st.form_submit_button("🚀 ĐĂNG CĂN"):
                    if v_ma:
                        imgs = up_img(up)
                        try:
                            h = list(df_raw.columns); row_d = [""] * len(h)
                            dm = {L_TYPE:tp, L_DATE:str(pd.Timestamp.now().date()), L_LH:v_lh, L_PK:v_pk, L_MA:v_ma, L_DT:v_dt, L_GIA:v_gi, L_HT:v_ht, L_GC:v_gc, L_TT:"Đang bán", L_IMG:imgs}
                            for i, col in enumerate(h):
                                if col in dm: row_d[i] = dm[col]
                            sh_obj.append_row(row_d); st.cache_resource.clear(); st.rerun()
                        except: st.error("Lỗi Sheets")
