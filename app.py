import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# --- DANH SÁCH CẤU HÌNH ---
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
        k = "19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk"
        ss = g.open_by_key(k)
        sh = ss.get_worksheet(0)
        r = sh.get_all_values()
        if not r or len(r) < 1: return pd.DataFrame(), sh
        df = pd.DataFrame(r[1:], columns=[h.strip() for h in r[0]])
        if "Giá bán" in df.columns:
            df["Giá bán"] = pd.to_numeric(df["Giá bán"].str.replace(',', '.'), errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
        return pd.DataFrame(), None

df_raw, sh_obj = load_data()

# --- HEADER GỌN GÀNG GÓC PHẢI ---
h1, h2 = st.columns([7.5, 2.5])
with h2:
    sub1, sub2 = st.columns([4, 1])
    with sub1:
        p_in = st.text_input("Admin", type="password", label_visibility="collapsed", placeholder="Mật khẩu Admin...")
        is_adm = (p_in == "admin123")
    with sub2:
        if st.button("🔄", help="Làm mới dữ liệu"):
            st.cache_resource.clear()
            st.rerun()
    if is_adm:
        st.markdown("<p style='text-align:right;color:#28a745;font-size:12px;font-weight:bold;margin:0;'>Admin Mode ✅</p>", unsafe_allow_html=True)

# --- TRANG CHÍNH ---
st.title("🏢 Kho Hàng Vinhomes Smart City")

@st.dialog("📋 Chi tiết căn hộ", width="large")
def show_dt(row, adm):
    c_img, c_txt = st.columns([1, 1])
    with c_img:
        if row.get('Link ảnh'): st.image(row['Link ảnh'], use_container_width=True)
        else: st.warning("Chưa có ảnh thực tế")
    with c_txt:
        st.subheader(f"🏢 {row.get('Loại hình')} - {row.get('Phân khu')}")
        st.write(f"📐 **Diện tích:** {row.get('Diện tích')} m2")
        st.write(f"🧭 **Hướng:** {row.get('Hướng BC')} | 🛋️ **Nội thất:** {row.get('Nội thất')}")
        st.markdown(f"### 💰 Giá bán: {row.get('Giá bán', 0):.2f} Tỷ")
        if adm: st.error(f"🔑 MÃ CĂN: {row.get('Mã căn')}")
        st.divider()
        t = "🏢 VINHOMES SMART CITY\n"
        t += f"📍 Phân khu: {row.get('Phân khu')}\n"
        t += f"✨ Loại hình: {row.get('Loại hình')}\n"
        t += f"📐 Diện tích: {row.get('Diện tích')} m2\n"
        t += f"💰 Giá: {row.get('Giá bán', 0):.2f} Tỷ\n"
        t += "📞 Liên hệ em xem nhà trực tiếp!"
        st.code(t, language="text")

if sh_obj is not None:
    t1, t2 = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])
    
    with t1:
        f1, f2, f3 = st.columns(3)
        with f1: pk_f = st.multiselect("Lọc Phân khu", PK_L)
        with f2: lh_f = st.multiselect("Lọc Loại hình", LH_L)
        with f3: pr_f = st.slider("Lọc Giá (Tỷ)", 0.0, 15.0, (0.0, 15.0), 0.1)

        df = df_raw.copy()
        if pk_f: df = df[df['Phân khu'].isin(pk_f)]
        if lh_f: df = df[df['Loại hình'].isin(lh_f)]
        df = df[(df['Giá bán'] >= pr_f[0]) & (df['Giá bán'] <= pr_f[1])]

        d_df = df.copy()
        if 'Mã căn' in d_df.columns: d_df = d_df.drop(columns=['Mã căn'])
        
        st.write(f"🔍 Tìm thấy **{len(df)}** căn hộ phù hợp")
        sel = st.dataframe(d_df, use_container_width=True, hide_index=True, 
                          on_select="rerun", selection_mode="single-row")
        if sel and sel.selection.rows:
            show_dt(df.iloc[sel.selection.rows[0]], is_adm)

    with t2:
        if is_adm:
            with st.form("add_f", clear_on_submit=True):
                st.write("### 📝 Nhập thông tin căn mới")
                i1, i2, i3 = st.columns(3)
                with i1:
                    n_y = st.date_input("Ngày lên hàng")
                    n_l = st.selectbox("Loại hình", LH_L)
                    n_p = st.selectbox("Phân
