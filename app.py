import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests
import base64

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# --- DANH MỤC NHÃN ---
L_TYPE = "Phân loại" 
L1, L2, L3 = "Phân khu", "Loại hình", "Mã căn"
L4, L5, L6 = "Diện tích", "Khoảng tầng", "Nội thất"
L7, L8, L9 = "Hướng BC", "Giá bán", "Link ảnh"
L10, L11, L12 = "Hiện trạng", "Ghi chú", "Trạng thái"

PK_L = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
LH_L = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
H_L = ["Đông", "Tây", "Nam", "Bắc", "ĐB", "ĐN", "TB", "TN"]
NT_L = ["Nguyên bản", "Cơ bản", "Full đồ"]
TG_L = ["Thấp", "Trung", "Cao"]
HT_L = ["Đang ở", "Đang cho thuê", "Để trống"]

def upload_multiple_imgs(files):
    if not files: return ""
    try:
        api_key = st.secrets.get("imgbb_api_key") or st.secrets.get("gcp_service_account", {}).get("imgbb_api_key")
        if not api_key: return ""
        urls = []
        for f in files:
            f.seek(0)
            img_64 = base64.b64encode(f.read()).decode('utf-8')
            payload = {"key": api_key, "image": img_64}
            res = requests.post("https://api.imgbb.com/1/upload", payload, timeout=20)
            if res.status_code == 200:
                urls.append(res.json()['data']['thumb']['url']) 
        return ",".join(urls)
    except: return ""

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
        if L12 not in df.columns: df[L12] = "Đang bán"
        return df.iloc[::-1].reset_index(drop=True), sh
    except: return pd.DataFrame(), None

df_raw, sh_obj = load_data()

if 'is_login' not in st.session_state: st.session_state.is_login = False

# --- HEADER ---
h1, h2 = st.columns([7, 3])
with h1: st.title("🏢 Vinhomes Manager")
with h2:
    s1, s2 = st.columns([5, 1])
    with s1:
        if not st.session_state.is_login:
            p = st.text_input("P", type="password", label_visibility="collapsed", placeholder="Pass...")
            if p == "admin123":
                st.session_state.is_login = True
                st.rerun()
        else:
            st.markdown("<div style='text-align:right;padding-top:10px;'><span style='color:#28a745;font-weight:bold;'>Admin Mode ✅</span></div>", unsafe_allow_html=True)
    with s2:
        if st.session_state.is_login:
            if st.button("❌"): st.session_state.is_login = False; st.rerun()
        else:
            if st.button("🔄"): st.cache_resource.clear(); st.rerun()

is_adm = st.session_state.is_login

# --- HÀM CẬP NHẬT TRẠNG THÁI ---
def update_status(row_data):
    try:
        headers = [h.strip() for h in sh_obj.row_values(1)]
        col_idx = headers.index(L12) + 1
        all_ma_can = sh_obj.col_values(headers.index(L3) + 1)
        row_idx = all_ma_can.index(row_data[L3]) + 1
        new_st = "Đã bán" if row_data[L_TYPE] == "Bán" else "Đã cho thuê"
        sh_obj.update_cell(row_idx, col_idx, new_st)
        st.success(f"🎉 Đã chốt căn {row_data[L3]}!")
        st.cache_resource.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Lỗi khi cập nhật: {e}")

# --- CỬA SỔ CHI TIẾT ---
@st.dialog("📋 Chi tiết")
def show_dt(row, adm):
    c1, c2 = st.columns([1.2, 1])
    with c1:
        raw_links = row.get(L9, "")
        if raw_links:
            img_list = raw_links.split(',')
            if len(img_list) > 1:
                if 'curr_img' not in st.session_state: st.session_state.curr_img = 0
                idx = st.session_state.curr_img % len(img_list)
                st.image(img_list[idx], use_container_width=True)
                b1, b
