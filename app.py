import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Vinhomes Smart City Manager", layout="wide", page_icon="🏢")

# Tùy chỉnh giao diện bằng CSS
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stCard {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .price-tag { color: #e74c3c; font-weight: bold; font-size: 20px; }
    </style>
    """, unsafe_allow_stdio=True)

# 2. KẾT NỐI DỮ LIỆU
@st.cache_resource
def get_gspread_client():
    creds_dict = st.secrets["gcp_service_account"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

client = get_gspread_client()
SHEET_ID = "19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk" # ID của bạn
sheet = client.open_by_key(SHEET_ID).sheet1

# 3. HÀM LẤY DỮ LIỆU
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# 4. GIAO DIỆN CHÍNH
st.title("🏢 Quản Lý Chuyển Nhượng Vinhomes Smart City")

tab1, tab2 = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])

# --- TAB 1: DANH SÁCH ---
with tab1:
    df = load_data()
    
    # Bộ lọc nhanh
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        pk_filter = st.multiselect("Phân khu", options=["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
    with col2:
        type_filter = st.multiselect("Loại hình", options=["Studio", "1PN+", "2PN", "2PN+", "3N"])
    with col3:
        price_range = st.slider("Khoảng giá (Tỷ)", 1.0, 10.0, (1.5, 5.0))
    with col4:
        st_filter = st.selectbox("Trạng thái", ["Đang bán", "Đã bán", "Tất cả"])

    # Xử lý lọc dữ liệu
    filtered_df = df.copy()
    if pk_filter: filtered_df = filtered_df[filtered_df['Phân khu'].isin(pk_filter)]
    if type_filter: filtered_df = filtered_df[filtered_df['Loại hình'].isin(type_filter)]
    if st_filter != "Tất cả": filtered_df = filtered_df[filtered_df['Trạng thái'] == st_filter]
    
    # ẨN MÃ CĂN khi hiển thị cho khách
    display_df = filtered_df.drop(columns=['Mã căn']) if 'Mã căn' in filtered_df.columns else filtered_df

    # Hiển thị bảng
    st.subheader(f"📊 Có {len(filtered_df)} căn phù hợp")
    
    # Sử dụng cột chọn để xem chi tiết
    selected_row = st.dataframe(
        display_df, 
        use_container_width=True, 
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    # Hiển thị thông tin chi tiết đẹp đẽ khi click chọn 1 dòng
    if len(selected_row.selection.rows) > 0:
        idx = selected_row.selection.rows[0]
        row_data = filtered_df.iloc[idx]
        
        st.divider()
        c1, c2 = st.columns([1, 1.5])
        
        with c1:
            if row_data['Link ảnh']:
                st.image(row_data['Link ảnh'], caption=f"Ảnh thực tế căn {row_data['Loại hình']}", use_container_width=True)
            else:
                st.info("Chưa có ảnh cho căn hộ này")
                
        with c2:
            st.header(f"{row_data['Loại hình']} - Phân khu {row_data['Phân khu']}")
            inner_c1, inner_c2 = st.columns(2)
            inner_c1.write(f"💰 **Giá bán:** {row_data['Giá bán']} Tỷ")
            inner_c1.write(f"📐 **Tầng:** {row_data['Khoảng tầng']}")
            inner_c1.write(f"🧭 **Hướng BC:** {row_data['Hướng BC']}")
            
            inner_c2.write(f"🛋️ **Nội thất:** {row_data['Nội thất']}")
            inner_c2.write(f"🏠 **Hiện trạng:** {row_data['Hiện trạng']}")
            inner_c2.write(f"📅 **Ngày lên:** {row_data['Ngày lên hàng']}")
            
            # Chỉ hiển thị mã căn trong khu vực chi tiết nếu bạn muốn quản lý
            # st.write(f"🔑 **Mã quản lý:** {row_data['Mã căn']}") 
            
            st.success(f"Trạng thái: {row_data['Trạng thái']}")

# --- TAB 2: THÊM MỚI ---
with tab2:
    with st.form("add_form", clear_on_submit=True):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            ngay = st.date_input("Ngày lên hàng")
            loai = st.selectbox("Loại hình", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
            phankhu = st.selectbox("Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
            macan = st.text_input("Mã căn (Nội bộ)")
        with f_col2:
            tang = st.selectbox("Khoảng tầng", ["Thấp", "Trung", "Cao"])
            noithat = st.selectbox("Nội thất", ["Cơ bản", "Nguyên bản", "Đầy đủ nội thất"])
            huong = st.text_input("Hướng Ban công")
            gia = st.number_input("Giá bán (Tỷ)", step=0.1)
        with f_col3:
            hientrang = st.selectbox("Hiện trạng", ["Đang ở", "Cho thuê", "Trống"])
            anh = st.text_input("Link ảnh (Google Drive/Imgur)")
            trangthai = st.radio("Trạng thái", ["Đang bán", "Đã bán"], horizontal=True)
        
        submit = st.form_submit_button("🚀 Lưu thông tin căn hộ")
        
        if submit:
            new_row = [str(ngay), loai, phankhu, macan, tang, noithat, huong, gia, hientrang, anh, trangthai]
            sheet.append_row(new_row)
            st.balloons()
            st.success("Đã thêm hàng thành công!")
