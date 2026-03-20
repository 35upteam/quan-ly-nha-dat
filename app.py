import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# 1. CẤU HÌNH TRANG (LUÔN Ở ĐẦU)
st.set_page_config(page_title="Vinhomes Smart City Manager", layout="wide", page_icon="🏢")

# 2. KẾT NỐI VÀ TẢI DỮ LIỆU
@st.cache_resource
def get_data():
    try:
        # Kết nối bằng Secrets
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Mở Sheet (Dùng ID của bạn)
        SHEET_ID = "19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk"
        sheet_instance = client.open_by_key(SHEET_ID).sheet1
        
        # Đọc dữ liệu
        records = sheet_instance.get_all_records()
        if not records:
            return pd.DataFrame(), sheet_instance
            
        df = pd.DataFrame(records)
        # Chuẩn hóa tên cột (Xóa khoảng trắng thừa và ép về chuỗi)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Ép kiểu số cho cột Giá bán
        if 'Giá bán' in df.columns:
            df['Giá bán'] = pd.to_numeric(df['Giá bán'], errors='coerce').fillna(0)
            
        return df, sheet_instance
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return pd.DataFrame(), None

# Tải dữ liệu ban đầu
df_raw, sheet_obj = get_data()

# 3. THANH BÊN (SIDEBAR)
with st.sidebar:
    st.header("🔑 Phân quyền")
    admin_pass = st.text_input("Mật khẩu Admin", type="password", help="Nhập 'admin123' để hiện Mã căn và Tab Thêm hàng")
    is_admin = (admin_pass == "admin123")
    
    if is_admin:
        st.success("✅ CHẾ ĐỘ: ADMIN")
    else:
        st.info("💡 CHẾ ĐỘ: CTV (Ẩn mã căn)")
    st.divider()
    st.caption("Khu vực: Vinhomes Smart City")

# 4. GIAO DIỆN CHÍNH
st.title("🏢 Kho Hàng Vinhomes Smart City")

if sheet_obj is None:
    st.error("Không thể kết nối với Google Sheet. Vui lòng kiểm tra lại cấu hình Secrets.")
else:
    tab_view, tab_add = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])

    # --- TAB 1: DANH SÁCH ---
    with tab_view:
        # HIỂN THỊ BỘ LỌC (LUÔN HIỆN)
        c1, c2, c3 = st.columns(3)
        with c1:
            pk_list = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
            pk_f = st.multiselect("Phân khu", options=pk_list)
        with c2:
            lh_list = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
            lh_f = st.multiselect("Loại hình", options=lh_list)
        with c3:
            price_f = st.slider("Khoảng giá (Tỷ)", 1.0, 15.0, (2.0, 6.0), step=0.1)

        if df_raw.empty:
            st.warning("Chưa có dữ liệu trong kho hàng. Vui lòng sang Tab 'Thêm hàng mới' để nhập căn đầu tiên.")
        else:
            # Xử lý lọc dữ liệu
            df = df_raw.copy()
            if pk_f and 'Phân khu' in df.columns:
                df = df[df['Phân khu'].isin(pk_f)]
            if lh_f and 'Loại hình' in df.columns:
                df = df[df['Loại hình'].isin(lh_f)]
            if 'Giá bán' in df.columns:
                df = df[(df['Giá bán'] >= price_f[0]) & (df['Giá bán'] <= price_f[1])]

            # Ẩn mã căn nếu là CTV
            display_df = df.copy()
            if not is_admin and 'Mã căn' in display_df.columns:
                display_df = display_df.drop(columns=['Mã căn'])

            st.write(f"🔍 Tìm thấy **{len(display_df)}** căn phù hợp")

            # Hiển thị bảng tương tác
            selection = st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )

            # Chi tiết khi click chọn một dòng
            if selection and selection.selection.rows:
                row_idx = selection.selection.rows[0]
                selected_row = df.iloc[row_idx]
                
                st.divider()
                col_a, col_b = st.columns([1, 1])
                with col_a:
                    img_url = selected_row.get('Link ảnh', '')
                    if img_url:
                        st.image(img_url, use_container_width=True, caption="Ảnh thực tế")
                    else:
                        st.info("Căn hộ này chưa có ảnh.")
                with col_b:
                    st.subheader(f"{selected_row.get('Loại hình','')} - Phân khu {selected_row.get('Phân khu','')}")
                    st.markdown(f"💰 Giá bán: **{selected_row.get('Giá bán',0)} Tỷ**")
                    st.write(f"📐 Tầng: {selected_row.get('Khoảng tầng','-')} | 🧭 Hướng BC: {selected_row.get('Hướng BC','-')}")
                    st.write(f"🛋️ Nội thất: {selected_row.get('Nội thất','-')} | 🏠 Hiện trạng: {selected_row.get('Hiện trạng','-')}")
                    
                    if is_admin:
                        st.error(f"🔑 MÃ CĂN NỘI BỘ: {selected_row.get('Mã căn','N/A')}")
                    
                    st.button("🔗 Sao chép thông tin gửi khách (Sắp có)")

    # --- TAB 2: THÊM MỚI ---
    with tab_add:
        if is_admin:
            with st.form("form_them_moi", clear_on_submit=True):
                st.subheader("📝 Nhập căn hộ mới vào hệ thống")
                f1, f2, f3 = st.columns(3)
                with f1:
                    f_ngay = st.date_input("Ngày lên hàng")
                    f_loai = st.selectbox("Loại hình", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
                    f_pk = st.selectbox("Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
                    f_ma = st.text_input("Mã căn (Dành cho Admin)")
                with f2:
                    f_tang = st.selectbox("Khoảng tầng", ["Thấp", "Trung", "Cao"])
                    f_nt = st.selectbox("Nội thất", ["Cơ bản", "Nguyên bản", "Đầy đủ nội thất"])
                    f_huong = st.text_input("Hướng Ban công")
                    f_gia = st.number_input("Giá (Tỷ)", step=0.1)
                with f3:
                    f_ht = st.selectbox("Hiện trạng", ["Đang ở", "Cho thuê", "Trống"])
                    f_anh = st.text_input("Link ảnh (Dán link từ Facebook/Drive)")
                    f_tt = st.radio("Trạng thái", ["Đang bán", "Đã bán"], horizontal=True)
                
                if st.form_submit_button("🚀 Lưu vào Google Sheet"):
                    try:
                        # Thứ tự: Ngày, Loại hình, Phân khu, Mã căn, Tầng, Nội thất, Hướng BC, Giá bán, Hiện trạng, Link ảnh, Trạng thái
                        sheet_obj.append_row([str(f_ngay), f_loai, f_pk, f_ma, f_tang, f_nt, f_huong, f_gia, f_ht, f_anh, f_tt])
                        st.success("Đã thêm thành công! Vui lòng F5 trang để cập nhật danh sách.")
                        # Xóa cache để lần sau nạp lại dữ liệu mới
                        st.cache_resource.clear()
                    except Exception as e:
                        st.error(f"Lỗi khi lưu dữ liệu: {e}")
        else:
            st.warning("⚠️ Bạn cần nhập mật khẩu Admin ở thanh bên trái (Sidebar) để sử dụng tính năng này.")
