import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests, base64

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

L_TYPE, L1, L2, L3 = "Phân loại", "Phân khu", "Loại hình", "Mã căn"
L4, L5, L6, L7, L8, L9 = "Diện tích", "Khoảng tầng", "Nội thất", "Hướng BC", "Giá bán", "Link ảnh"
L10, L11, L12 = "Hiện trạng", "Ghi chú", "Trạng thái"

PK_L = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
LH_L = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
H_L = ["Đông", "Tây", "Nam", "Bắc", "ĐB", "ĐN", "TB", "TN"]
NT_L = ["Nguyên bản", "Cơ bản", "Full đồ"]
TG_L = ["Thấp", "Trung", "Cao"]
HT_L = ["Đang ở", "Đang cho thuê", "Để trống"]

def up_img(fs):
    if not fs: return ""
    try:
        ak = st.secrets.get("imgbb_api_key") or st.secrets.get("gcp_service_account", {}).get("imgbb_api_key")
        res_ls = []
        for f in fs:
            f.seek(0); b6 = base64.b64encode(f.read()).decode('utf-8')
            r = requests.post("https://api.imgbb.com/1/upload", {"key": ak, "image": b6}, timeout=20)
            if r.status_code == 200: res_ls.append(r.json()['data']['thumb']['url']) 
        return ",".join(res_ls)
    except: return ""

@st.cache_resource
def load_data():
    try:
        s = st.secrets["gcp_service_account"]; sc = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        c = ServiceAccountCredentials.from_json_keyfile_dict(s, sc); g = gspread.authorize(c)
        ss = g.open_by_key("19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk"); sh = ss.get_worksheet(0); r = sh.get_all_values()
        if not r or len(r) < 1: return pd.DataFrame(), sh
        df = pd.DataFrame(r[1:], columns=[h.strip() for h in r[0]])
        for cn in [L_TYPE, L1, L2, L3, L8, L12]:
            if cn not in df.columns: df[cn] = ""
        return df.iloc[::-1].reset_index(drop=True), sh
    except: return pd.DataFrame(), None

df_raw, sh_obj = load_data()
if 'is_login' not in st.session_state: st.session_state.is_login = False

h1, h2 = st.columns([7, 3])
with h1: st.title("🏢 Vinhomes Manager")
with h2:
    s1, s2 = st.columns([5, 1])
    with s1:
        if not st.session_state.is_login:
            p = st.text_input("P", type="password", label_visibility="collapsed")
            if p == "admin123": st.session_state.is_login = True; st.rerun()
        else: st.write("Admin ✅")
    with s2:
        if st.button("🔄"): st.cache_resource.clear(); st.rerun()

is_adm = st.session_state.is_login

if sh_obj is not None:
    t1, t2, t3 = st.tabs(["🔴 Bán", "🟢 Thuê", "➕ Thêm"])
    def draw(df_in, ks):
        df_a = df_in[~df_in[L12].astype(str).str.contains("Đã", na=False)]
        if df_a.empty: 
            st.info("Trống"); return
        ca, cb = st.columns(2)
        with ca: pk = st.multiselect(f"Phân khu", PK_L, key=f"p{ks}")
        with cb: lh = st.multiselect(f"Loại hình", LH_L, key=f"l{ks}")
        if pk: df_a = df_a[df_a[L1].isin(pk)]
        if lh: df_a = df_a[df_a[L2].isin(lh)]
        scols = df_a.drop(columns=[L9, L_TYPE, L12, L3] if not is_adm else [L9, L_TYPE, L12], errors='ignore')
        st.write(f"Tìm thấy {len(df_a)} căn")
        sel = st.dataframe(scols, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key=f"d{ks}")

        @st.dialog(f"Chi tiết {ks}")
        def show_dt(row):
            c1, c2 = st.columns([1.2, 1])
            with c1:
                ls = str(row.get(L9, "")).split(',') if row.get(L9) else []
                if ls and ls[0]:
                    if 'ci' not in st.session_state: st.session_state.ci = 0
                    ix = st.session_state.ci % len(ls)
                    st.image(ls[ix], use_container_width=True)
                    if len(ls) > 1:
                        b1, b2 = st.columns(2)
                        with b1: 
                            if st.button("⬅️", key=f"prev{ks}"): st.session_state.ci -= 1; st.rerun()
                        with b2:
                            if st.button("
