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
        for c in [L_TYPE, L1, L2, L3, L8, L12]:
            if c not in df.columns: df[c] = ""
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
            p = st.text_input("P", type="password", label_visibility="collapsed")
            if p == "admin123": st.session_state.is_login = True; st.rerun()
        else: st.write("Admin ✅")
    with s2:
        if st.button("🔄"): st.cache_resource.clear(); st.rerun()

is_adm = st.session_state.is_login

@st.dialog("📋 Chi tiết")
def show_dt(row, adm):
    c1, c2 = st.columns([1.2, 1])
    with c1:
        links = str(row.get(L9, "")).split(',') if row.get(L9) else []
        if links:
            if 'ci' not in st.session_state: st.session_state.ci = 0
            idx = st.session_state.ci % len(links)
            st.image(links[idx], use_container_width=True)
            if len(links) > 1:
                b1, b2 = st.columns(2)
                with b1: 
                    if st.button("⬅️"): st.session_state.ci -= 1; st.rerun()
                with b2:
                    if st.button("➡️"): st.session_state.ci += 1; st.rerun()
        else: st.info("Không ảnh")
    with c2:
        st.subheader(f"{row[L2]} - {row[L1]}")
        st.success(f"💰 {row[L8]}")
        if adm:
            st.divider()
            ck = f"c_{row[L3]}"
            if ck not in st.session_state: st.session_state[ck] = False
            if not st.session_state[ck]:
                if st.button("✅ CHỐT CĂN", use_container_width=True, type="primary"):
                    st.session_state[ck] = True; st.rerun()
            else:
                st.warning("Xác nhận?")
                if st.button("CÓ, CHỐT!", use_container_width=True):
                    try:
                        h = [x.strip() for x in sh_obj.row_values(1)]
                        r_idx = sh_obj.col_values(h.index(L3)+1).index(row[L3])+1
                        sh_obj.update_cell(r_idx, h.index(L12)+1, "Đã bán" if row[L_TYPE]=="Bán" else "Đã thuê")
                        st.session_state[ck] = False; st.cache_resource.clear(); st.rerun()
                    except: st.error("Lỗi Sheets")
        st.divider()
        st.code(f"📍 {row[L1]}\n✨ {row[L2]}\n💰 {row[L8]}")

if sh_obj is not None:
    t1, t2, t3 = st.tabs(["🔴 Bán", "🟢 Thuê", "➕ Thêm"])
    
    def draw(df_in, ks):
        df_a = df_in[~df_in[L12].isin(["Đã bán", "Đã thuê", "Đã cho thuê"])]
        if df_a.empty: 
            st.info("Trống"); return
        c_a, c_b = st.columns(2)
        with c_a: pk = st.multiselect(f"{L1}", PK_L, key=f"p{ks}")
        with c_b: lh = st.multiselect(f"{L2}", LH_L, key=f"l{ks}")
        if pk: df_a = df_a[df_a[L1].isin(pk)]
        if lh: df_a = df_a[df_a[L2].isin(lh)]
        
        show_df = df_a.drop(columns=[L9, L_TYPE, L12, L3] if not is_adm else [L9, L_TYPE, L12], errors='ignore')
        st.write(f"Có {len(df_a)} căn")
        sel = st.dataframe(show_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key=f"d{ks}")
        if sel and sel.selection.rows:
            st.session_state.ci = 0
            show_dt(df_a.iloc[sel.selection.rows[0]], is_adm)

    with t1: draw(df_raw[df_raw[L_TYPE] == "Bán"] if not df_raw.empty else pd.DataFrame(), "b")
    with t2: draw(df_raw[df_raw[L_TYPE] == "Cho thuê"] if not df_raw.empty else pd.DataFrame(), "t")
    with t3:
        if is_adm:
            with st.form("f_add", clear_on_submit=True):
                tp = st.radio("Loại", ["Bán", "Cho thuê"], horizontal=True)
                i1, i2, i3 = st.columns(3)
                with i1: ng = st.date_input("Ngày"); v_lh = st.selectbox(L2, LH_L); v_pk = st.selectbox(L1, PK_L)
                with i2: v_ma = st.text_input(L3); v_dt = st.number_input(L4, 0.0); v_tg = st.selectbox(L5, TG_L)
                with i3: v_nt = st.selectbox(L6, NT_L); v_hb = st.selectbox(L7, H_L); v_gi = st.text_input(L8)
                v_ht = st.selectbox(L10, HT_L); v_gc = st.text_input(L11)
                up = st.file_uploader("Ảnh", accept_multiple_files=True)
                if st.form_submit_button("Lưu"):
                    imgs = upload_multiple_imgs(up)
                    try:
                        h = [x.strip() for x in sh_obj.row_values(1)]
                        new = [""] * len(h)
                        dm = {L_TYPE:tp, "Ngày lên hàng":str(ng), L2:v_lh, L1:v_pk, L3:v_ma, L4:v_dt, L5:v_tg, L6:v_nt, L7:v_hb, L8:v_gi, L9:imgs, L10:v_ht, L11:v_gc, L12:"Đang bán"}
                        for idx, col in enumerate(h):
                            if col in dm: new[idx] = dm[col]
                        sh_obj.append_row(new)
                        st.success("Xong!"); st.cache_resource.clear(); st.rerun()
                    except: st.error("Lỗi lưu")
        else: st.warning("Đăng nhập Admin")
