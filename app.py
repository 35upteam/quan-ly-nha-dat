import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# --- ĐỊNH NGHĨA BIẾN SIÊU NGẮN (Để không bị ngắt dòng) ---
T_PK = "Phân khu"
T_LH = "Loại hình"
T_MC = "Mã căn"
T_DT = "Diện tích"
T_HBC = "Hướng BC"
T_GB = "Giá bán"
T_NT = "Nội thất"
T_KT = "Khoảng tầng"
T_LA = "Link ảnh"

PK_L = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
LH_L = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
H_L = ["Đông", "Tây", "Nam", "Bắc", "ĐB", "ĐN", "TB", "TN"]
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
        if T_GB in df.columns:
            df[T_GB] = pd.to_numeric(df[T_GB].str.replace(',', '.'), errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame(), None

df_raw, sh_obj = load_data()

# --- HEADER ---
h1, h2 = st.columns([7.5, 2.5])
with h2:
    s1, s2 = st.columns([4, 1])
    with s1:
        p_in = st.text_input("A", type="password", label_visibility="collapsed", placeholder="Pass...")
        is_adm = (p_in == "admin123")
    with s2:
        if st.button("🔄"):
            st.cache_resource.clear()
            st.rerun()
    if is_adm:
        st.markdown("<p style='text-align:right;color:green;font-size:12px;'>Admin OK ✅</p>", unsafe_allow_html=True)

# --- DIALOG ---
@st.dialog("📋 Chi tiết")
def show_dt(row, adm):
    c_i, c_t = st.columns(2)
    with c_i:
        if row.get(T_LA): st.image(row[T_LA], use_container_width=True)
        else: st.info("No image")
    with c_t:
        st.subheader(f"{row.get(T_LH)} - {row.get(T_PK)}")
        st.write(f"📐 {row.get(T_DT)} m2 | 🧭 {row.get(T_HBC)}")
        st.markdown(f"### 💰 {row.get(T_GB, 0):.2f} Tỷ")
        if adm: st.error(f"🔑 {T_MC}: {row.get(T_MC)}")
        st.divider()
        t = f"🏢 VINHOMES\n📍 Khu: {row.get(T_PK)}\n✨ Loại: {row.get(T_LH)}\n💰 Giá: {row.get(T_GB)} Tỷ"
        st.code(t)

st.title("🏢 Kho Hàng Vinhomes")

if sh_obj is not None:
    t1, t2 = st.tabs(["📋 Danh sách", "➕ Thêm mới"])
    with t1:
        f1, f2, f3 = st.columns(3)
        with f1: pk_f = st.multiselect(T_PK, PK_L)
        with f2: lh_f = st.multiselect(T_LH, LH_L)
        with f3: pr_f = st.slider(T_GB, 0.0, 15.0, (0.0, 15.0))

        df = df_raw.copy()
        if pk_f: df = df[df[T_PK].isin(pk_f)]
        if lh_f: df = df[df[T_LH].isin(lh_f)]
        df = df[(df[T_GB] >= pr_f[0]) & (df[T_GB] <= pr_f[1])]

        d_df = df.drop(columns=[T_MC]) if T_MC in df.columns else df
        st.write(f"Tìm thấy: {len(df)}")
        sel = st.dataframe(d_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
        if sel and sel.selection.rows:
            show_dt(df.iloc[sel.selection.rows[0]], is_adm)

    with t2:
        if is_adm:
            with st.form("a_f", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                with c1:
                    n_y = st.date_input("Ngày")
                    n_l = st.selectbox(T_LH, LH_L)
                with c2:
                    n_p = st.selectbox(T_PK, PK_L)
                    n_m = st.text_input(T_MC)
                with c3:
                    n_s = st.number_input(T_DT, 0.0)
                    n_g = st.number_input(T_GB, 0.0)
                n_a = st.text_input(T_LA)
                if st.form_submit_button("🚀 Lưu"):
                    try:
                        h = [x.strip() for x in sh_obj.row_values(1)]
                        r = [""] * len(h)
                        m = {"Ngày lên hàng":str(n_y), T_LH:n_l, T_PK:n_p, T_MC:n_m, T_DT:n_s, T_GB:n_g, T_LA:n_a}
                        for i, x in enumerate(h):
                            if x in m: r[i] = m[x]
                        sh_obj.append_row(r)
                        st.success("OK!")
                        st.cache_resource.clear()
                    except Exception as e: st.error(e)
        else: st.warning("Nhập Pass Admin để thêm hàng")
