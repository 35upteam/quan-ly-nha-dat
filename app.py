import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Vinhomes Smart City Manager", layout="wide", page_icon="🏢")

# 2. KẾT NỐI DỮ LIỆU
@st.cache_resource
def get_gspread_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Lỗi cấu hình Secrets: {e}")
        return None

# 3. HÀM TẢI DỮ LIỆU
def load_data(sheet_client):
    try:
        # ID file Google Sheet của bạn
        SHEET_ID = "19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk"
        sheet = sheet_client.open_by_key(SHEET_ID).sheet1
        data = sheet.get_all_records()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        # Chuẩn hóa tên cột (xóa khoảng trắng thừa)
        df.columns = df.columns.str.strip()
        # Ép kiểu số cho Giá bán
        if 'Giá bán' in df.columns:
            df['Giá bán'] = pd.to_numeric(df['Giá bán'], errors='coerce').fillna(0)
        return df, sheet
    except Exception as e:
        st.error(f"Lỗi đọc dữ liệu từ Google Sheets: {e}")
        return pd.DataFrame(), None

# 4. GIAO DIỆN THANH BÊN (SIDEBAR)
with st.sidebar:
    st.header("🔑 Phân quyền")
    admin_pass = st.text_input("Mật khẩu Admin", type="password")
    is_admin = (admin_pass == "admin123") # Mật khẩu của bạn
    
    if is_admin:
        st.success("✅ CHẾ ĐỘ: ADMIN")
    else:
        st.info("💡 CHẾ ĐỘ: CTV (Ẩn mã căn)")

# 5. XỬ LÝ CHÍNH
client = get_gspread_client()
if client:
    df_raw, sheet_obj = load_data(client)
    
    st.title("🏢 Kho Hàng Vinhomes Smart City")
    tab_view, tab_add = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])

    # --- TAB 1: XEM DANH SÁCH ---
    with tab_view:
        if df_raw.empty:
            st.warning("Hiện chưa có dữ liệu hoặc file Google Sheet đang trống.")
        else:
            # Bộ lọc
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                pk_list = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
                pk_f = st.multiselect("Phân khu", options=pk_list)
            with c2:
                lh_list = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
                lh_f = st.multiselect("Loại hình", options=lh_list)
            with c3:
                price_f = st.slider("Khoảng giá (Tỷ)", 1.5, 12.0, (2.0, 6.0), step=0.1)
            with c4:
                st_f = st.selectbox("Trạng thái", ["Đang bán", "Đã bán", "Tất cả"])

            # Thực hiện lọc dữ liệu
            df = df_raw.copy()
            if pk_f and 'Phân khu' in df.columns: 
                df = df[df['Phân khu'].isin(pk_f)]
            if lh_f and 'Loại hình' in df.columns: 
                df = df[df['Loại hình'].isin(lh_f)]
            if 'Giá bán' in df.columns:
                df = df[(df['Giá bán'] >= price_f[0]) & (df['Giá bán'] <= price_f[1])]
            if st_f != "Tất cả" and 'Trạng thái' in df.columns: 
                df = df[df['Trạng thái'] == st_f]

            # Ẩn mã căn nếu không phải Admin
            display_df = df.copy()
            if not is_admin and 'Mã căn' in display_df.columns:
                display_df = display_df.drop(columns=['Mã căn'])

            st.write(f"🔍 Tìm thấy **{len(display_df)}** căn phù hợp")

            # Bảng hiển thị
            selection = st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )

            # Chi tiết khi chọn dòng
            if selection and hasattr(selection, 'selection') and len(selection.selection.get('rows', [])) > 0:
                row_idx = selection.selection.rows[0]
                selected_row = df.iloc[row_idx]
                
                st.divider()
                col_a, col_b = st.columns([1, 1])
                with col_a:
                    img_link = selected_row.get('Link ảnh', '')
                    if img_link:
                        st.image(img_link, use_container_width=True)
                    else:
                        st.info("Căn hộ này chưa có ảnh thực tế.")
                
                with col_b:
                    st.subheader
