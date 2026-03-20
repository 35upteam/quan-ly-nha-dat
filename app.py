import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# 1. CẤU HÌNH & KẾT NỐI
st.set_page_config(page_title="Vinhomes Smart City Manager", layout="wide")

@st.cache_resource
def get_data():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        ss = client.open_by_key("19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk")
        sheet = ss.get_worksheet(0)
        raw = sheet.get_all_values()
        if not raw or len(raw) < 1: return pd.DataFrame(), sheet
        headers = [str(h).strip() for h in raw[0]]
        df = pd.DataFrame(raw[1:], columns=headers)
        if "Giá bán" in df.columns:
            df["Giá bán"] = pd.to_numeric(df["Giá bán"], errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sheet
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame(), None

df_raw, sheet_obj = get_data()

# 2. THANH BÊN
with st.sidebar:
    st.header("🔑 Phân quyền")
    pw = st.text_input("Mật khẩu Admin", type="password")
    is_admin = (pw == "admin123")
    st.info("✅ ADMIN" if is_admin else "💡 CTV")
    if st.button("🔄 Cập nhật danh sách"):
        st.cache_resource.clear()
        st.rerun()

# 3. GIAO DIỆN CHÍNH
st.title("🏢 Kho Hàng Vinhomes Smart City")

if sheet_obj is not None:
    t1, t2 = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])

    with t1:
        c1, c2, c3 = st.columns(3)
        with c1: pk_f = st.multiselect("Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
        with c2: lh_f = st.multiselect("Loại hình", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
        with c3: pr_f = st.slider("Giá (Tỷ)", 0.0, 10.0, (0.0, 10.0), step=0.001, format="%.3f")

        df = df_raw.copy()
        if pk_f: df = df[df['Phân khu'].isin(pk_f)]
        if lh_f: df = df[df['Loại hình'].isin(lh_f)]
        if 'Giá bán' in df.columns:
            df = df[(df['Giá bán'] >= pr_f[0]) & (df['Giá bán'] <= pr_f[1])]

        v_df = df.copy()
        if not is_admin and 'Mã căn' in v_df.columns: v_df = v_df.drop(columns=['Mã căn'])

        st.write(f"🔍 Tìm thấy **{len(v_df)}** căn (Mới nhất ở trên)")
        sel = st.dataframe(v_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
