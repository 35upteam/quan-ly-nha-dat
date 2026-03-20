import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests, base64, time

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# --- NHÃN CỘT ---
L_DATE, L_LH, L_PK, L_MA = "Ngày lên hàng", "Loại hình", "Phân khu", "Mã căn"
L_DT, L_TANG, L_NT, L_HBC = "Diện tích", "Khoảng tầng", "Nội thất", "Hướng BC"
L_GIA, L_HT, L_TT, L_IMG = "Giá bán", "Hiện trạng", "Trạng thái", "Link ảnh"
L_TYPE, L_GC = "Phân loại", "Ghi chú"
V_SOLD, V_RENT = "Đã bán", "Đã thuê"

# --- HÀM XỬ LÝ CHUYỂN ẢNH (CALLBACK) ---
def change_img(step, total):
    st.session_state.ci = (st.session_state.get('ci', 0) + step) % total

@st.cache_resource
def load_data():
    try:
        s = st.secrets["gcp_service_account"]
        sc = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        c = ServiceAccountCredentials.from_json_keyfile_dict(s, sc); g = gspread.authorize(c)
        ss = g.open_by_key("19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk")
        sh = ss.get_worksheet(0); r = sh.get_all_values()
        if not r: return pd.DataFrame(), None
        h = [x.strip() for x in r[0]]; df = pd.DataFrame(r[1:], columns=h)
        df['sheet_row'] = range(2, len(df) + 2)
        df[L_GIA] = pd.to_numeric(df[L_GIA], errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except: return pd.DataFrame(), None

df_raw, sh_obj = load_data()
if 'is_login' not in st.session_state: st.session_state.is_login = False
is_adm = st.session_state.is_login

# --- DIALOG CHI TIẾT ---
@st.dialog("Chi tiết căn hộ")
def show_dt(row, ks):
    mid = str(row.get(L_MA, "0"))
    cl1, cl2 = st.columns([1.2, 1])
    with cl1:
        imgs = str(row.get(L_IMG, "")).split(',') if row.get(L_IMG) else []
        if imgs and imgs[0]:
            if 'ci' not in st.session_state: st.session_state.ci = 0
            total = len(imgs)
            ix = st.session_state.ci % total
            st.image(imgs[ix], use_container_width=True, caption=f"Ảnh {ix+1}/{total}")
            
            if total > 1:
                b1, b2 = st.columns(2)
                with b1:
                    st.button("⬅️ Trước", key=f"p_{mid}", on_click=change_img, args=(-1, total))
                with b2:
                    st.button("Sau ➡️", key=f"n_{mid}", on_click=change_img, args=(1, total))
        else: st.info("Không có ảnh")
    with cl2:
        st.subheader(f"{row[L_LH]} - {row[L_PK]}")
        st.success(f"💰 Giá: {row[L_GIA]} Tỷ")
        st.write(f"📐 **Diện tích:** {row[L_DT]}m²")
        st.write(f"🧭 **Hướng BC:** {row[L_HBC]}")
        st.write(f"🧱 **Tầng:** {row[L_TANG]} | **Nội thất:** {row[L_NT]}")
        st.write(f"🚧 **Hiện trạng:** {row[L_HT]}")
        if row.get(L_GC): st.info(f"Ghi chú: {row[L_GC]}")
        
        if is_adm:
            st.divider(); ck = f"ck_{mid}"
            if not st.session_state.get(ck, False):
                if st.button("✅ ĐÃ CHỐT", use_container_width=True, type="primary", key=f"bt_{mid}"):
                    st.session_state[ck] = True; st.rerun()
            else:
                st.warning("Xác nhận chốt?"); cy, cn = st.columns(2)
                with cy:
                    if st.button("OK", type="primary", use_container_width=True, key=f"ok_{mid}"):
                        c_idx = list(df_raw.columns).index(L
