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
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Mở Sheet
        spreadsheet = client.open_by_key("19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk")
        sheet = spreadsheet.get_worksheet(0)
        
        # Đọc tất cả bản ghi (Dùng get_all_records để tự động lấy tiêu đề làm key)
        data = sheet.get_all_records()
        if not data:
            return pd.DataFrame(), sheet
            
        df = pd.DataFrame(data)
        
        # CHUẨN HÓA TIÊU ĐỀ (Xóa khoảng trắng thừa)
        df.columns = [str(c).strip() for c in df.columns]
        
        # CHUẨN HÓA DỮ LIỆU SỐ (Cột Giá bán)
        # Tìm cột có tên chứa chữ "Giá" để ép kiểu số
        for col in df.columns:
            if "Giá" in col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        return df, sheet
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return pd.DataFrame(), None

df_raw, sheet_obj = get_data()

# 3. THANH BÊN (SIDEBAR)
with st.sidebar:
    st.header("🔑 Phân quyền")
    pw = st.text_input("Mật khẩu Admin", type="password")
    is_admin = (pw == "admin123")
    
    if is_admin:
        st.success("✅ CHẾ ĐỘ: ADMIN")
    else:
        st.info("💡 CHẾ ĐỘ: CTV (Ẩn mã căn)")
    
    st.divider()
    if st.button("🔄 Cập nhật danh sách mới nhất"):
        st.cache_resource.clear()
        st.rerun()

# 4. GIAO DIỆN CHÍNH
st.title("🏢 Kho Hàng Vinhomes Smart City")

if sheet_obj is None:
    st.error("Không thể kết nối Google Sheet. Kiểm tra lại quyền của Service Account.")
else:
    tab1, tab2 = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])

    # --- TAB 1: DANH SÁCH ---
    with tab1:
        # KIỂM TRA NẾU CÓ DỮ LIỆU THÌ HIỆN BỘ LỌC
        if not df_raw.empty:
            c1, c2, c3 = st.columns(3)
            
            # Lấy danh sách các giá trị duy nhất để làm bộ lọc (tránh lỗi nếu cột không tồn tại)
            pk_options = sorted(df_raw['Phân khu'].unique().tolist()) if 'Phân khu' in df_raw.columns else []
            lh_options = sorted(df_raw['Loại hình'].unique().tolist()) if 'Loại hình' in df_raw.columns else []
            
            with c1: pk_f = st.multiselect("Lọc Phân khu", options=pk_options)
            with c2: lh_f = st.multiselect("Lọc Loại hình", options=lh_options)
            with c3:
                max_price = float(df_raw['Giá bán'].max()) if 'Giá bán' in df_raw.columns else 15.0
                price_f = st.slider("Khoảng giá (Tỷ)", 0.0, max(15.0, max_price), (0.0, max(15.0, max_price)), step=0.1)

            # Thực hiện lọc dữ liệu
            df = df_raw.copy()
            if pk_f: df = df[df['Phân khu'].isin(pk_f)]
            if lh_f: df = df[df['Loại hình'].isin(lh_f)]
            if 'Giá bán' in df.columns:
                df = df[(df['Giá bán'] >= price_f[0]) & (df['Giá bán'] <= price_f[1])]

            # Xử lý hiển thị (Ẩn mã căn nếu không phải Admin)
            view_df = df.copy()
            if not is_admin and 'Mã căn' in view_df.columns:
                view_df = view_df.drop(columns=['Mã căn'])

            st.write(f"🔍 Tìm thấy **{len(view_df)}** căn hộ")
            
            # Hiển thị bảng
            sel = st.dataframe(
                view_df, 
                use_container_width=True, 
                hide_index=True, 
                on_select="rerun", 
                selection_mode="single-row"
            )

            # HIỂN THỊ CHI TIẾT KHI CLICK CHỌN DÒNG
            if sel and sel.selection.rows:
                idx = sel.selection.rows[0]
                row = df.iloc[idx]
                st.divider()
                col_a, col_b = st.columns([1, 1])
                with col_a:
                    img_url = row.get('Link ảnh') or row.get('Ảnh')
                    if img_url:
                        st.image(img_url, use_container_width=True, caption="Ảnh thực tế căn hộ")
                    else:
                        st.info("Căn hộ này chưa có ảnh.")
                with col_b:
                    st.subheader(f"{row.get('Loại hình','-')} - Phân khu {row.get('Phân khu','-')}")
                    st.markdown(f"💰 Giá bán: **{row.get('Giá bán',0)} Tỷ**")
                    st.write(f"📐 Tầng: {row.get('Khoảng tầng','-')} | 🧭 Hướng: {row.get('Hướng BC','-')}")
                    st.write(f"🛋️ Nội thất: {row.get('Nội thất','-')} | 🏠 Hiện trạng: {row.get('Hiện trạng','-')}")
                    
                    if is_admin:
                        st.error(f"🔑 MÃ CĂN NỘI BỘ: {row.get('Mã căn','N/A')}")
                    
                    st.button("🔗 Sao chép thông tin gửi khách")
        else:
            st.warning("⚠️ Hiện tại chưa có dữ liệu nào trong bảng tính. Hãy sang Tab 'Thêm hàng mới' để nhập.")

    # --- TAB 2: THÊM MỚI ---
    with tab2:
        if is_admin:
            with st.form("add_form", clear_on_submit=True):
                st.write("### 📝 Nhập thông tin căn hộ mới")
                f1, f2, f3 = st.columns(3)
                with f1:
                    f_ngay = st.date_input("Ngày lên hàng")
                    f_loai = st.selectbox("Loại hình", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
                    f_pk = st.selectbox("Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
                with f2:
                    f_ma = st.text_input("Mã căn (Dành cho Admin)")
                    f_tang = st.selectbox("Khoảng tầng", ["Thấp", "Trung", "Cao"])
                    f_gia = st.number_input("Giá bán (Tỷ)", value=3.5, step=0.1)
                with f3:
                    f_nt = st.text_input("Nội thất")
                    f_huong = st.text_input("Hướng ban công")
                    f_anh = st.text_input("Link ảnh")
                
                if st.form_submit_button("🚀 Lưu vào hệ thống"):
                    try:
                        # Tự động lấy danh sách tiêu đề hiện có trên Sheet để ghi cho đúng vị trí
                        headers = sheet_obj.row_values(1)
                        new_row = [""] * len(headers)
                        
                        # Khớp dữ liệu vào đúng cột dựa trên tên tiêu đề
                        mapping = {
                            "Ngày lên hàng": str(f_ngay),
                            "Loại hình": f_loai,
                            "Phân khu": f_pk,
                            "Mã căn": f_ma,
                            "Khoảng tầng": f_tang,
                            "Nội thất": f_nt,
                            "Hướng BC": f_huong,
                            "Giá bán": f_gia,
                            "Link ảnh": f_anh,
                            "Trạng thái": "Đang bán"
                        }
                        
                        for i, h in enumerate(headers):
                            h_clean = h.strip()
                            if h_clean in mapping:
                                new_row[i] = mapping[h_clean]
                        
                        sheet_obj.append_row(new_row)
                        st.success("Đã lưu thành công! Hãy bấm 'Cập nhật danh sách' ở thanh bên trái.")
                        st.cache_resource.clear()
                    except Exception as e:
                        st.error(f"Lỗi khi lưu: {e}")
        else:
            st.warning("⚠️ Bạn cần nhập mật khẩu Admin để sử dụng tính năng thêm hàng.")
