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
            df["Giá bán"] = pd.to_numeric(df["Giá bán"].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame(), None

df_raw, sheet_obj = load_data()

# --- THANH LOGIN GỌN GÀNG GÓC PHẢI ---
t_col1, t_col2 = st.columns([7, 3])
with t_col2:
    # Ô mật khẩu thu nhỏ
    pw = st.text_input("Admin Login", type="password", label_visibility="collapsed", placeholder="Nhập pass để xem mã căn...")
    is_admin = (pw == "admin123")
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if is_admin: st.success("Chào Admin")
    with btn_col2:
        if st.button("🔄 Làm mới"):
            st.cache_resource.clear()
            st.rerun()

# --- HỘP THOẠI CHI TIẾT (BẢO MẬT MÃ CĂN) ---
@st.dialog("Thông tin căn hộ", width="large")
def show_details(row, admin_mode):
    # Nội dung gửi khách (Không bao giờ có mã căn)
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
        else: st.info("Hình ảnh đang được cập nhật...")
            
    with col_info:
        st.subheader(f"{row.get('Loại hình')} - {row.get('Phân khu')}")
        st.write(f"📐 **Diện tích:** {row.get('Diện tích')} m2 | 🧭 **Hướng:** {row.get('Hướng BC')}")
        st.write(f"🛋️ **Nội thất:** {row.get('Nội thất')}")
        st.markdown(f"### 💰 Giá: {row.get('Giá bán', 0):.2f} Tỷ")
        st.write("---")
        
        # PHẦN BẢO MẬT RIÊNG CHO ADMIN
        if admin_mode:
            st.error(f"🔑 MÃ CĂN HỘ: {row.get('Mã căn')}")
            st.caption("(Thông tin này chỉ hiển thị khi bạn đã đăng nhập)")
        
        st.write("📋 **Nội dung copy gửi khách:**")
        st.code(copy_text, language="text")

# --- TRANG CHÍNH ---
st.title("🏢 Kho Hàng Vinhomes Smart City")

if sheet_obj is not None:
    tab_list, tab_add = st.tabs(["📋 Danh sách", "➕ Thêm
