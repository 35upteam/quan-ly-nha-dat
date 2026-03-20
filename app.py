import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Vinhomes Smart City Manager", layout="wide", page_icon="🏢")

# 2. KẾT NỐI VÀ TẢI DỮ LIỆU
@st.cache_resource
def get_data():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open_by_key("19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk")
        sheet = spreadsheet.get_worksheet(0)
        
        raw_values = sheet.get_all_values()
        if not raw_values or len(raw_values) < 1:
            return pd.DataFrame(), sheet
            
        headers = [str(h).strip() for h in raw_values[0]]
        data = raw_values[1:]
        
        df = pd.DataFrame(data, columns=headers)
        
        if "Giá bán" in df.columns:
            df["Giá bán"] = pd.to_numeric(df["Giá bán"], errors='coerce').fillna(0)
        
        # SẮP XẾP: Mới nhất lên đầu
        df = df.iloc[::-1].reset_index(drop=True)
                
        return df, sheet
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return pd.DataFrame(), None

df_raw, sheet_obj = get_data()

# 3. THANH BÊN (SIDEBAR)
with st.sidebar:
    st.header("🔑 Phân quyền")
    pw = st.text_input("Mật khẩu Admin", type="password")
    is_admin = (pw == "admin123")
    st.info("✅ ADMIN" if is_admin else "💡 CTV")
    st.divider()
    if st.button("🔄 Cập nhật danh sách"):
        st.cache_resource.clear()
        st.rerun()

# 4. GIAO DIỆN CHÍNH
st.title("🏢 Kho Hàng Vinhomes Smart City")

if sheet_obj is None:
    st.error("Không thể kết nối Google Sheet.")
else:
    tab1, tab2 = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])

    # --- TAB 1: DANH SÁCH ---
    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1:
            pk_list = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
            pk_f = st.multiselect("Lọc Phân khu", options=pk_list)
        with c2:
            lh_list = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
            lh_f = st.multiselect("Lọc Loại hình", options=lh_list)
        with c3:
            # Mặc định 0 - 10 tỷ
            price_f = st.slider("Khoảng giá (Tỷ)", 0.0, 10.0, (0.0, 10.0), step=0.001, format="%.3f")

        if df_raw.empty:
            st.warning("Chưa có dữ liệu.")
        else:
            df = df_raw.copy()
            if pk_f: df = df[df['Phân khu'].isin(pk_f)]
            if lh_f: df = df[df['Loại hình'].isin(lh_f)]
            if 'Giá bán' in df.columns:
                df = df[(df['Giá bán'] >= price_f[0]) & (df['Giá bán'] <= price_f[1])]

            view_df = df.copy()
            if not is_admin and 'Mã căn' in view_df.columns:
                view_df = view_df.drop(columns=['Mã căn'])

            st.write(f"🔍 Tìm thấy **{len(view_df)}** căn hộ (Mới nhất ở trên)")
            sel = st.dataframe(view_df, use_container_width=True, hide_index=True, on_select="
