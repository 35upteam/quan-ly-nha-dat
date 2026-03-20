import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import urllib.parse

# 1. CẤU HÌNH TRANG (LUÔN Ở ĐẦU)
st.set_page_config(page_title="Vinhomes Smart City - Kho Hàng", layout="wide", page_icon="🏢")

# Tùy chỉnh giao diện bằng CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
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
    st.error(f"Lỗi kết nối: {e}")
    st.stop()

# 3. QUẢN LÝ QUYỀN TRUY CẬP (SIDEBAR)
with st.sidebar:
    st.header("🔑 Cài đặt quyền")
    admin_pass = st.text_input("Mật khẩu Admin", type="password", help="Nhập để xem Mã căn và Thêm hàng")
    is_admin = (admin_pass == "admin123") # <--- BẠN CÓ THỂ ĐỔI MẬT KHẨU TẠI ĐÂY
    
    if is_admin:
        st.markdown('<div class="admin-status">✅ Chế độ: ADMIN</div>', unsafe_allow_html=True)
    else:
        st.info("💡 Chế độ: CTV (Ẩn mã căn)")
    
    st.divider()
    st.write("📍 **Khu vực:** Vinhomes Smart City")

# 4. TẢI DỮ LIỆU
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# 5. GIAO DIỆN CHÍNH
st.title("🏢 Hệ Thống Chuyển Nhượng Vinhomes")

tab_view, tab_add = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])

# --- TAB 1: XEM DANH SÁCH ---
with tab_view:
    df_raw = load_data()
    
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

    # Lọc DataFrame
    df = df_raw.copy()
    if pk_f: df = df[df['Phân khu'].isin(pk_f)]
    if lh_f: df = df[df['Loại hình'].isin(lh_f)]
    df = df[(df['Giá bán'] >= price_f[0]) & (df['Giá bán'] <= price_f[1])]
    if st_f != "Tất cả": df = df[df['Trạng thái'] == st_f]

    # Xử lý ẩn mã căn cho CTV
    display_df = df.copy()
    if not is_admin:
        if 'Mã căn' in display_df.columns:
            display_df = display_df.drop(columns=['Mã căn'])

    st.write(f"🔍 Tìm thấy **{len(display_df)}** căn hộ phù hợp")

    # Bảng dữ liệu (Tính năng mới của Streamlit 1.35+)
    selection = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    # HIỂN THỊ CHI TIẾT KHI CLICK CHỌN DÒNG
    if selection and hasattr(selection, 'selection') and len(selection.selection.get('rows', [])) > 0:
        row_index = selection.selection.rows[0]
        selected_row = df.iloc[row_index] # Lấy từ df gốc để có mã căn nếu là admin
        
        st.divider()
        col_a, col_b = st.columns([1, 1])
        
        with col_a:
            if selected_row['Link ảnh']:
                st.image(selected_row['Link ảnh'], use_container_width=True, caption="Ảnh thực tế căn hộ")
            else:
                st.info("Căn hộ này chưa có ảnh.")
        
        with col_b:
            st.subheader(f"Căn {selected_row['Loại hình']} - Phân khu {selected_row['Phân khu']}")
            
            m1, m2 = st.columns(2)
            m1.metric("Giá bán", f"{selected_row['Giá bán']} Tỷ")
            m2.metric("Tầng", selected_row['Khoảng tầng'])
            
            st.write(f"🧭 **Hướng BC:** {selected_row['Hướng BC']}")
            st.write(f"🛋️ **Nội thất:** {selected_row['Nội thất']}")
            st.write(f"🏠 **Hiện trạng:** {selected_row['Hiện trạng']}")
            
            if is_admin:
                st.markdown(f"🔑 **MÃ CĂN (NỘI BỘ):** `{selected_row['Mã căn']}`")
            
            # Nút giả lập chia sẻ
            st.button("🔗 Sao chép link gửi khách (Coming soon)")

# --- TAB 2: THÊM MỚI (CHỈ ADMIN) ---
with tab_add:
    if is_admin:
        with st.form("form_them", clear_on_submit=True):
            st.subheader("📝 Nhập thông tin căn hộ mới")
            f1, f2, f3 = st.columns(3)
            with f1:
                f_ngay = st.date_input("Ngày lên hàng")
                f_loai = st.selectbox("Loại hình", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
                f_pk = st.selectbox("Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
                f_ma = st.text_input("Mã căn (Nội bộ)")
            with f2:
                f_tang = st.selectbox("Khoảng tầng", ["Thấp", "Trung", "Cao"])
                f_nt = st.selectbox("Nội thất", ["Cơ bản", "Nguyên bản", "Đầy đủ nội thất"])
                f_huong = st.text_input("Hướng Ban công")
                f_gia = st.number_input("Giá (Tỷ)", step=0.1)
            with f3:
                f_ht = st.selectbox("Hiện trạng", ["Đang ở", "Cho thuê", "Trống"])
                f_anh = st.text_input("Link ảnh")
                f_tt = st.radio("Trạng thái", ["Đang bán", "Đã bán"], horizontal=True)
            
            if st.form_submit_button("🚀 Lưu vào hệ thống"):
                try:
                    sheet.append_row([str(f_ngay), f_loai, f_pk, f_ma, f_tang, f_nt, f_huong, f_gia, f_ht, f_anh, f_tt])
                    st.success("Đã thêm thành công! Vui lòng F5 hoặc sang Tab Danh sách để xem.")
                except Exception as e:
                    st.error(f"Lỗi: {e}")
    else:
        st.warning("⚠️ Bạn cần nhập mật khẩu Admin ở thanh bên trái để sử dụng tính năng này.")
