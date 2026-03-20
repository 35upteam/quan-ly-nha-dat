import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Vinhomes Smart City Manager", layout="wide")

# 2. KẾT NỐI VÀ TẢI DỮ LIỆU
@st.cache_resource
def get_data():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Mở Sheet bằng ID
        spreadsheet = client.open_by_key("19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk")
        sheet = spreadsheet.get_worksheet(0)
        
        # Lấy dữ liệu thô (Bỏ qua tiêu đề cũ, tự gán tiêu đề mới để khớp hàng cũ & mới)
        raw = sheet.get_all_values()
        if len(raw) <= 1: return pd.DataFrame(), sheet
        
        # Định nghĩa 11 cột chuẩn
        cols = ["Ngày", "Loại hình", "Phân khu", "Mã căn", "Tầng", "Nội thất", "Hướng", "Giá", "Hiện trạng", "Link ảnh", "Trạng thái"]
        df = pd.DataFrame(raw[1:])
        
        # Bù cột nếu hàng cũ bị thiếu
        for i in range(len(df.columns), len(cols)): df[i] = ""
        df = df.iloc[:, :len(cols)]
        df.columns = cols
        
        # Ép kiểu số cho cột Giá
        df["Giá"] = pd.to_numeric(df["Giá"], errors='coerce').fillna(0)
        return df, sheet
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame(), None

df_raw, sheet_obj = get_data()

# 3. THANH BÊN (SIDEBAR)
with st.sidebar:
    st.header("🔑 Phân quyền")
    pw = st.text_input("Mật khẩu Admin", type="password")
    is_admin = (pw == "admin123")
    st.info("✅ ADMIN" if is_admin else "💡 CTV")
    if st.button("🔄 Cập nhật danh sách"):
        st.cache_resource.clear()
        st.rerun()

# 4. GIAO DIỆN CHÍNH
st.title("🏢 Kho Hàng Vinhomes Smart City")

if sheet_obj is not None:
    tab1, tab2 = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])

    with tab1:
        # BỘ LỌC
        c1, c2, c3 = st.columns(3)
        with c1: pk_f = st.multiselect("Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
