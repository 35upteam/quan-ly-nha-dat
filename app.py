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
        
        # Mở file Google Sheet (Thay ID của bạn nếu cần)
        SHEET_ID = "19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk"
        spreadsheet = client.open_by_key(SHEET_ID)
        
        # Lấy trang tính đầu tiên
        sheet_instance = spreadsheet.get_worksheet(0)
        
        # Đọc tất cả dữ liệu (Bao gồm cả việc xử lý lỗi nếu bảng có ô trống)
        records = sheet_instance.get_all_records(default_blank=None)
        
        if not records:
            return pd.DataFrame(), sheet_instance
            
        df = pd.DataFrame(records)
        
        # Làm sạch tên cột: Xóa khoảng trắng, bỏ các cột không có tên
        df.columns = [str(c).strip() for c in df.columns]
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # Bỏ các dòng hoàn toàn trống
        df = df.dropna(how='all')
        
        # Ép kiểu số cho Giá bán
        if 'Giá bán' in df.columns:
            df['Giá bán'] = pd.to_numeric(df['Giá bán'], errors='coerce').fillna(0)
            
        return df, sheet_instance
    except Exception as e:
        st.error(f"Lỗi hệ thống khi đọc dữ liệu: {e}")
        return pd.DataFrame(), None

# Tải dữ liệu
df_raw, sheet_obj = get_data()

# 3. THANH BÊN (SIDEBAR)
with st.sidebar:
    st.header("🔑 Phân quyền")
    admin_pass = st.text_input("Mật khẩu Admin", type="password")
    is_admin = (admin_pass == "admin123")
    st.info("✅ ADMIN" if is_admin else "💡 CTV (Ẩn mã căn)")
    
    if st.button("🔄 Làm mới dữ liệu"):
        st.cache_resource.clear()
        st.rerun()

# 4. GIAO DIỆN CHÍNH
st.title("🏢 Kho Hàng Vinhomes Smart City")

if sheet_obj is None:
    st.error("⚠️ Không thể kết nối với Google Sheet. Kiểm tra lại Secrets và Quyền chia sẻ file.")
else:
    tab_view, tab_add = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])

    # --- TAB 1: DANH SÁCH ---
    with tab_view:
        # BỘ LỌC
        c1, c2, c3 = st.columns(3)
        with c1:
            pk_opt = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
            pk_f = st.multiselect("Phân khu", options=pk_opt)
        with c2:
            lh_opt = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
            lh_f = st.multiselect("Loại hình", options=lh_opt)
        with c3:
            price_f = st.slider("Khoảng giá (Tỷ)", 1.0, 15.0, (1.0, 10.0), step=0.1)

        if df_raw.empty:
            st.warning("⚠️ Đã kết nối nhưng không thấy dữ liệu. Hãy kiểm tra lại file Google Sheet hoặc thêm căn mới!")
        else:
            # Lọc dữ liệu
            df = df_raw.copy()
            if pk_f and 'Phân khu' in df.columns:
                df = df[df['Phân khu'].isin(pk_f)]
            if lh_f and 'Loại hình' in df.columns:
                df = df[df['Loại hình'].isin(lh_f)]
            if 'Giá bán' in df.columns:
                df = df[(df['Giá bán'] >= price_f[0]) & (df['Giá bán'] <= price_f[1])]

            # Phân quyền hiển thị
            display_df = df.copy()
            if not is_admin and 'Mã căn' in display_df.columns:
                display_df = display_df.drop(columns=['Mã căn'])

            st.write(f"🔍 Tìm thấy **{len(display_df)}** căn hộ")

            # Bảng chính
            selection = st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )

            # Chi tiết khi chọn dòng
            if selection and selection.selection.rows:
                idx = selection.selection.rows[0]
                row = df.iloc[idx]
                st.divider()
                ca, cb = st.columns(2)
                with ca:
                    img = row.get('Link ảnh', '')
                    if img: st.image(img, use_container_width=True)
                    else: st.info("Không có ảnh.")
                with cb:
                    st.subheader(f"{row.get('Loại hình')} - {row.get('Phân khu')}")
                    st.write(f"💰 Giá: {row.get('Giá bán')} Tỷ | Tầng: {row.get('Khoảng tầng')}")
                    if is_admin: st.error(f"🔑 MÃ CĂN: {row.get('Mã căn')}")
                    st.button("🔗 Sao chép link gửi khách")

    # --- TAB 2: THÊM MỚI ---
    with tab_add:
        if is_admin:
            with st.form("add_form", clear_on_submit=True):
                st.write("### Nhập thông tin căn hộ mới")
                f1, f2, f3 = st.columns(3)
                with f1:
                    f_ngay = st.date_input("Ngày lên hàng")
                    f_loai = st.selectbox("Loại hình", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
                    f_pk = st.selectbox("Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
                with f2:
                    f_ma = st.text_input("Mã căn")
                    f_tang = st.selectbox("Tầng", ["Thấp", "Trung", "Cao"])
                    f_gia = st.number_input("Giá (Tỷ)", value=3.0, step=0.1)
                with f3:
                    f_anh = st.text_input("Link ảnh")
                    f_tt = st.radio("Trạng thái", ["Đang bán", "Đã bán"], horizontal=True)
                
                if st.form_submit_button("🚀 Lưu dữ liệu"):
                    try:
                        # Ghi vào Google Sheet theo đúng thứ tự cột
                        # Chú ý: Cần khớp với số lượng cột trong file của bạn
                        sheet_obj.append_row([str(f_ngay), f_loai, f_pk, f_ma, f_tang, "", "", f_gia, "", f_anh, f_tt])
                        st.success("Đã lưu thành công! Hãy bấm 'Làm mới dữ liệu' ở Sidebar.")
                    except Exception as e:
                        st.error(f"Lỗi: {e}")
        else:
            st.warning("Nhập mật khẩu Admin để sử dụng.")
