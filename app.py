import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# Cau hinh danh sach
PK_L = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
LH_L = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
H_L = ["Dong", "Tay", "Nam", "Bac", "DB", "DN", "TB", "TN"]
NT_L = ["Nguyen ban", "Co ban", "Full do"]

@st.cache_resource
def load_data():
    try:
        c_dict = st.secrets["gcp_service_account"]
        sc = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(c_dict, sc)
        client = gspread.authorize(creds)
        ss = client.open_by_key("19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk")
        sh = ss.get_worksheet(0)
        raw = sh.get_all_values()
        if not raw or len(raw) < 1: return pd.DataFrame(), sh
        df = pd.DataFrame(raw[1:], columns=[str(h).strip() for h in raw[0]])
        if "Giá bán" in df.columns:
            df["Giá bán"] = pd.to_numeric(df["Giá bán"].str.replace(',', '.'), errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except Exception as e:
        st.error(f"Loi: {e}")
        return pd.DataFrame(), None

df_raw, sheet_obj = load_data()

# Thanh Header
h_c1, h_c2 = st.columns([7, 3])
with h_c2:
    pw = st.text_input("Pass", type="password", label_visibility="collapsed", placeholder="Admin password...")
    is_admin = (pw == "admin123")
    b_c1, b_c2 = st.columns(2)
    with b_c1: 
        if is_admin: st.success("ADMIN")
    with b_c2:
        if st.button("Refresh"):
            st.cache_resource.clear()
            st.rerun()

@st.dialog("Chi tiet", width="large")
def show_details(row, adm):
    txt = (f"CĂN HỘ SMART CITY\n- Khu: {row.get('Phân khu')}\n- Loại: {row.get('Loại hình')}\n"
           f"- DT: {row.get('Diện tích')}m2\n- Huong: {row.get('
