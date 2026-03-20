import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests, base64

# Cấu hình trang
st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# KHAI BÁO NHÃN CỘT (Sử dụng chuỗi ngắn để tránh ngắt dòng)
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

# CÁC BIẾN TRẠNG THÁI
T_DONE = "Đã"
V_SOLD = f"{T_DONE} bán"
V_RENT = f"{T_DONE} thuê"

def up_img(fs):
    if not fs: return ""
    try:
        ak = st.secrets.get("imgbb_api_key") or st.secrets.get("gcp_service_account", {}).get("imgbb_api_key")
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
        cols = [h.strip() for h in r[0]]
        df = pd.DataFrame(r[1:], columns=cols)
        df['sheet_row'] = range(2, len(df) + 2)
        df[L_GIA] = pd.to_numeric(df[L_GIA], errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
        return pd.DataFrame(), None

df_raw, sh_obj = load_data()
if 'is_login' not in st.session_state:
    st.session_state.is_login = False

# --- GIAO DIỆN CHÍNH ---
c_h1, c_h2 = st.columns([7, 3])
with c_h1:
    st.title("🏢 Vinhomes Manager")
with c_h2:
    if not st.session_state.is_login:
        p = st.text_input("Admin Pass", type="password", label_visibility="collapsed")
        if p == "admin123":
            st.session_state.is_login = True
            st.rerun()
    else:
        st.info("✅ Chế độ Admin")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("🔄 Làm mới"):
                st.cache_resource.clear()
                st.rerun()
        with b2:
            if st.button("❌ Thoát"):
                st.session_state.is_login = False
                st.rerun()

is_adm = st.session_state.is_login

if sh_obj is not None:
    tab_titles = ["🔴 Chuyển nhượng", "🟢 Cho thuê", "➕ Thêm hàng"]
    t1, t2, t3 = st.tabs(tab_titles)
    
    def draw_tab(df_in, ks):
        # Lọc các căn chưa bán/thuê
        df_a = df_in[~df_in[L_TT].astype(str).str.contains(T_DONE, na=False)]
        
        if df_a.empty:
            st.warning("Hiện tại danh sách trống.")
            return

        st.markdown("### 🔍 Tìm kiếm & Bộ lọc")
        s_ma = st.text_input("Tìm nhanh theo Mã căn...", key=f"s_{ks}").strip()
        
        f1, f2, f3 = st.columns([3, 3, 4])
        with f1:
            pk_list = sorted(df_in[L_PK].unique())
            pk = st.multiselect("Phân khu", pk_list, key=f"p_{ks}")
        with f2:
            lh_list = sorted(df_in[L_LH].unique())
            lh = st.multiselect("Loại hình", lh_list, key=f"l_{ks}")
        with f3:
            mi_g = float(df_in[L_GIA].min())
            ma_g = float(df_in[L_GIA].max())
            r_gia = st.slider("Khoảng giá (Tỷ)", mi_g, ma_g, (mi_g, ma_g), key=f"g_{ks}")
        
        # Áp dụng lọc
        if s_ma:
            df_a = df_a[df_a[L_MA].astype(str).str.contains(s_ma, case=False, na=False)]
        if pk:
            df_a = df_a[df_a[L_PK].isin(pk)]
        if lh:
            df_a = df_a[df_a[L_LH].isin(lh)]
        df_a = df_a[(df_a[L_GIA] >= r_gia[0]) & (df_a[L_GIA] <= r_gia[1])]

        st.write(f"Tìm thấy: **{len(df_a)}** căn")
        
        # Cột hiển thị
        disp_cols = [L_DATE, L_LH, L_PK, L_DT, L_
