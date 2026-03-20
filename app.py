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
L10, L11 = "Hiện trạng", "Ghi chú"

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

# --- CỬA SỔ CHI TIẾT (SỬA LỖI DUPLICATE ID) ---
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
                b1, b2, b3 = st.columns([1, 2, 1])
                with b1:
                    if st.button("⬅️"): st.session_state.curr_img -= 1; st.rerun()
                with b2: st.write(f"Ảnh {idx + 1}/{len(img_list)}")
                with b3:
                    if st.button("➡️"): st.session_state.curr_img += 1; st.rerun()
            else: st.image(img_list[0], use_container_width=True)
        else: st.info("Chưa có ảnh")
    with c2:
        st.subheader(f"{row.get(L2)} - {row.get(L1)}")
        st.success(f"💰 Giá: {row.get(L8)}")
        st.info(f"📍 Hiện trạng: {row.get(L10, 'N/A')}")
        if row.get(L11): st.write(f"📝 {row[L11]}")
        if adm: st.error(f"🔑 {L3}: {row.get(L3)}")
        st.divider()
        st.code(f"🏢 VINHOMES\n📍 {row.get(L1)}\n✨ {row.get(L2)}\n💰 {row.get(L8)}\n🏠 {row.get(L10)}")

# --- GIAO DIỆN CHÍNH ---
if sh_obj is not None:
    t_ban, t_thue, t_add = st.tabs(["🔴 Chuyển nhượng", "🟢 Cho thuê", "➕ Thêm hàng"])
    
    def draw_list(df_filter, key_s):
        if df_filter.empty:
            st.info("Hiện chưa có căn nào.")
            return

        f1, f2 = st.columns(2)
        with f1: pk = st.multiselect(f"{L1}", PK_L, key=f"pk_{key_s}")
        with f2: lh = st.multiselect(f"{L2}", LH_L, key=f"lh_{key_s}")
        
        if pk: df_filter = df_filter[df_filter[L1].isin(pk)]
        if lh: df_filter = df_filter[df_filter[L2].isin(lh)]
        
        cols_drop = [L9, L_TYPE]
        if not is_adm: cols_drop.append(L3)
        display_df = df_filter.drop(columns=[c for c in cols_drop if c in df_filter.columns], errors='ignore')
        
        st.write(f"Tìm thấy {len(df_filter)} căn")
        sel = st.dataframe(display_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key=f"df_{key_s}")
        
        if sel and sel.selection.rows:
            st.session_state.curr_img = 0
            show_dt(df_filter.iloc[sel.selection.rows[0]], is_adm)

    with t_ban:
        df_b = df_raw[df_raw[L_TYPE] == "Bán"] if (not df_raw.empty and L_TYPE in df_raw.columns) else df_raw
        draw_list(df_b, "ban")

    with t_thue:
        df_t = df_raw[df_raw[L_TYPE] == "Cho thuê"] if (not df_raw.empty and L_TYPE in df_raw.columns) else pd.DataFrame()
        draw_list(df_t, "thue")

    with t_add:
        if is_adm:
            with st.form("form_v18_3", clear_on_submit=True):
                v_type = st.radio("Loại hình:", ["Bán", "Cho thuê"], horizontal=True)
                i1, i2, i3 = st.columns(3)
                with i1:
                    v_ng = st.date_input("Ngày"); v_lh = st.selectbox(L2, LH_L); v_pk = st.selectbox(L1, PK_L)
                with i2:
                    v_ma = st.text_input(L3); v_dt = st.number_input(L4, 0.0); v_tg = st.selectbox(L5, TG_L)
                with i3:
                    v_nt = st.selectbox(L6, NT_L); v_hb = st.selectbox(L7, H_L); v_gi = st.text_input(L8)
                
                c1, c2 = st.columns([1, 2])
                with c1: v_ht = st.selectbox(L10, HT_L)
                with c2: v_gc = st.text_input(L11)
                
                f_up = st.file_uploader("📸 Ảnh", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
                
                if st.form_submit_button("🚀 Lưu"):
                    imgs = upload_multiple_imgs(f_up) if f_up else ""
                    try:
                        cols = [c.strip() for c in sh_obj.row_values(1)]
                        new_row = [""] * len(cols)
                        data_m = {L_TYPE: v_type, "Ngày lên hàng": str(v_ng), L2: v_lh, L1: v_pk, L3: v_ma, L4: v_dt, L5: v_tg, L6: v_nt, L7: v_hb, L8: v_gi, L9: imgs, L10: v_ht, L11: v_gc, "Trạng thái": "Đang bán"}
                        for idx, col in enumerate(cols):
                            if col in data_m: new_row[idx] = data_m[col]
                        sh_obj.append_row(new_row)
                        st.success("✅ Đã lưu!"); st.cache_resource.clear(); st.rerun()
                    except Exception as e: st.error(f"Lỗi: {e}")
        else: st.warning("Cần Pass Admin")
