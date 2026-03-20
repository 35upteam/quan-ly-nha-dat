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
        
        data = sheet.get_all_records()
        if not data:
            return pd.DataFrame(), sheet
            
        df = pd.DataFrame(data)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Ép kiểu số cho cột Giá bán
        if "Giá bán" in df.columns:
            df["Giá bán"] = pd.to_numeric(df["Giá bán"], errors='coerce').fillna(0)
        
        # SẮP XẾP: Căn mới nhất lên trên (đảo ngược dataframe)
        df = df.iloc[::-1].reset_index(drop=True)
                
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
    st.info("✅ ADMIN" if is_admin else "💡 CTV")
    st.divider()
    if st.button("🔄 Cập nhật danh sách"):
        st.cache_resource.clear()
        st.rerun()

# 4. GIAO DIỆN CHÍNH
st.title("🏢 Kho Hàng Vinhomes Smart City")

if sheet_obj is None:
    st.error("Không thể kết nối Google Sheet.")
else:
    tab1, tab2 = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])

    # --- TAB 1: DANH SÁCH ---
    with tab1:
        if not df_raw.empty:
            c1, c2, c3 = st.columns(3)
            with c1:
                pk_list = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
                pk_f = st.multiselect("Lọc Phân khu", options=pk_list)
            with c2:
                lh_list = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
                lh_f = st.multiselect("Lọc Loại hình", options=lh_list)
            with c3:
                # MẶC ĐỊNH KHOẢNG GIÁ 0 - 10 TỶ
                price_f = st.slider("Khoảng giá (Tỷ)", 0.0, 10.0, (0.0, 10.0), step=0.050)

            df = df_raw.copy()
            if pk_f: df = df[df['Phân khu'].isin(pk_f)]
            if lh_f: df = df[df['Loại hình'].isin(lh_f)]
            if 'Giá bán' in df.columns:
                df = df[(df['Giá bán'] >= price_f[0]) & (df['Giá bán'] <= price_f[1])]

            view_df = df.copy()
            if not is_admin and 'Mã căn' in view_df.columns:
                view_df = view_df.drop(columns=['Mã căn'])

            st.write(f"🔍 Tìm thấy **{len(view_df)}** căn hộ (Mới nhất ở trên)")
            sel = st.dataframe(view_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

            if sel and sel.selection.rows:
                idx = sel.selection.rows[0]
                row = df.iloc[idx]
                st.divider()
                ca, cb = st.columns([1, 1])
                with ca:
                    img = row.get('Link ảnh')
                    if img: st.image(img, use_container_width=True)
                    else: st.info("Không có ảnh.")
                with cb:
                    st.subheader(f"{row.get('Loại hình')} - Phân khu {row.get('Phân khu')}")
                    st.markdown(f"💰 Giá bán: **{row.get('Giá bán',0):.3f} Tỷ**")
                    st.write(f"📐 Tầng: {row.get('Khoảng tầng')} | 🧭 Hướng: {row.get('Hướng BC')}")
                    st.write(f"🛋️ Nội thất: {row.get('Nội thất')} | 🏠 Trạng thái: {row.get('Trạng thái')}")
                    if is_admin: st.error(f"🔑 MÃ CĂN: {row.get('Mã căn')}")
                    st.button("🔗 Sao chép thông tin")
        else:
            st.warning("Chưa có dữ liệu.")

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
                    f_ma = st.text_input("Mã căn")
                with f2:
                    f_tang = st.selectbox("Khoảng tầng", ["Thấp", "Trung", "Cao"])
                    # LỰA CHỌN NỘI THẤT
                    f_nt = st.selectbox("Nội thất", ["Nguyên bản", "Cơ bản", "Đầy đủ nội thất"])
                    # LỰA CHỌN HƯỚNG BAN CÔNG
                    f_huong = st.selectbox("Hướng ban công", ["Đông", "Tây", "Nam", "Bắc", "Đông Bắc", "Đông Nam", "Tây Bắc", "Tây Nam"])
                with f3:
                    # NHẬP GIÁ KIỂU 1.200
                    f_gia = st.number_input("Giá bán (Ví dụ: 2.550)", min_value=0.0, step=0.001, format="%.3f")
                    f_anh = st.text_input("Link ảnh")
                    f_tt = st.radio("Trạng thái", ["Đang bán", "Đã bán"], horizontal=True)
                
                if st.form_submit_button("🚀 Lưu vào hệ thống"):
                    try:
                        headers = sheet_obj.row_values(1)
                        new_row = [""] * len(headers)
                        mapping = {
                            "Ngày lên hàng": str(f_ngay), "Loại hình": f_loai, "Phân khu": f_pk,
                            "Mã căn": f_ma, "Khoảng tầng": f_tang, "Nội thất": f_nt,
                            "Hướng BC": f_huong, "Giá bán": f_gia, "Link ảnh": f_anh, "Trạng thái": f_tt
                        }
                        for i, h in enumerate(headers):
                            if h.strip() in mapping: new_row[i] = mapping[h.strip()]
                        
                        sheet_obj.append_row(new_row)
                        st.success("Đã lưu! Hãy bấm 'Cập nhật danh sách' ở Sidebar.")
                        st.cache_resource.clear()
                    except Exception as e:
                        st.error(f"Lỗi: {e}")
        else:
            st.warning("⚠️ Nhập mật khẩu Admin để thêm hàng.")
