import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests
import base64

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# --- DANH MỤC NHÃN ---
L_TYPE, L1, L2, L3 = "Phân loại", "Phân khu", "Loại hình", "Mã căn"
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
            res = requests.post("https://api.imgbb.com/1/upload", {"key": api_key, "image": img_64}, timeout=20)
            if res.status_code == 200: urls.append(res.json()['data']['thumb']['url']) 
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
        for c_name in [L_TYPE, L1, L2, L3, L8, L12]:
            if c_name not in df.columns: df[c_name] = ""
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
            if p == "admin123": st.session_state.is_login = True; st.rerun()
        else: st.write("Admin ✅")
    with s2:
        if st.button("🔄"): st.cache_resource.clear(); st.rerun()

is_adm = st.session_state.is_login

if sh_obj is not None:
    t1, t2, t3 = st.tabs(["🔴 Chuyển nhượng", "🟢 Cho thuê", "➕ Thêm hàng"])
    
    def draw(df_in, ks):
        # Lọc bỏ các căn đã chốt
        df_a = df_in[~df_in[L12].astype(str).str.contains("Đã", na=False)]
        if df_a.empty: 
            st.info("Hiện không có căn nào."); return
        
        ca, cb = st.columns(2)
        with ca: pk = st.multiselect(f"Phân khu ({ks})", PK_L, key=f"p{ks}")
        with cb: lh = st.multiselect(f"Loại hình ({ks})", LH_L, key=f"l{ks}")
        if pk: df_a = df_a[df_a[L1].isin(pk)]
        if lh: df_a = df_a[df_a[L2].isin(lh)]
        
        show_cols = df_a.drop(columns=[L9, L_TYPE, L12, L3] if not is_adm else [L9, L_TYPE, L12], errors='ignore')
        st.write(f"Tìm thấy {len(df_a)} căn")
        sel = st.dataframe(show_cols, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key=f"d{ks}")

        # Định nghĩa Dialog bên trong hàm draw để tránh lỗi Duplicate ID
        @st.dialog(f"Chi tiết căn {ks.upper()}")
        def show_dt(row):
            c1, c2 = st.columns([1.2, 1])
            with c1:
                links = str(row.get(L9, "")).split(',') if row.get(L9) else []
                if links and links[0]:
                    if 'ci' not in st.session_state: st.session_state.ci = 0
                    idx = st.session_state.ci % len(links)
                    st.image(links[idx], use_container_width=True)
                    if len(links) > 1:
                        b1, b2 = st.columns(2)
                        with b1: 
                            if st.button("⬅️", key=f"prev{ks}"): st.session_state.ci -= 1; st.rerun()
                        with b2:
                            if st.button("➡️", key=f"next{ks}"): st.session_state.ci += 1; st.rerun()
                else: st.info("Không có ảnh")
            with c2:
                st.subheader(f"{row[L2]} - {row[L1]}")
                st.success(f"💰 Giá: {row[L8]}")
                if is_adm:
                    st.divider()
                    ck = f"confirm_{row[L3]}"
                    if ck not in st.session_state: st.session_state[ck] = False
                    
                    if not st.session_state[ck]:
                        if st.button("✅ ĐÃ CHỐT C
