import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# PHẢI ĐẶT LỆNH NÀY ĐẦU TIÊN
st.set_page_config(page_title="Quản Lý Nhà Đất", layout="wide")

# 1. KẾT NỐI HỆ THỐNG
try:
    creds_dict = st.secrets["gcp_service_account"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # Mở file Google Sheet bằng ID
    SHEET_ID = "19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk"
    sheet = client.open_by_key(SHEET_ID).sheet1
except Exception as e:
    st.error(f"Lỗi kết nối Google Sheets: {e}")
    st.stop()

# 2. GIAO DIỆN CHÍNH
st.title("🏠 Hệ Thống Ký Gửi Nhà Đất")

# Nhập liệu ở thanh bên (Sidebar)
with st.sidebar.form("form_nhap"):
    st.header("Thêm Căn Hộ")
    m = st.text_input("Mã căn")
    c = st.text_input("Chủ nhà")
    s = st.text_input("SĐT")
    g = st.number_input("Giá (VNĐ)", step=1000000, format="%d")
    d = st.number_input("Diện tích (m2)", format="%.2f")
    btn = st.form_submit_button("Lưu vào Google Sheet")

if btn:
    if m and c: # Kiểm tra xem đã nhập Mã và Tên chưa
        try:
            sheet.append_row([m, c, s, g, d, "Đang rao"])
            st.sidebar.success("✅ Đã lưu thành công!")
            # Tự động tải lại trang để cập nhật bảng dữ liệu
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Lỗi khi lưu: {e}")
    else:
        st.sidebar.warning("Vui lòng nhập Mã căn và Tên chủ nhà")

# 3. HIỂN THỊ VÀ TÌM KIẾM
try:
    data = sheet.get_all_records()
    if data:
        df = pd.DataFrame(data)
        
        # Ô tìm kiếm
        tk = st.text_input("🔍 Tìm nhanh (Mã căn, Tên, SĐT...)")
        if tk:
            # Tìm kiếm không phân biệt hoa thường trên toàn bộ bảng
            df = df[df.astype(str).apply(lambda x: x.str.contains(tk, case=False)).any(axis=1)]
        
        # Hiển thị bảng dạng DataFrame (đẹp và chuyên nghiệp hơn st.table)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Hiện chưa có dữ liệu căn hộ nào. Hãy nhập căn hộ đầu tiên ở thanh bên!")
except Exception as e:
    st.warning("Chưa đọc được dữ liệu. Hãy đảm bảo dòng đầu tiên của Google Sheet là tiêu đề (Mã căn, Chủ nhà, SĐT...)")
