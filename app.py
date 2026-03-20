import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# --- DANH SÁCH CẤU HÌNH (Rút ngắn để chống lỗi) ---
PK_L = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
LH_L = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
H_L = ["Đông", "Tây", "Nam", "Bắc", "Đông Bắc", "Đông Nam", "Tây Bắc", "Tây Nam"]
NT_L = ["Nguyên bản", "Cơ bản", "Full đồ"]
TG_L = ["Thấp", "Trung", "Cao"]

@st.cache_resource
def load_data():
    try:
        s = st.secrets["gcp_service_account"]
        sc = ["https://spreadsheets.google.com/feeds", 
              "https://www.googleapis.com/auth/drive"]
        c = ServiceAccountCredentials.from_json_keyfile_dict(s, sc)
        g = gspread.authorize(c)
        k = "19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk"
        ss = g.open_by_key(k)
        sh = ss.get_worksheet(0)
        r = sh.get_all_values()
        if not r or len(r) < 1: return pd.DataFrame(), sh
        df = pd.DataFrame(r[1:], columns=[h.strip() for h in r[0]])
        if "Giá bán" in df.columns:
            df["Giá bán"] = pd.to_numeric(
                df["Giá bán"].str.replace(',', '.'), 
                errors='coerce'
            ).fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame(), None

df_raw, sh_obj = load_data()

# --- THANH HEADER SIÊU GỌN GÓC PHẢI ---
h1, h2 = st.columns([7.5, 2.5])
with h2:
    sub1, sub2 = st.columns([4, 1])
    with sub1:
        p_in = st.text_input("P", type="password", 
                            label_visibility="collapsed", 
                            placeholder="Mật khẩu Admin...")
        is_adm = (p_in == "admin123")
    with sub2:
        if st.button("🔄"):
            st.cache_resource.clear()
            st.rerun()
    if is_adm:
        st.markdown(
            "<p style='text-align:right;color:green;font-size:12px;margin:0;'>Admin Mode ✅</p>", 
            unsafe_allow_html=True
        )

# --- DIALOG CHI TIẾT (BẢO MẬT) ---
@st.dialog("📋 Chi tiết căn hộ", width="large")
def show_dt(row, adm):
    c_img, c_txt = st.columns([1, 1])
    with c_img:
        if row.get('Link ảnh'): 
            st.image(row['Link ảnh'], use_container_width=True)
        else: st.info("Chưa có ảnh thực tế")
    with c_txt:
        st.subheader(f"🏢 {row.get('Loại hình')} - {row.get('Phân khu')}")
        st.write(f"📐 **Diện tích:** {row.get('Diện tích')} m2")
        st.write(f"🧭 **Hướng:** {row.get('Hướng BC')} | 🛋️ **Nội thất:** {row.get('Nội thất')}")
        st.markdown(f"### 💰 Giá: {row.get('Giá bán', 0):.2f} Tỷ")
        if adm: st.error(f"🔑 MÃ CĂN: {row.get('Mã căn')}")
        st.divider()
        # Nội dung copy (An toàn cho khách)
        t = "🏢 VINHOMES SMART CITY\n"
        t += f"📍 Khu: {row.get('Phân khu')}\n"
        t += f"✨ Loại: {row.get('Loại hình')}\n"
        t += f"📐 DT: {row.get('Diện tích')} m2\n"
        t += f"💰 Giá: {row.get('Giá bán', 0):.2f} Tỷ\n"
        t += "📞 Liên hệ em xem nhà ngay!"
        st.code(t, language="text")

# --- GIAO DIỆN CHÍNH ---
st.title("🏢 Kho Hàng Vinhomes")

if sh_obj is not None:
    t1, t2 = st.tabs(["📋 Danh sách", "➕ Thêm hàng"])
