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
        
        # Đọc toàn bộ giá trị thô
        raw_data = sheet_instance.get_all_values()
        
        if len(raw_data) <= 1: 
            return pd.DataFrame(), sheet_instance
            
        # Tự định nghĩa lại tên cột để không bị phụ thuộc vào Google Sheet
        # Thứ tự: Ngày, Loại hình, Phân khu, Mã căn, Tầng, Nội thất, Hướng, Giá, Hiện trạng, Link ảnh, Trạng thái
        columns = ["Ngày", "Loại hình", "Phân khu", "Mã căn", "Tầng", "Nội thất", "Hướng", "Giá", "Hiện trạng", "Link ảnh", "Trạng thái"]
        
        # Lấy dữ liệu từ dòng 2 trở đi, ép vào đúng số lượng cột định sẵn
        df = pd.DataFrame(raw_data[1:], columns=raw_data[0][:len(raw_data[0])])
        
        # Ép lại tên cột chuẩn để Code bên dưới chạy được
        df.columns = columns[:len(df.columns)]
        
        # Chuẩn hóa cột Giá
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
    st.error("Không thể kết nối. Kiểm tra lại quyền Service Account.")
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
            price_f = st.slider("Khoảng giá (Tỷ)", 1.0, 15.0, (1.0, 10.0), step=0.1)

        if df_raw.empty:
            st.warning("⚠️ Hiện chưa thấy dữ liệu. Hãy thử sang Tab 'Thêm mới' nhập 1 căn rồi quay lại đây.")
        else:
            df = df_raw.copy()
            # Lọc theo Phân khu
            if pk_f: df = df[df['Phân khu'].isin(pk_f)]
            # Lọc theo Loại hình
            if lh_f: df = df[df['Loại hình'].isin(lh_f)]
            # Lọc theo Giá
            df = df[(df['Giá'] >= price_f[0]) & (df['Giá'] <= price_f[1])]

            # Phân quyền 
            display_df = df.copy()
            if not is_admin and 'Mã căn' in display_df.columns:
                display_df = display_df.drop(columns=['Mã căn'])

            st.write(f"🔍 Tìm thấy **{len(display_df)}** căn hộ")

            # Bảng hiển thị
            selection = st.dataframe(display_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

            if selection and selection.selection.rows:
                idx = selection.selection.rows[0]
                row = df.iloc[idx]
                st.divider()
                col_a, col_b = st.columns(2)
                with col_a:
                    if row.get('Link ảnh'): st.image(row['Link ảnh'], use_container_width=True)
                    else: st.info("Chưa có ảnh.")
                with col_b:
                    st.subheader(f"{row.get('Loại hình')} - {row.get('Phân khu')}")
                    st.write(f"💰 Giá: {row.get('Giá')} Tỷ | Tầng: {row.get('Tầng')}")
                    if is_admin: st.error(f"🔑 MÃ CĂN: {row.get('Mã căn')}")
                    st.button("🔗 Sao chép thông tin")

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
                    f_tang = st.selectbox("Khoảng tầng", ["Thấp", "Trung", "Cao"])
                    f_gia = st.number_input("Giá (Tỷ)", value=3.5, step=0.1)
                with f3:
                    f_anh = st.text_input("Link ảnh")
                    f_tt = st.radio("Trạng thái", ["Đang bán", "Đã bán"], horizontal=True)
                
                if st.form_submit_button("🚀 Lưu dữ liệu"):
                    try:
                        # Ghi dữ liệu: Đảm bảo đúng 11 cột như danh sách bên trên
                        sheet_obj.append_row([str(f_ngay), f_loai, f_pk, f_ma, f_tang, "", "", f_gia, "", f_anh, f_tt])
                        st.success("Đã lưu! Hãy nhấn 'Cập nhật danh sách mới' ở Sidebar.")
                        st.cache_resource.clear()
                    except Exception as e:
                        st.error(f"Lỗi: {e}")
        else:
            st.warning("⚠️ Nhập mật khẩu Admin để thêm hàng.")
