import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests, base64

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# NHÃN CỘT chuẩn
L_DATE, L_LH, L_PK, L_MA = "Ngày lên hàng", "Loại hình", "Phân khu", "Mã căn"
L_DT, L_TANG, L_NT, L_HBC = "Diện tích", "Khoảng tầng", "Nội thất", "Hướng BC"
L_GIA, L_HT, L_TT, L_IMG, L_TYPE, L_GC = "Giá bán", "Hiện trạng", "Trạng thái", "Link ảnh", "Phân loại", "Ghi chú"

# TRẠNG THÁI
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
    except Exception as e: return pd.DataFrame(), None

df_raw, sh_obj = load_data()
if 'is_login' not in st.session_state: st.session_state.is_login = False

# --- HEADER: Khôi phục icon và tiêu đề ---
h1, h2 = st.columns([7, 3])
with h1: st.title("🏢 Vinhomes Manager")
with h2:
    if not st.session_state.is_login:
        p = st.text_input("Mật khẩu truy cập", type="password", label_visibility="collapsed")
        if p == "admin123": st.session_state.is_login = True; st.rerun()
    else:
        st.info("✅ Chế độ Admin")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 Làm mới"): st.cache_resource.clear(); st.rerun()
        with c2:
            if st.button("❌ Thoát"): st.session_state.is_login = False; st.rerun()

is_adm = st.session_state.is_login
if sh_obj is not None:
    # Khôi phục tên Tab đầy đủ
    t1, t2, t3 = st.tabs(["🔴 Chuyển nhượng", "🟢 Cho thuê", "➕ Thêm hàng"])
    
    def draw(df_in, ks):
        df_a = df_in[~df_in[L_TT].astype(str).str.contains(T_DONE, na=False)]
        if df_a.empty: st.info("Hiện không có căn nào trống."); return
        
        st.markdown("### 🔍 Tìm kiếm & Lọc")
        s_ma = st.text_input("Nhập mã căn để tìm nhanh...", key=f"sm{ks}").strip()
        
        c1, c2, c3 = st.columns([3, 3, 4])
        with c1: pk = st.multiselect("Phân khu", sorted(df_in[L_PK].unique()), key=f"p{ks}")
        with c2: lh = st.multiselect("Loại hình", sorted(df_in[L_LH].unique()), key=f"l{ks}")
        with c3:
            mi, ma = float(df_in[L_GIA].min()), float(df_in[L_GIA].max())
            r_gia = st.slider("Khoảng giá (T
