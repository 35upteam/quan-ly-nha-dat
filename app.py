import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# 1. THIẾT LẬP KẾT NỐI
st.set_page_config(page_title="Vinhomes Smart City", layout="wide")

@st.cache_resource
def get_data():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        # Thay ID Sheet của bạn vào đây nếu cần
        sheet = client.open_by_key("19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk").sheet1
        
        data = sheet.get_all_records()
        if not data:
            return pd.DataFrame(), sheet
            
        df = pd.DataFrame(data)
        
        # SỬA LỖI: Ép tên cột về dạng chuỗi trước khi strip
        df.columns = [str(c).strip() for c in df.columns]
        
        # Chuẩn hóa cột Giá bán
        if 'Giá bán' in df.columns:
            df['Giá bán'] = pd.to_numeric(df['Giá bán'], errors='coerce').fillna(0)
        return df, sheet
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return pd.DataFrame(), None

df_raw, sheet_obj = get_data()

# 2. PHÂN QUYỀN (SIDEBAR)
with st.sidebar:
    st.title("🔑 Đăng nhập")
    pw = st.text_input("Mật khẩu Admin", type="password")
    is_admin = (pw == "admin123") # Bạn có thể đổi mật khẩu tại đây
    if is_admin:
        st.success("Quyền: ADMIN")
    else:
        st.info("Quyền: CTV (Ẩn mã căn)")

# 3. GIAO DIỆN CHÍNH
st.title("🏢 Kho Hàng Vinhomes Smart City")

if sheet_obj is not None:
    t1, t2 = st.tabs(["📋 Danh sách", "➕ Thêm hàng"])
    
    with t1:
        if df_raw.empty:
            st.warning("Chưa có dữ liệu trong bảng tính.")
        else:
            # Bộ lọc nhanh
            c1, c2, c3 = st.columns(3)
            with c1: 
                pk_list = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
                pk = st.multiselect("Phân khu", options=pk_list)
            with c2: 
                lh_list = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
                lh = st.multiselect("Loại hình", options=lh_list)
            with c3: 
                gia = st.slider("Giá (Tỷ)", 1.0, 10.0, (2.0, 5.0), step=0.1)

            # Lọc dữ liệu an toàn
            df_f = df_raw.copy()
            if pk and 'Phân khu' in df_f.columns:
                df_f = df_f[df_f['Phân khu'].isin(pk)]
            if lh and 'Loại hình' in df_f.columns:
                df_f = df_f[df_f['Loại hình'].isin(lh)]
            if 'Giá bán' in df_f.columns:
                df_f = df_f[(df_f['Giá bán'] >= gia[0]) & (df_f['Giá bán'] <= gia[1])]

            # Ẩn mã căn nếu là CTV
            view_df = df_f.copy()
            if not is_admin and 'Mã căn' in view_df.columns:
                view_df = view_df.drop(columns=['Mã căn'])
            
            # Hiển thị bảng
            sel = st.dataframe(view_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

            # Hiện chi tiết khi bấm vào dòng
            if sel and sel.selection.rows:
                row = df_f.iloc[sel.selection.rows[0]]
                st.divider()
                col_a, col_b = st.columns(2)
                with col_a:
                    link_anh = row.get('Link ảnh', '')
                    if link_anh:
                        st.image(link_anh, use_container_width=True, caption="Ảnh căn hộ")
                    else:
                        st.info("Căn hộ này chưa có ảnh thực tế.")
                with col_b:
                    st.subheader(f"{row.get('Loại hình')} - {row.get('Phân khu')}")
                    st.markdown(f"💰 Giá bán: **{row.get('Giá bán')} Tỷ**")
                    st.write(f"📐 Tầng: {row.get('Khoảng tầng')} | 🧭 Hướng: {row.get('Hướng BC')}")
                    st.write(f"🛋️ Nội thất: {row.get('Nội thất')} | 🏠 Hiện trạng: {row.get('Hiện trạng')}")
                    
                    if is_admin:
                        st.error(f"🔑 MÃ CĂN NỘI BỘ: {row.get('Mã căn')}")
                    
                    st.button("🔗 Gửi thông tin cho khách")

    with t2:
        if is_admin:
            with st.form("add_new", clear_on_submit=True):
                st.write("### Nhập căn hộ mới")
                f1, f2 = st.columns(2)
                with f1:
                    ngay = st.date_input("Ngày lên hàng")
                    loai = st.selectbox("Loại hình", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
                    pk_n = st.selectbox("Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
                    ma = st.text_input("Mã căn")
                with f2:
                    tg = st.selectbox("Khoảng tầng", ["Thấp", "Trung", "Cao"])
                    gb = st.number_input("Giá (Tỷ)", step=0.1)
                    anh = st.text_input("Link ảnh")
                    tt = st.radio("Trạng thái", ["Đang bán", "Đã bán"], horizontal=True)
                
                if st.form_submit_button("🚀 Lưu vào hệ thống"):
                    try:
                        # Thứ tự cột: Ngày, Loại, Phân khu, Mã căn, Tầng, Nội thất, Hướng, Giá, Hiện trạng, Link ảnh, Trạng thái
                        sheet_obj.append_row([str(ngay), loai, pk_n, ma, tg, "", "", gb, "", anh, tt])
                        st.success("Đã thêm thành công! Hãy tải lại trang (F5).")
                    except Exception as e:
                        st.error(f"Lỗi khi lưu: {e}")
        else:
            st.warning("Vui lòng nhập mật khẩu Admin ở thanh bên trái để thêm hàng.")
