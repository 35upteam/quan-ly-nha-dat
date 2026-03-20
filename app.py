import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests, base64

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# KHAI BÁO BIẾN NGẮN
L_DATE, L_LH, L_PK, L_MA = "Ngày lên hàng", "Loại hình", "Phân khu", "Mã căn"
L_DT, L_TANG, L_NT, L_HBC = "Diện tích", "Khoảng tầng", "Nội thất", "Hướng BC"
L_GIA, L_HT, L_TT, L_IMG, L_TYPE, L_GC = "Giá bán", "Hiện trạng", "Trạng thái", "Link ảnh", "Phân loại", "Ghi chú"

T_DONE = "Đã"
V_SOLD = f"{T_DONE} bán"
V_RENT = f"{T_DONE} thuê"

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
        cols = [h.strip() for h in r[0]]; df = pd.DataFrame(r[1:], columns=cols)
        df['sheet_row'] = range(2, len(df) + 2)
        df[L_GIA] = pd.to_numeric(df[L_GIA], errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except: return pd.DataFrame(), None

df_raw, sh_obj = load_data()
if 'is_login' not in st.session_state: st.session_state.is_login = False

# --- HEADER ---
h1, h2 = st.columns([7, 3])
with h1: st.title("🏢 Vinhomes Manager")
with h2:
    if not st.session_state.is_login:
        p = st.text_input("Pass", type="password", label_visibility="collapsed")
        if p == "admin123": st.session_state.is_login = True; st.rerun()
    else:
        st.info("✅ Admin")
        if st.button("🔄 Làm mới"): st.cache_resource.clear(); st.rerun()

is_adm = st.session_state.is_login
if sh_obj is not None:
    t1, t2, t3 = st.tabs(["🔴 Bán", "🟢 Thuê", "➕ Thêm hàng"])
    
    def draw(df_in, ks):
        df_a = df_in[~df_in[L_TT].astype(str).str.contains(T_DONE, na=False)]
        if df_a.empty: st.info("Trống."); return
        st.markdown("### 🔍 Tìm kiếm")
        s_ma = st.text_input("Mã căn...", key=f"s{ks}").strip()
        c1, c2, c3 = st.columns([3, 3, 4])
        with c1: pk = st.multiselect("Khu", sorted(df_in[L_PK].unique()), key=f"p{ks}")
        with c2: lh = st.multiselect("Loại", sorted(df_in[L_LH].unique()), key=f"l{ks}")
        with c3:
            mi, ma = float(df_in[L_GIA].min()), float(df_in[L_GIA].max())
            r_gia = st.slider("Giá", mi, ma, (mi, ma), key=f"g{ks}")
        if s_ma: df_a = df_a[df_a[L_MA].astype(str).str.contains(s_ma, case=False, na=False)]
        if pk: df_a = df_a[df_a[L_PK].isin(pk)]
        if lh: df_a = df_a[df_a[L_LH].isin(lh)]
        df_a = df_a[(df_a[L_GIA] >= r_gia[0]) & (df_a[L_GIA] <= r_gia[1])]

        # FIX LỖI TRIỆT ĐỂ TẠI ĐÂY: Dùng Append thay vì List dài
        v_cols = []
        v_cols.append(L_DATE)
        v_cols.append(L_LH)
        v_cols.append(L_PK)
        v_cols.append(L_DT)
        v_cols.append(L_TANG)
        v_cols.append(L_NT)
        v_cols.append(L_HBC)
        v_cols.append(L_GIA)
        v_cols.append(L_HT)
        v_cols.append(L_TT)
        if is_adm: v_cols.append(L_MA)
        
        sel = st.dataframe(df_a[v_cols], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key=f"d{ks}")

        @st.dialog("Chi tiết")
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
                            if st.button("⬅️", key=f"p{ks}"): st.session_state.ci -= 1; st.rerun()
                        with b2:
                            if st.button("➡️", key=f"n{ks}"): st.session_state.ci += 1; st.rerun()
                else: st.info("Không ảnh")
            with cl2:
                st.subheader(f"{row[L_LH]} - {row[L_PK]}")
                st.success(f"Giá: {row[L_GIA]} Tỷ")
                if is_adm:
                    st.divider(); ck = f"c_{row[L_MA]}"
                    if ck not in st.session_state: st.session_state[ck] = False
                    if not st.session_state[ck]:
                        if st.button("✅ CHỐT CĂN", use_container_width=True, type="primary"): st.session_state[ck] = True; st.rerun()
                    else:
                        st.warning("Chốt?"); cy, cn = st.columns(2)
                        with cy:
                            if st.button("OK", type="primary", use_container_width=True):
                                try:
                                    h = [x.strip() for x in sh_obj.row_values(1)]; idx = h.index(L_TT) + 1
                                    sh_obj.update_cell(int(row['sheet_row']), idx, V_SOLD if ks == "B" else V_RENT)
                                    st.session_state[ck] = False; st.cache_resource.clear(); st.toast("Xong!"); st.rerun()
                                except: st.error("Lỗi")
                        with cn:
                            if st.button("Hủy", use_container_width=True): st.session_state[ck] = False; st.rerun()
                st.code(f"Mã: {row.get(L_MA, 'Ẩn')}\nGhi chú: {row.get(L_GC, '')}")
        if sel and sel.selection.rows: st.session_state.ci = 0; show_dt(df_a.iloc[sel.selection.rows[0]])

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
                    v_dt = st.number_input(L_DT, 0.0); v_tg = st.selectbox(L_TANG, ["Thấp", "Trung", "Cao"])
                    v_hb = st.selectbox(L_HBC, ["Đông", "Tây", "Nam", "Bắc", "ĐB", "ĐN", "TB", "TN"])
                with i3:
                    v_nt = st.selectbox(L_NT, ["Nguyên bản", "Cơ bản", "Full đồ"])
                    v_gi = st.number_input(L_GIA, step=0.1); v_ht = st.selectbox(L_HT, ["Đang ở", "Để trống", "Cho thuê"])
                v_gc = st.text_input(L_GC); up = st.file_uploader("Ảnh", accept_multiple_files=True)
                if st.form_submit_button("🚀 ĐĂNG"):
                    if not v_ma: st.error("Mã!"); st.stop()
                    imgs = up_img(up)
                    try:
                        h = [x.strip() for x in sh_obj.row_values(1)]; row = [""] * len(h)
                        dm = {L_TYPE:tp, L_DATE:str(pd.Timestamp.now().date()), L_LH:v_lh, L_PK:v_pk, L_MA:v_ma, L_DT:v_dt, L_TANG:v_tg, L_HBC:v_hb, L_NT:v_nt, L_GIA:v_gi, L_HT:v_ht, L_GC:v_gc, L_TT:"Đang bán", L_IMG:imgs}
                        for i, col in enumerate(h):
                            if col in dm: row[i] = dm[col]
                        sh_obj.append_row(row); st.balloons(); st.success("Xong!"); st.cache_resource.clear()
                    except: st.error("Lỗi")
