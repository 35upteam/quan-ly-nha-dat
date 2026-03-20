import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Vinhomes Smart City Manager", layout="wide", page_icon="🏢")

# 2. KẾT NỐI VÀ TẢI DỮ LIỆU
@st.cache_resource
def get_data():
    try:
        # Kết nối Credentials
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Mở Sheet
        SHEET_ID = "19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk"
        sheet_instance = client.open_by_key(SHEET_ID).sheet1
        
        # Đọc dữ liệu
        data = sheet_instance.get_all_records()
        if not data:
            return pd.DataFrame(), sheet_instance
            
        df = pd.DataFrame(data)
        df.columns = df.columns.str.strip() # Xóa khoảng trắng tiêu đề
        
        # Chuẩn hóa cột Giá bán
        if 'Giá bán' in df.columns:
            df['Giá bán'] = pd.to_numeric(df['Giá bán'], errors='coerce').fillna(0)
            
        return df, sheet_instance
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return pd.DataFrame(), None

# 3. CHẠY ỨNG DỤNG
df_raw, sheet_obj = get_data()

# 4. THANH BÊN (SIDEBAR)
with st.sidebar:
    st.header("🔑 Phân quyền")
    admin_pass = st.text_input("Mật khẩu Admin", type="password")
    is_admin = (admin_pass == "admin123") 
    
    if is_admin:
        st.success("✅ CHẾ ĐỘ: ADMIN")
    else:
        st.info("💡 CHẾ ĐỘ: CTV (Ẩn mã căn)")

# 5. GIAO DIỆN CHÍNH
st.title("🏢 Kho Hàng Vinhomes Smart City")

if sheet_obj is None:
    st.error("Không thể kết nối với Google Sheet. Vui lòng kiểm tra lại Secrets hoặc ID Sheet.")
else:
    tab_view, tab_add = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])

    # --- TAB 1: DANH SÁCH ---
    with tab_view:
        if df_raw.empty:
            st.info("Hiện chưa có dữ liệu. Hãy thêm căn hộ đầu tiên ở Tab 'Thêm hàng mới'.")
        else:
            # Bộ lọc
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                pk_opt = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
                pk_f = st.multiselect("Phân khu", options=pk_opt)
            with c2:
                lh_opt = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
                lh_f = st.multiselect("Loại hình", options=lh_opt)
            with c3:
                price_f = st.slider("Giá bán (Tỷ)", 1.5, 12.0, (2.0, 6.0), step=0.1)
            with c4:
                st_f = st.selectbox("Trạng thái", ["Đang bán", "Đã bán", "Tất cả"])

            # Lọc dữ liệu
            df = df_raw.copy()
            if pk_
