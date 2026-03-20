import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import urllib.parse

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Vinhomes Smart City - Kho Hàng", layout="wide", page_icon="🏢")

# Tùy chỉnh giao diện CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stDataFrame { border: 1px solid #e6e9ef; border-radius: 10px; }
    .admin-status { color: #27ae60; font-weight: bold; background-color: #eafaf1; padding: 10px; border-radius: 5px; border: 1px solid #27ae60; }
    </style>
    """, unsafe_allow_html=True)

# 2. KẾT NỐI DỮ LIỆU
@st.cache_resource
def get_gspread_client():
    creds_dict = st.secrets["gcp_service_account"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

try:
    client = get_gspread_client()
    SHEET_ID = "19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk"
    sheet = client.open_by_key(SHEET_ID).sheet1
except Exception as e:
    st.error(f"Lỗi kết nối Google Sheets: {e}")
    st.stop()

# 3. HÀM TẢI VÀ CHUẨN HÓA DỮ LIỆU (CHỐNG LỖI KEYERROR)
def load_data():
    try:
        data = sheet.get_all_records()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        
        # Xử lý tiêu đề: Xóa khoảng trắng thừa, viết hoa chữ cái đầu
        df.columns = df.columns.str.strip()
        
        # Ép kiểu dữ liệu số cho cột Giá bán để slider không lỗi
        if 'Giá bán' in df.columns:
            df['Giá bán'] = pd.to_numeric(df['Giá bán'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Lỗi đọc bảng tính: {e}")
        return pd.DataFrame()

# 4. THANH BÊN (SIDEBAR) & PHÂN QUYỀN
with st.sidebar:
    st.header("🔑 Phân quyền")
    admin_pass = st.text_input("Mật khẩu Admin", type="password")
    is_admin = (admin_pass == "admin123") # Thay mật khẩu tại đây
    
    if is_admin:
        st.markdown('<div class="admin-status">✅ CHẾ ĐỘ: ADMIN</div>', unsafe_allow_html=True)
    else:
        st.info("💡 CHẾ ĐỘ: CTV (Ẩn mã căn)")
    st.divider()
    st.caption("Khu vực: Vinhomes Smart City")

# 5. GIAO DIỆN CHÍNH
st.title("🏢 Kho Hàng Chuyển Nhượng Smart City")

tab_view, tab_add = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])

# --- TAB 1: XEM DANH SÁCH ---
with tab_view:
    df_raw
