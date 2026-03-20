import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# 1. CẤU HÌNH
st.set_page_config(page_title="Vinhomes Smart City Manager", layout="wide")

@st.cache_resource
def get_data():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key("19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk")
        sheet = spreadsheet.get_worksheet(0)
        raw = sheet.get_all_values()
        if not raw or len(raw) < 1: return pd.DataFrame(), sheet
        headers = [str(h).strip() for h in raw[0]]
        df = pd.DataFrame(raw[1:], columns=headers)
        if "Giá bán" in df.columns:
            df["Giá bán"] = pd.to_numeric(df["Giá bán"], errors='coerce').fillna(0)
        # Mới nhất lên đầu
        df = df.iloc[::-1].reset_index(drop=True)
        return df, sheet
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame(), None

df_raw, sheet_obj = get_data()

# 2. SIDEBAR
with st.sidebar:
    st.header("🔑 Phân quyền")
    pw = st.text_input("Mật khẩu Admin", type="password")
    is_admin = (pw == "admin123")
    st.info("✅ ADMIN" if is_admin else "💡 CTV")
    if st.button("🔄 Cập nhật danh sách"):
        st.cache_resource.clear()
        st.rerun()

# 3. GIAO DIỆN
st.title("🏢 Kho Hàng Vinhomes Smart City")

if sheet_obj is not None:
    t1, t2 = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])

    with t1:
        c1, c2, c3 = st.columns(3)
        with c1: pk_f = st.multiselect("Lọc Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
        with c2: lh_f = st.multiselect("Lọc Loại hình", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
        with c3: price_f = st.slider("Giá (Tỷ)", 0.0, 10.0, (0.0, 10.0), step=0.001, format="%.3f")

        if not df_raw.empty:
            df = df_raw.copy()
            if pk_f: df = df[df['Phân khu'].isin(pk_f)]
