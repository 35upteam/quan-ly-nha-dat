import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# --- DANH MỤC DỮ LIỆU ---
PK_L = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
LH_L = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
H_L = ["Đông", "Tây", "Nam", "Bắc", "Đông Bắc", "Đông Nam", "Tây Bắc", "Tây Nam"]
NT_L = ["Nguyên bản", "Cơ bản", "Full đồ"]
TG_L = ["Thấp", "Trung", "Cao"]

@st.cache_resource
def load_data():
    try:
        s = st.secrets["gcp_service_account"]
        sc = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        c = ServiceAccountCredentials.from_json_keyfile_dict(s, sc)
        g = gspread.authorize(c)
        ss = g.open_by_key("19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk")
        sh = ss.get_worksheet(0)
        r = sh.get_all_values()
        if not r or len(r) < 1: return pd.DataFrame(), sh
        df = pd.DataFrame(r[1:], columns=[h.strip() for h in r[0]])
        if "Giá bán" in df.columns:
            df["Giá bán"] = pd.to_numeric(df["Giá bán"].str.replace(',', '.'), errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame(), None

df_raw, sh_obj = load_data()

# --- XỬ LÝ TRẠNG THÁI ---
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

# --- HEADER ---
h1, h2 = st.columns([7, 3])
with h2:
    s1, s2 = st.columns([5, 1])
    
    with s1:
        if not st.session_state.admin_logged_in:
            p_in = st.text_input("Admin", type="password", label_visibility="collapsed", placeholder="Nhập Pass...")
            if p_in == "admin123":
                st.session_state.admin_logged_in = True
                st.rerun()
        else:
            # Chữ Admin Mode to hơn và sát nút X
            st.markdown(
                """
                <div style='text-align: right; padding-top: 5px;'>
                    <span style='color: #28a745; font-size: 16px; font-weight: bold;'>
                        Admin Mode ✅
                    </span>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
    with s2:
        # Nút Refresh hoặc Nút X Đỏ tùy trạng thái
        if st.session_state.admin_logged_in:
            if st.button("❌", help="Thoát Admin"):
                st.session_state.admin_logged_in = False
                st.rerun()
        else:
            if st.button("🔄"):
                st.cache_resource.clear()
                st.rerun()

is_adm = st.session_state.admin_logged_in

# --- DIALOG CHI TIẾT ---
@st.dialog("📋 Chi tiết căn hộ", width="large")
def show_dt(row, adm):
    c_i, c_t = st.columns([1, 1])
    with c_i:
        if row.get('Link ảnh'): st.image(row['Link ảnh'], use_container_width=True)
        else: st.info("Chưa có ảnh thực tế")
    with c_t:
        st.subheader(f"🏢 {row.get('Loại hình')} - {row.get('Phân khu')}")
        st.write(f"📐 **Diện tích:** {row.get('Diện tích')} m2")
        st.write(f"🧭 **Hướng:** {row.get('Hướng BC')} | 🛋️ **Nội thất:** {row.get('Nội thất')}")
        st.markdown(f"### 💰 Giá: {row.get('Giá bán', 0):.2f} Tỷ")
        if adm: st.error(f"🔑 MÃ CĂN: {row.get('Mã căn')}")
        st
