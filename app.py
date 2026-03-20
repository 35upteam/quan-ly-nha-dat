import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(page_title="Vinhomes", layout="wide")

# Config lists
PK_L = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
LH_L = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
H_L = ["Dong", "Tay", "Nam", "Bac", "DB", "DN", "TB", "TN"]
NT_L = ["Nguyen ban", "Co ban", "Full do"]

@st.cache_resource
def load_data():
    try:
        c_dict = st.secrets["gcp_service_account"]
        sc = ["https://spreadsheets.google.com/feeds", 
              "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(c_dict, sc)
        client = gspread.authorize(creds)
        ss = client.open_by_key("19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk")
        sh = ss.get_worksheet(0)
        raw = sh.get_all_values()
        if not raw or len(raw) < 1: return pd.DataFrame(), sh
        cols = [str(h).strip() for h in raw[0]]
        df = pd.DataFrame(raw[1:], columns=cols)
        if "Giá bán" in df.columns:
            df["Giá bán"] = pd.to_numeric(
                df["Giá bán"].str.replace(',', '.'), 
                errors='coerce'
            ).fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except Exception as e:
        st.error(f"Loi: {e}")
        return pd.DataFrame(), None

df_raw, sheet_obj = load_data()

# Header
h_c1, h_c2 = st.columns([7, 3])
with h_c2:
    pw = st.text_input("Pass", type="password", 
                      label_visibility="collapsed", 
                      placeholder="Admin pass...")
    is_admin = (pw == "admin123")
    b_c1, b_c2 = st.columns(2)
    if is_admin: 
        with b_c1: st.success("ADMIN")
    with b_c2:
        if st.button("Refresh"):
            st.cache_resource.clear()
            st.rerun()

@st.dialog("Chi tiet", width="large")
def show_details(row, adm):
    # Noi dung copy (tach dong de chong loi syntax)
    line1 = "CĂN HỘ SMART CITY\n"
    line2 = f"- Khu: {row.get('Phân khu')}\n"
    line3 = f"- Loai: {row.get('Loại hình')}\n"
    line4 = f"- DT: {row.get('Diện tích')}m2\n"
    line5 = f"- Huong: {row.get('Hướng BC')}\n"
    line6 = f"- Gia: {row.get('Giá bán', 0):.2f} Ty\n"
    line7 = "LH xem nha ngay!"
    txt = line1 + line2 + line3 + line4 + line5 + line6 + line7
    
    im_c, if_c = st.columns([1, 1])
    with im_c:
        if row.get('Link ảnh'): 
            st.image(row['Link ảnh'], use_container_width=True)
        else: st.info("Chua co anh")
    with if_c:
        st.subheader(f"{row.get('Loại hình')} - {row.get('Phân khu')}")
        st.write(f"DT: {row.get('Diện tích')}m2")
        st.markdown(f"### Gia: {row.get('Giá bán', 0):.2f} Ty")
        if adm: st.error(f"MA CAN: {row.get('Mã căn')}")
        st.divider()
        st.code(txt, language="text")

st.title("Kho Hang Vinhomes")
if sheet_obj is not None:
    t1, t2 = st.tabs(["Danh sach", "Them hang"])
    
    with t1:
        f1, f2, f3 = st.columns(3)
        with f1: pk_f = st.multiselect("Phan khu", PK_L)
        with f2: lh_f = st.multiselect("Loai hinh", LH_L)
        with f3: pr_f = st.slider("Gia (Ty)", 0.0, 15.0, (0.0, 15.0), 0.1)

        df = df_raw.copy()
        if pk_f: df = df[df['Phân khu'].isin(pk_f)]
        if lh_f: df = df[df['Loại hình'].isin(lh_f)]
        df = df[(df['Giá bán'] >= pr_f[0]) & (df['Giá bán'] <= pr_f[1])]

        d_df = df.drop(columns=['Mã căn']) if 'Mã căn' in df.columns else df
        st.info(f"Tim thay {len(df)} can")
        sel = st.dataframe(d_df, use_container_width=True, 
                          hide_index=True, on_select="rerun", 
                          selection_mode="single-row")
        if sel and sel.selection.rows:
            show_details(df.
