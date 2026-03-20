import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# --- DANH MỤC DỮ LIỆU (Giữ nguyên 100%) ---
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
        st.error(f"Lỗi kết nối Sheets: {e}")
        return pd.DataFrame(), None

df_raw, sh_obj = load_data()

# --- QUẢN LÝ TRẠNG THÁI ĐĂNG NHẬP ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- HEADER TỐI ƯU ---
h1, h2 = st.columns([7, 3])
with h2:
    s1, s2 = st.columns([5, 1])
    with s1:
        if not st.session_state.logged_in:
            p_in = st.text_input("A", type="password", label_visibility="collapsed", placeholder="Nhập Pass...")
            if p_in == "admin123":
                st.session_state.logged_in = True
                st.rerun()
        else:
            # Làm Admin Mode to hơn và sát nút X
            st.markdown("<div style='text-align:right; padding-top:5px;'><span style='color:#28a745; font-size:18px; font-weight:bold;'>Admin Mode ✅</span></div>", unsafe_allow_html=True)
    with s2:
        if st.session_state.logged_in:
            if st.button("❌", help="Thoát Admin"):
                st.session_state.logged_in = False
                st.rerun()
        else:
            if st.button("🔄"):
                st.cache_resource.clear()
                st.rerun()

is_adm = st.session_state.logged_in

# --- DIALOG CHI TIẾT ---
@st.dialog("📋 Thông tin căn hộ", width="large")
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
        st.divider()
        t = "🏢 VINHOMES SMART CITY\n"
        t += f"📍 Khu: {row.get('Phân khu')}\n✨ Loại: {row.get('Loại hình')}\n"
        t += f"📐 DT: {row.get('Diện tích')} m2\n💰 Giá: {row.get('Giá bán')} Tỷ\n"
        t += "📞 Liên hệ xem nhà ngay!"
        st.code(t)

# --- GIAO DIỆN CHÍNH ---
st.title("🏢 Kho Hàng Vinhomes")
if sh_obj is not None:
    t1, t2 = st.tabs(["📋 Danh sách", "➕ Thêm hàng mới"])
    
    with t1:
        f1, f2, f3 = st.columns(3)
        with f1: pk_f = st.multiselect("Phân khu", PK_L)
        with f2: lh_f = st.multiselect("Loại hình", LH_L)
        with f3: pr_f = st.slider("Giá (Tỷ)", 0.0, 15.0, (0.0, 15.0), 0.1)

        df = df_raw.copy()
        if pk_f: df = df[df['Phân khu'].isin(pk_f)]
        if lh_f: df = df[df['Loại hình'].isin(lh_f)]
        df = df[(df['Giá bán'] >= pr_f[0]) & (df['Giá bán'] <= pr_f[1])]

        d_df = df.copy()
        if 'Mã căn' in d_df.columns: d_df = d_df.drop(columns=['Mã căn'])
        
        st.write(f"🔍 Tìm thấy {len(df)} căn hộ.")
        sel = st.dataframe(d_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
        if sel and sel.selection.rows:
            show_dt(df.iloc[sel.selection.rows[0]], is_adm)

    with t2:
        if is_adm:
            with st.form("form_v5", clear_on_submit=True):
                st.write("### 📝 Thêm căn hộ mới")
                c1, c2, c3 = st.columns(3)
                with c1:
                    v_ngay = st.date_input("Ngày lên hàng")
                    v_loai = st.selectbox("Loại hình", LH_L)
                    v_pk = st.selectbox("Phân khu", PK_L)
                with c2:
                    v_ma = st.text_input("Mã căn (Bảo mật)")
                    v_dt = st.number_input("Diện tích (m2)", 0.0, step=0.1)
                    v_tg = st.selectbox("Khoảng tầng", TG_L)
                with c3:
                    v_nt = st.selectbox("Nội thất", NT_L)
                    v_hbc = st.selectbox("Hướng ban công", H_L)
                    v_gia = st.number_input("Giá bán (Tỷ)", 0.0, step=0.01)
                v_anh = st.text_input("Link ảnh")
                
                if st.form_submit_button("🚀 Xác nhận lưu hàng"):
                    try:
                        headers = [x.strip() for x in sh_obj.row_values(1)]
                        new_row = [""] * len(headers)
                        data_map = {
