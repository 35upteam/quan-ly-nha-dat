import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(page_title="Vinhomes", layout="wide")

# Constants
PK_L = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
LH_L = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
H_L = ["Dong", "Tay", "Nam", "Bac", "DB", "DN", "TB", "TN"]
NT_L = ["Nguyen ban", "Co ban", "Full do"]

@st.cache_resource
def load_data():
    try:
        s = st.secrets["gcp_service_account"]
        u = "https://spreadsheets.google.com/feeds"
        v = "https://www.googleapis.com/auth/drive"
        c = ServiceAccountCredentials.from_json_keyfile_dict(s, [u, v])
        g = gspread.authorize(c)
        k = "19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk"
        ss = g.open_by_key(k)
        sh = ss.get_worksheet(0)
        r = sh.get_all_values()
        if not r or len(r) < 1: return pd.DataFrame(), sh
        df = pd.DataFrame(r[1:], columns=[h.strip() for h in r[0]])
        if "Giá bán" in df.columns:
            df["Giá bán"] = df["Giá bán"].str.replace(',', '.')
            df["Giá bán"] = pd.to_numeric(df["Giá bán"], errors='coerce')
            df["Giá bán"] = df["Giá bán"].fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except Exception as e:
        st.error(f"Loi: {e}")
        return pd.DataFrame(), None

df_raw, sh_obj = load_data()

# Login Header
c1, c2 = st.columns([7, 3])
with c2:
    p_in = st.text_input("P", type="password", label_visibility="collapsed")
    is_adm = (p_in == "admin123")
    if st.button("Refresh"):
        st.cache_resource.clear()
        st.rerun()

@st.dialog("Chi tiet")
def show_dt(row, adm):
    c_i, c_t = st.columns(2)
    with c_i:
        if row.get('Link ảnh'): st.image(row['Link ảnh'])
        else: st.write("No image")
    with c_t:
        st.write(f"Khu: {row.get('Phân khu')}")
        st.write(f"Gia: {row.get('Giá bán')} Ty")
        if adm: st.error(f"MA: {row.get('Mã căn')}")
        st.divider()
        # Copy text safety
        t = f"Khu: {row.get('Phân khu')}\n"
        t += f"Loai: {row.get('Loại hình')}\n"
        t += f"Gia: {row.get('Giá bán')} Ty"
        st.code(t)

st.title("Kho Hang")
if sh_obj is not None:
    t_n = ["Danh sach", "Them"]
    t1, t2 = st.tabs(t_n)
    
    with t1:
        col1, col2, col3 = st.columns(3)
        with col1: f_p = st.multiselect("PK", PK_L)
        with col2: f_l = st.multiselect("LH", LH_L)
        with col3: f_g = st.slider("G", 0.0, 15.0, (0.0, 15.0))

        df = df_raw.copy
