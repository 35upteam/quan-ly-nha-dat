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
        
        spreadsheet = client.open_by_key("19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk")
        sheet = spreadsheet.get_worksheet(0)
        
        raw = sheet.get_all_values()
        if len(raw) <= 1: return pd.DataFrame(), sheet
        
        # Định nghĩa 11 cột chuẩn để khớp mọi dữ liệu cũ/mới
        cols = ["Ngày", "Loại hình", "Phân khu", "Mã căn", "Tầng", "Nội thất", "Hướng", "Giá", "Hiện trạng", "Link ảnh", "Trạng thái"]
        df = pd.DataFrame(raw[1:])
        
        # Bù cột nếu hàng cũ bị thiếu
        for i in range(len(df.columns), len(cols)): df[i] = ""
        df = df.iloc[:, :len(cols)]
        df.columns = cols
        
        # Ép kiểu số cho cột Giá để lọc slider
        df["Giá"] = pd.to_numeric(df["Giá"], errors='coerce').fillna(0)
        return df, sheet
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame(), None

df_raw, sheet_obj = get_data()

# 3. THANH BÊN (SIDEBAR)
with st.sidebar:
    st.header("🔑 Phân quyền")
    pw = st.text_input("Mật khẩu Admin", type="password")
    is_admin = (pw == "admin123")
    st.info("✅ ADMIN" if is_admin else "💡 CTV")
    if st.button("🔄 Cập nhật danh sách"):
        st.cache_resource.clear()
        st.rerun()

# 4. GIAO DIỆN CHÍNH
st.title("🏢 Kho Hàng Vinhomes Smart City")

if sheet_obj is not None:
    tab1, tab2 = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])

    with tab1:
        # BỘ LỌC ĐẦY ĐỦ
        c1, c2, c3 = st.columns(3)
        with c1: pk_f = st.multiselect("Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
        with c2: lh_f = st.multiselect("Loại hình", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
        with c3: price_f = st.slider("Giá (Tỷ)", 1.0, 15.0, (1.0, 15.0), step=0.1)

        if df_raw.empty:
            st.warning("⚠️ Hiện tại chưa có dữ liệu.")
        else:
            df = df_raw.copy()
            # Thực hiện lọc
            if pk_f: df = df[df['Phân khu'].isin(pk_f)]
            if lh_f: df = df[df['Loại hình'].isin(lh_f)]
            df = df[(df['Giá'] >= price_f[0]) & (df['Giá'] <= price_f[1])]

            # Ẩn mã căn nếu là CTV
            view_df = df.copy()
            if not is_admin and 'Mã căn' in view_df.columns:
                view_df = view_df.drop(columns=['Mã căn'])

            st.write(f"🔍 Tìm thấy **{len(view_df)}** căn")
            
            # Hiển thị bảng có chức năng chọn dòng (selection)
            sel = st.dataframe(view_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

            # HIỂN THỊ CHI TIẾT KHI CHỌN DÒNG
            if sel and sel.selection.rows:
                idx = sel.selection.rows[0]
                row = df.iloc[idx]
                st.divider()
                col_a, col_b = st.columns(2)
                with col_a:
                    if row.get('Link ảnh'): st.image(row['Link ảnh'], use_container_width=True, caption="Ảnh thực tế")
                    else: st.info("Căn hộ này chưa có ảnh.")
                with col_b:
                    st.subheader(f"{row.get('Loại hình')} - {row.get('Phân khu')}")
                    st.write(f"💰 Giá: **{row.get('Giá')} Tỷ**")
                    st.write(f"📐 Tầng: {row.get('Tầng')} | 🧭 Hướng: {row.get('Hướng')}")
                    st.write(f"🛋️ Nội thất: {row.get('Nội thất')} | 🏠 Hiện trạng: {row.get('Hiện trạng')}")
                    if is_admin: st.error(f"🔑 MÃ CĂN NỘI BỘ: {row.get('Mã căn')}")
                    st.button("🔗 Sao chép thông tin gửi khách")

    with tab2:
        if is_admin:
            with st.form("add_form", clear_on_submit=True):
                st.write("### Nhập căn hộ mới")
                f1, f2, f3 = st.columns(3)
                with f1:
                    ngay = st.date_input("Ngày lên hàng")
                    loai = st.selectbox("Loại hình", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
                    pk_n = st.selectbox("Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
                with f2:
                    ma = st.text_input("Mã căn")
                    tg = st.selectbox("Khoảng tầng", ["Thấp", "Trung", "Cao"])
                    gia = st.number_input("Giá (Tỷ)", value=3.5, step=0.1)
                with f3:
                    nt = st.text_input("Nội thất")
                    h_bc = st.text_input("Hướng BC")
                    anh = st.text_input("Link ảnh")
                    tt = st.radio("Trạng thái", ["Đang bán", "Đã bán"], horizontal=True)
                
                if st.form_submit_button("🚀 Lưu dữ liệu"):
                    try:
                        # Ghi đủ 11 cột để đồng bộ với hàng cũ
                        sheet_obj.append_row([str(ngay), loai, pk_n, ma, tg, nt, h_bc, gia, "Trống", anh, tt])
                        st.success("Đã lưu! Hãy bấm 'Cập nhật danh sách' ở Sidebar.")
                        st.cache_resource.clear()
                    except Exception as e:
                        st.error(f"Lỗi: {e}")
        else:
            st.warning("Vui lòng nhập mật khẩu Admin ở thanh bên để thêm hàng.")
