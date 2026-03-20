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
        sheet = client.open_by_key("19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk").sheet1
        df = pd.DataFrame(sheet.get_all_records())
        df.columns = df.columns.str.strip()
        if 'Giá bán' in df.columns:
            df['Giá bán'] = pd.to_numeric(df['Giá bán'], errors='coerce').fillna(0)
        return df, sheet
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return pd.DataFrame(), None

df_raw, sheet_obj = get_data()

# 2. PHÂN QUYỀN (SIDEBAR)
with st.sidebar:
    st.title("🔑 Đăng nhập")
    pw = st.text_input("Mật khẩu Admin", type="password")
    is_admin = (pw == "admin123")
    st.info("Quyền: ADMIN" if is_admin else "Quyền: CTV")

# 3. GIAO DIỆN CHÍNH
st.title("🏢 Kho Hàng Vinhomes Smart City")

if sheet_obj is not None:
    t1, t2 = st.tabs(["📋 Danh sách", "➕ Thêm hàng"])
    
    with t1:
        if df_raw.empty:
            st.warning("Chưa có dữ liệu.")
        else:
            # Bộ lọc nhanh
            c1, c2, c3 = st.columns(3)
            with c1: pk = st.multiselect("Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
            with c2: lh = st.multiselect("Loại hình", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
            with c3: gia = st.slider("Giá (Tỷ)", 1.5, 10.0, (2.0, 5.0))

            # Lọc dữ liệu
            df_f = df_raw.copy()
            if pk: df_f = df_f[df_f['Phân khu'].isin(pk)]
            if lh: df_f = df_f[df_f['Loại hình'].isin(lh)]
            df_f = df_f[(df_f['Giá bán'] >= gia[0]) & (df_f['Giá bán'] <= gia[1])]

            # Ẩn mã căn nếu là CTV
            view_df = df_f.drop(columns=['Mã căn']) if (not is_admin and 'Mã căn' in df_f.columns) else df_f
            
            # Hiển thị bảng
            sel = st.dataframe(view_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

            # Hiện chi tiết khi bấm vào dòng
            if sel and sel.selection.rows:
                row = df_f.iloc[sel.selection.rows[0]]
                st.divider()
                col_a, col_b = st.columns(2)
                with col_a:
                    if row.get('Link ảnh'): st.image(row['Link ảnh'], use_container_width=True)
                with col_b:
                    st.subheader(f"{row.get('Loại hình')} - {row.get('Phân khu')}")
                    st.write(f"💰 Giá: **{row.get('Giá bán')} Tỷ**")
                    st.write(f"📐 Tầng: {row.get('Khoảng tầng')} | 🧭 Hướng: {row.get('Hướng BC')}")
                    if is_admin: st.error(f"🔑 MÃ CĂN: {row.get('Mã căn')}")
                    st.button("🔗 Gửi link cho khách")

    with t2:
        if is_admin:
            with st.form("add"):
                st.write("### Nhập căn hộ mới")
                f1, f2 = st.columns(2)
                with f1:
                    ngay = st.date_input("Ngày")
                    loai = st.selectbox("Loại", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
                    pk_n = st.selectbox("Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
                    ma = st.text_input("Mã căn")
                with f2:
                    tg = st.selectbox("Tầng", ["Thấp", "Trung", "Cao"])
                    gb = st.number_input("Giá (Tỷ)", step=0.1)
                    anh = st.text_input("Link ảnh")
                    tt = st.radio("Trạng thái", ["Đang bán", "Đã bán"], horizontal=True)
                if st.form_submit_button("Lưu"):
                    sheet_obj.append_row([str(ngay), loai, pk_n, ma, tg, "", "", gb, "", anh, tt])
                    st.success("Đã thêm! Hãy tải lại trang.")
        else:
            st.warning("Nhập mật khẩu Admin để thêm hàng.")
