import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

@st.cache_resource
def load_data():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        ss = client.open_by_key("19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk")
        sh = ss.get_worksheet(0)
        raw = sh.get_all_values()
        if not raw or len(raw) < 1: return pd.DataFrame(), sh
        cols = [str(h).strip() for h in raw[0]]
        df = pd.DataFrame(raw[1:], columns=cols)
        if "Giá bán" in df.columns:
            df["Giá bán"] = pd.to_numeric(
                df["Giá bán"].astype(str).str.replace(',', '.'), 
                errors='coerce'
            ).fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame(), None

df_raw, sheet_obj = load_data()

# --- THANH LOGIN GỌN GÀNG ---
t_col1, t_col2 = st.columns([7, 3])
with t_col2:
    pw = st.text_input(
        "Admin Login", 
        type="password", 
        label_visibility="collapsed", 
        placeholder="Nhập pass xem mã căn..."
    )
    is_admin = (pw == "admin123")
    btn_c1, btn_c2 = st.columns(2)
    with btn_c1:
        if is_admin: st.success("Chào Admin")
    with btn_c2:
        if st.button("🔄 Làm mới"):
            st.cache_resource.clear()
            st.rerun()

# --- HỘP THOẠI CHI TIẾT ---
@st.dialog("Thông tin căn hộ", width="large")
def show_details(row, admin_mode):
    copy_text = (
        f"🏢 CĂN HỘ VINHOMES SMART CITY\n"
        f"📍 Phân khu: {row.get('Phân khu')}\n"
        f"✨ Loại hình: {row.get('Loại hình')}\n"
        f"📐 Diện tích: {row.get('Diện tích')} m2\n"
        f"🧭 Hướng: {row.get('Hướng BC')}\n"
        f"🛋️ Nội thất: {row.get('Nội thất')}\n"
        f"💰 Giá bán: {row.get('Giá bán', 0):.2f} Tỷ\n"
        f"📞 Liên hệ em để xem nhà trực tiếp!"
    )
    col_img, col_info = st.columns([1, 1])
    with col_img:
        if row.get('Link ảnh'): st.image(row['Link ảnh'], use_container_width=True)
        else: st.info("Hình ảnh đang cập nhật...")
    with col_info:
        st.subheader(f"{row.get('Loại hình')} - {row.get('Phân khu')}")
        st.write(f"📐 {row.get('Diện tích')} m2 | 🧭 {row.get('Hướng BC')}")
        st.write(f"🛋️ Nội thất: {row.get('Nội thất')}")
        st.markdown(f"### 💰 Giá: {row.get('Giá bán', 0):.2f} Tỷ")
        if admin_mode:
            st.error(f"🔑 MÃ CĂN: {row.get('Mã căn')}")
        st.write("---")
        st.write("📋 Nội dung copy gửi khách:")
        st.code(copy_text, language="text")

# --- TRANG CHÍNH ---
st.title("🏢 Kho Hàng Vinhomes Smart City")
if sheet_obj is not None:
    # Chia nhỏ danh sách tab để tránh lỗi Syntax
    tab_names = ["📋 Danh sách", "➕ Thêm hàng"]
    tab_list, tab_add = st.tabs(tab_names)
    
    with tab_list:
        f1, f2, f3 = st.columns(3)
        pks = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
        lhs = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
        with f1: pk_f = st.multiselect("Phân khu", pks)
        with f2: lh_f = st.multiselect("Loại hình", lhs)
        with f3: pr_f = st.slider("Giá (Tỷ)", 0.0, 15.0, (0.0, 15.0), 0.1)

        df = df_raw.copy()
        if pk_f: df = df[df['Phân khu'].isin(pk_f)]
        if lh_f: df = df[df['Loại hình'].isin(lh_f)]
        df = df[(df['Giá bán'] >= pr_f[0]) & (df['Giá bán'] <= pr_f[1])]

        display_df = df.copy()
        if 'Mã căn' in display_df.columns:
            display_df = display_df.drop(columns=['Mã căn'])

        st.info(f"💡 Nhấn vào dòng để xem chi tiết. Tìm thấy {len(df)} căn.")
        sel = st.dataframe(
            display_df, 
            use_container_width=True, 
            hide_index=True, 
            on_select="rerun", 
            selection_mode="single-row"
        )
        if sel and sel.selection.rows:
            show_details(df.iloc[sel.selection.rows[0]], is_admin)

    with tab_add:
        if is_admin:
            with st.form("form_add", clear_on_submit=True):
                st.write("### 📝 Thêm căn hộ mới")
                c1, c2, c3 = st.columns(3)
                with c1:
                    n_ngay = st.date_input("Ngày")
                    n_loai = st.selectbox("Loại hình", lhs)
                    n_pk = st.selectbox("Phân khu", pks)
                with c2:
                    n_ma = st.text_input("Mã căn")
                    n_dt = st.number_input("Diện tích (m2)", 0.0, step=0.1)
                    n_tg = st.selectbox("Tầng", ["Thấp", "Trung", "Cao"])
                with c3:
                    nts = ["Nguyên bản", "Cơ bản", "Full đồ"]
                    hbc_l = ["Đông", "Tây", "Nam", "Bắc", "ĐB", "ĐN", "TB", "TN"]
