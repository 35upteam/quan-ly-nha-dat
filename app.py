import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Vinhomes Smart City Manager", layout="wide", page_icon="🏢")

# 2. KẾT NỐI DỮ LIỆU
@st.cache_resource
def get_data():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        SHEET_ID = "19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk"
        sheet_instance = client.open_by_key(SHEET_ID).sheet1
        
        records = sheet_instance.get_all_records()
        if not records: return pd.DataFrame(), sheet_instance
            
        df = pd.DataFrame(records)
        df.columns = df.columns.str.strip()
        if 'Giá bán' in df.columns:
            df['Giá bán'] = pd.to_numeric(df['Giá bán'], errors='coerce').fillna(0)
        return df, sheet_instance
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame(), None

df_raw, sheet_obj = get_data()

# 3. THANH BÊN (SIDEBAR)
with st.sidebar:
    st.header("🔑 Phân quyền")
    admin_pass = st.text_input("Mật khẩu Admin", type="password")
    is_admin = (admin_pass == "admin123")
    st.success("ADMIN" if is_admin else "CTV (Ẩn mã căn)")

# 4. GIAO DIỆN CHÍNH
st.title("🏢 Kho Hàng Vinhomes Smart City")

if sheet_obj is not None:
    tab1, tab2 = st.tabs(["📋 Danh sách", "➕ Thêm hàng"])

    with tab1:
        if df_raw.empty:
            st.info("Chưa có dữ liệu.")
        else:
            c1, c2, c3 = st.columns(3)
            with c1: pk_f = st.multiselect("Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
            with c2: lh_f = st.multiselect("Loại hình", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
            with c3: price_f = st.slider("Giá (Tỷ)", 1.5, 10.0, (2.0, 5.0), step=0.1)

            df_f = df_raw.copy()
            if pk_f: df_f = df_f[df_f['Phân khu'].isin(pk_f)]
            if
