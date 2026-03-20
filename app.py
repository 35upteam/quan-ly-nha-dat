import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# --- DANH SÁCH CẤU HÌNH (Tách riêng để chống lỗi ngắt dòng) ---
LIST_PK = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
LIST_LH = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
LIST_HUONG = ["Đông", "Tây", "Nam", "Bắc", "ĐB", "ĐN", "TB", "TN"]
LIST_NT = ["Nguyên bản", "Cơ bản", "Full đồ"]
LIST_TANG = ["Thấp", "Trung", "Cao"]

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
        st.error(f"Lỗi kết nối: {e}")
        return pd.DataFrame(), None

df_raw, sheet_obj = load_data()

# --- THANH LOGIN GỌN GÀNG GÓC PHẢI ---
t_col1, t_col2 = st.columns([7, 3])
with t_col2:
    pw = st.text_input("Login", type="password", label_visibility="collapsed", placeholder="Mật khẩu Admin...")
    is_admin = (pw == "admin123")
    b1, b2 = st.columns(2)
    with b1:
        if is_admin: st.success("ADMIN")
    with b2:
        if st.button("🔄 Làm mới"):
            st.cache_resource.clear()
            st.rerun()

# --- POPUP CHI TIẾT ---
@st.dialog("Thông tin chi tiết", width="large")
def show_details(row, admin_mode):
    copy_text = (
        f"🏢 CĂN HỘ VINHOMES SMART CITY\n"
        f"📍 Phân khu: {row.get('Phân khu')}\n"
        f"✨ Loại hình: {row.get('Loại hình')}\n"
        f"📐 Diện tích: {row.get('Diện tích')} m2\n"
        f"🧭 Hướng: {row.get('Hướng BC')}\n"
        f"🛋️ Nội thất: {row.get('Nội thất')}\n"
        f"💰 Giá bán: {row.get('Giá bán', 0):.2f} Tỷ\n"
        f"📞 Liên hệ em xem nhà ngay!"
    )
    c_img, c_info = st.columns([1, 1])
    with c_img:
        if row.get('Link ảnh'): st.image(row['Link ảnh'], use_container_width=True)
        else: st.info("Chưa có ảnh thực tế")
    with c_info:
        st.subheader(f"{row.get('Loại hình')} - {row.get('Phân khu')}")
        st.write(f"📐 **{row.get('Diện tích')} m2** | 🧭 **{row.get('Hướng BC')}**")
        st.write(f"🛋️ **Nội thất:** {row.get('Nội thất')}")
        st.markdown(f"### 💰 Giá: {row.get('Giá bán', 0):.2f} Tỷ")
        if admin_mode:
            st.error(f"🔑 MÃ CĂN: {row.get('Mã căn')}")
        st.divider()
        st.write("📋 Nội dung copy gửi khách:")
        st.code(copy_text, language="text")

# --- TRANG CHÍNH ---
st.title("🏢 Kho Hàng Vinhomes Smart City")
if sheet_obj is not None:
    tab_list, tab_add = st.tabs(["📋 Danh sách", "➕ Thêm hàng
