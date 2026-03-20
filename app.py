import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests, base64

st.set_page_config(page_title="Vinhomes", layout="wide")

# KHAI BÁO NHÃN
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

# TRẠNG THÁI
T_DONE = "Đã"
V_SOLD = f"{T_DONE} bán"
V_RENT = f"{T_DONE} thuê"

def up_img(fs):
    if not fs: return ""
    try:
        ak = st.secrets.get("imgbb_api_key")
        res = []
        for f in fs:
            f.seek(0)
            b6 = base64.b64encode(f.read()).decode('utf-8')
            r = requests.post("https://api.imgbb.com/1/upload", {"key": ak, "image": b6}, timeout=20)
            if r.status_code == 200:
                res.append(r.json()['data']['thumb']['url']) 
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
        h = [x.strip() for x in r[0]]
        df = pd.DataFrame(r[1:], columns=h)
        df['sheet_row'] = range(2, len(df) + 2)
        df[L_GIA] = pd.to_numeric(df[L_GIA], errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except: return pd.DataFrame(), None

df_raw, sh_obj = load_data()
if 'is_login' not in st.session_state:
    st.session_state.is_login = False

# --- HEADER: Viết tách dòng hoàn toàn ---
h1, h2 = st.columns([7, 3])
with h1:
    st.title("🏢 Vinhomes Manager")
with h2:
    if not st.session_state.is_login:
        p = st.text_input("Pass", type="password", label_visibility="collapsed")
        if p == "admin123":
            st.session_state.is_login = True
            st.rerun()
    else:
        st.info("✅ Admin")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄"):
                st.cache_resource.clear()
                st.rerun()
        with c2:
            if st.button("❌"):
                st.session_state.is_login = False
                st.rerun()

is_adm = st.session_state.is_login
if sh_obj is not None and not df_raw.empty:
    t1, t2, t3 = st.tabs(["🔴 Bán", "🟢 Thuê", "
