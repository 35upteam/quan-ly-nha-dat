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
        # Kết nối Credentials
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Mở file Google Sheet
        SHEET_ID = "19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk"
        spreadsheet = client.open_by_key(SHEET_ID)
        sheet_instance = spreadsheet.get_worksheet(0) # Lấy tab đầu tiên
        
        # CƠ CHẾ ĐỌC MỚI: Lấy toàn bộ giá trị thô để tránh lỗi tiêu đề
        raw_data = sheet_instance.get_all_values()
        
        if len(raw_data) <= 1: # Nếu chỉ có dòng tiêu đề hoặc trống
            return pd.DataFrame(), sheet_instance
            
        # Chuyển dữ liệu thô thành DataFrame
        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        
        # CHUẨN HÓA TIÊU ĐỀ: Xóa khoảng trắng thừa
        df.columns = [str(c).strip() for c in df.columns]
        
        # CHUẨN HÓA DỮ LIỆU SỐ: Cột 'Giá bán'
        if 'Giá bán' in df.columns:
            df['Giá bán'] = pd.to_numeric(df['Giá bán'], errors='coerce').fillna(0)
            
        return df, sheet_instance
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return pd.DataFrame(), None

# Tải dữ liệu
df_raw, sheet_obj = get_data_from_google()

# 3. THANH BÊN (SIDEBAR)
with st.sidebar:
    st.header("🔑 Phân quyền")
    admin_pass = st.text_input("Mật khẩu Admin", type="password")
    is_admin = (admin_pass == "admin123")
    
    if is_admin:
        st.success("✅ CHẾ ĐỘ: ADMIN")
    else:
        st.info("💡 CHẾ ĐỘ: CTV (Ẩn mã căn)")
    
    if st.button("🔄 Cập nhật danh sách mới"):
        st.cache_resource.clear()
        st.rerun()

# 4. GIAO DIỆN CHÍNH
st.title("🏢 Kho Hàng Vinhomes Smart City")

if sheet_obj is None:
    st.error("Không thể kết nối. Vui lòng kiểm tra lại quyền truy cập của Service Account.")
else:
    tab_view, tab_add = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])

    # --- TAB 1: DANH SÁCH ---
    with tab_view:
        # BỘ LỌC LUÔN HIỆN
        c1, c2, c3 = st.columns(3)
        with c1:
            pk_list = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
            pk_f = st.multiselect("Phân khu", options=pk_list)
        with c2:
            lh_list = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
            lh_f = st.multiselect("Loại hình", options=lh_list)
        with c3:
            price_f = st.slider("Khoảng giá (Tỷ)", 1.0, 15.0, (1.0, 10.0), step=0.1)

        if df_raw.empty:
            st.warning("⚠️ Hiện chưa thấy dữ liệu từ trang tính. Hãy thử bấm nút 'Cập nhật danh sách mới' ở bên trái.")
            # Hiển thị cấu trúc cột thực tế để gỡ lỗi
            if not df_raw.empty:
                st.write("Các cột tìm thấy:", df_raw.columns.tolist())
        else:
            # Lọc dữ liệu
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

            st.write(f"🔍 Tìm thấy **{len(display_df)}** căn hộ phù hợp")

            # Bảng hiển thị
            selection = st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )

            # Hiện chi tiết khi chọn dòng
            if selection and selection.selection.rows:
                idx = selection.selection.rows[0]
                row = df.iloc[idx]
                st.divider()
                col_a, col_b = st.columns(2)
                with col_a:
                    img = row.get('Link ảnh', '')
                    if img: st.image(img, use_container_width=True)
                    else: st.info("Căn này chưa cập nhật ảnh.")
                with col_b:
                    st.subheader(f"{row.get('Loại hình','')} - {row.get('Phân khu','')}")
                    st.write(f"💰 Giá: {row.get('Giá bán',0)} Tỷ | Tầng: {row.get('Khoảng tầng','-')}")
                    if is_admin:
                        st.error(f"🔑 MÃ CĂN NỘI BỘ: {row.get('Mã căn','N/A')}")
                    st.button("🔗 Gửi thông tin cho khách")

    # --- TAB 2: THÊM MỚI ---
    with tab_add:
        if is_admin:
            with st.form("form_add", clear_on_submit=True):
                st.write("### Nhập thông tin căn hộ mới")
                f1, f2, f3 = st.columns(3)
                with f1:
                    f_ngay = st.date_input("Ngày lên hàng")
                    f_loai = st.selectbox("Loại hình", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
                    f_pk = st.selectbox("Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
                with f2:
                    f_ma = st.text_input("Mã căn")
                    f_tang = st.selectbox("Khoảng tầng", ["Thấp", "Trung", "Cao"])
                    f_gia = st.number_input("Giá (Tỷ)", value=3.5, step=0.1)
                with f3:
                    f_anh = st.text_input("Link ảnh")
                    f_tt = st.radio("Trạng thái", ["Đang bán", "Đã bán"], horizontal=True)
                
                if st.form_submit_button("🚀 Lưu dữ liệu"):
                    try:
                        # Ghi dữ liệu: Đảm bảo khớp với tiêu đề dòng 1 Google Sheet của bạn
                        sheet_obj.append_row([str(f_ngay), f_loai, f_pk, f_ma, f_tang, "", "", f_gia, "", f_anh, f_tt])
                        st.success("Đã lưu thành công! Hãy nhấn nút 'Cập nhật danh sách mới' ở Sidebar để xem.")
                    except Exception as e:
                        st.error(f"Lỗi: {e}")
        else:
            st.warning("⚠️ Nhập mật khẩu Admin để thêm hàng.")
