import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests, base64

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# KHAI BÁO NHÃN (Tách nhỏ để không bị ngắt dòng)
L_DATE = "Ngày" + " lên" + " hàng"
L_LH = "Loại" + " hình"
L_PK = "Phân" + " khu"
L_MA = "Mã" + " căn"
L_DT = "Diện" + " tích"
L_TANG = "Khoảng" + " tầng"
L_NT = "Nội" + " thất"
L_HBC = "Hướng" + " BC"
L_GIA = "Giá" + " bán"
L_HT = "Hiện" + " trạng"
L_TT = "Trạng" + " thái"
L_IMG = "Link" + " ảnh"
L_TYPE = "Phân" + " loại"
L_GC = "Ghi" + " chú"

V_SOLD = "Đã" + " bán"
V_RENT = "Đã" + " thuê"

def up_img(fs):
    if not fs: return ""
    try:
        ak = st.secrets.get("imgbb_api_key")
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
        h = [x.strip() for x in r[0]]; df = pd.DataFrame(r[1:], columns=h)
        df['sheet_row'] = range(2, len(df) + 2)
        df[L_GIA] = pd.to_numeric(df[L_GIA], errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except: return pd.DataFrame(), None

df_raw, sh_obj = load_data()
if 'is_login' not in st.session_state: st.session_state.is_login = False

# --- HEADER CHUẨN ---
h1, h2 = st.columns([7, 3])
with h1: st.title("🏢 Vinhomes Manager")
with h2:
    if not st.session_state.is_login:
        p = st.text_input("Mật khẩu", type="password", label_visibility="collapsed")
        if p == "admin123":
            st.session_state.is_login = True
            st.rerun()
    else:
        st.info("✅ Admin Mode")
        ca1, ca2 = st.columns(2)
        with ca1:
            if st.button("🔄 Ref"): st.cache_resource.clear(); st.rerun()
        with ca2:
            if st.button("❌ Out"): st.session_state.is_login = False; st.rerun()

is_adm = st.session_state.is_login
if sh_obj is not None and not df_raw.empty:
    t1, t2, t3 = st.tabs(["🔴 Chuyển nhượng", "🟢 Cho thuê", "➕ Thêm hàng"])
    
    def draw(df_in, ks):
        df_a = df_in[~df_in[L_TT].astype(str).str.contains("Đã", na=False)]
        if df_a.empty: st.info("Trống."); return
        
        st.markdown("### 🔍 Tìm & Lọc")
        s_ma = st.text_input("Mã căn...", key=f"s{ks}").strip()
        
        # QUAY LẠI GIAO DIỆN HÀNG NGANG
        c1, c2, c3 = st.columns([3, 3, 4])
        with c1: pk = st.multiselect("Phân khu", sorted(df_in[L_PK].unique()), key=f"p{ks}")
        with c2: lh = st.multiselect("Loại hình", sorted(df_in[L_LH].unique()), key=f"l{ks}")
        with c3:
            mi, ma = float(df_in[L_GIA].min()), float(df_in[L_GIA].max())
            r_gia = st.slider("Giá (Tỷ)", mi, ma, (mi, ma), key=f"g{ks}")
        
        if s_ma: df_a = df_a[df_a[L_MA].astype(str).str.contains(s_ma, case=False, na=False)]
        if pk: df_a = df_a[df_a[L_PK].isin(pk)]
        if lh: df_a = df_a[df_a[L_LH].isin(lh)]
        df_a = df_a[(df_a[L_GIA] >= r_gia[0]) & (df_a[L_GIA] <= r_gia[1])]

        v_cols = [L_DATE, L_LH, L_PK, L_DT, L_GIA, L_TT]
        if is_adm: v_cols.append(L_MA)
        
        sel = st.dataframe(df_a[v_cols], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key=f"df{ks}")

        @st.dialog("Chi tiết căn hộ")
        def show_dt(row):
            mid = str(row.get(L_MA, "0"))
            cl1, cl2 = st.columns([1.2, 1])
            with cl1:
                imgs = str(row.get(L_IMG, "")).split(',') if row.get(L_IMG) else []
                if imgs and imgs[0]:
                    if 'ci' not in st.session_state: st.session_state.ci = 0
                    ix = st.session_state.ci % len(imgs); st.image(imgs[ix], use_container_width=True)
                    if len(imgs) > 1:
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("⬅️", key=f"p_{mid}_{ks}"): st.session_state.ci -= 1; st.rerun()
                        with b2:
                            if st.button("➡️", key=f"n_{mid}_{ks}"): st.session_state.ci += 1; st.rerun()
                else: st.info("Không ảnh")
            with cl2:
                st.subheader(f"{row[L_LH]} - {row[L_PK]}")
                st.success(f"Giá: {row[L_GIA]} Tỷ")
                if is_adm:
                    st.divider(); ck = f"ck_{mid}"
                    if ck not in st.session_state: st.session_state[ck] = False
                    if not st.session_state[ck]:
                        if st.button("✅ CHỐT CĂN", use_container_width=True, type="primary", key=f"bt_{mid}"): 
                            st.session_state[ck] = True; st.rerun()
                    else:
                        st.warning("Xác nhận?"); cy, cn = st.columns(2)
                        with cy:
                            if st.button("OK", type="primary", key=f"y_{mid}"):
                                try:
                                    h = [x.strip() for x in sh_obj.row_values(1)]; idx = h.index(L_TT) + 1
                                    sh_obj.update_cell(int(row['sheet_row']), idx, V_SOLD if ks=="B" else V_RENT)
                                    st.session_state[ck] = False; st.cache_resource.clear(); st.rerun()
                                except: st.error("Lỗi")
                        with cn:
                            if st.button("Hủy", key=f"n_{mid}"): st.session_state[ck]=False; st.rerun()
                st.code(f"Mã: {mid}\nGhi chú: {row.get(L_GC, '')}")
        if sel and sel.selection.rows: st.session_state.ci = 0; show_dt(df_a.iloc[sel.selection.rows[0]])

    with t1: draw(df_raw[df_raw[L_TYPE].astype(str).str.contains("Bán|Ban|bán|ban", na=False)], "B")
    with t2: draw(df_raw[df_raw[L_TYPE].astype(str).str.contains("Thuê|Thue|thuê|thue", na=False)], "T")
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
                            h = [x.strip() for x in sh_obj.row_values(1)]; row_d = [""] * len(h)
                            dm = {L_TYPE:tp, L_DATE:str(pd.Timestamp.now().date()), L_LH:v_lh, L_PK:v_pk, L_MA:v_ma, L_DT:v_dt, L_GIA:v_gi, L_HT:v_ht, L_GC:v_gc, L_TT:"Đang bán", L_IMG:imgs}
                            for i, col in enumerate(h):
                                if col in dm: row_d[i] = dm[col]
                            sh_obj.append_row(row_d); st.cache_resource.clear(); st.rerun()
                        except: st.error("Lỗi")
