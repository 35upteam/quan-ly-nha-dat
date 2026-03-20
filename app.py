import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Vinhomes Smart City Manager", layout="wide", page_icon="🏢")

# 2. KẾT NỐI VÀ TẢI DỮ LIỆU
@st.cache_resource
def get_data_from_google():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        SHEET_ID = "19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk"
        spreadsheet = client.open_by_key(SHEET_ID)
        sheet_instance = spreadsheet.get_worksheet(0) 
        
        # Đọc toàn bộ giá trị thô từ Sheet
        raw_data = sheet_instance.get_all_values()
        
        if len(raw_data) <= 1: 
            return pd.DataFrame(), sheet_instance

        # MẸO QUAN TRỌNG: Lấy dữ liệu thô và tự gán tên cột để khớp cả cũ lẫn mới
        # Định nghĩa 11 cột chuẩn
        std_cols = ["Ngày", "Loại hình", "Phân khu", "Mã căn", "Tầng", "Nội thất", "Hướng", "Giá", "Hiện trạng", "Link ảnh", "Trạng thái"]
        
        # Chuyển thành DataFrame, chỉ lấy dữ liệu (từ dòng 2), bỏ qua tiêu đề cũ của Sheet
        df = pd.DataFrame(raw_data[1:])
        
        # Nếu dòng cũ thiếu cột (ví dụ chỉ có 8 cột), ta bù thêm cột trống cho đủ 11
        for i in range(len(df.columns), len(std_cols)):
            df[i] = ""
            
        # Chỉ lấy đúng 11 cột đầu tiên (phòng trường hợp Sheet có cột thừa bên phải)
        df = df.iloc[:, :len(std_cols)]
        df.columns = std_cols
        
        # Xử lý dữ liệu
        df = df.dropna(how='all') # Bỏ dòng trống hoàn toàn
        if "Giá" in df.columns:
            df["Giá"] = pd.to_numeric(df["Giá"], errors='coerce').fillna(0)
            
        return df, sheet_instance
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return pd.DataFrame(), None

df_raw, sheet_obj = get_data_from_google()

# 3. THANH BÊN (SIDEBAR)
with st.sidebar:
    st.header("🔑 Phân quyền")
    admin_pass = st.text_input("Mật khẩu Admin", type="password")
    is_admin = (admin_pass == "admin123")
    st.info("✅ ADMIN" if is_admin else "💡 CTV")
    
    if st.button("🔄 Cập nhật toàn bộ danh sách"):
        st.cache_resource.clear()
        st.rerun()

# 4. GIAO DIỆN CHÍNH
st.title("🏢 Kho Hàng Vinhomes Smart City")

if sheet_obj is None:
    st.error("Không thể kết nối Google Sheet.")
else:
    tab_view, tab_add = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])

    with tab_view:
        # BỘ LỌC
        c1, c2, c3 = st.columns(3)
        with c1:
            pk_f = st.multiselect("Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
        with c2:
            lh_f = st.multiselect("Loại hình", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
        with c3:
            price_f = st.slider("Khoảng giá (Tỷ)", 1.0, 15.0, (1.0, 15.0), step=0.1)

        if
