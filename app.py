import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests
import base64

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# --- DANH MỤC NHÃN (L1-L9 cũ, thêm L10-L11 mới) ---
L1, L2, L3 = "Phân khu", "Loại hình", "Mã căn"
L4, L5, L6 = "Diện tích", "Khoảng tầng", "Nội thất"
L7, L8, L9 = "Hướng BC", "Giá bán", "Link ảnh"
L10, L11 = "Hiện trạng", "Ghi chú" # Các trường mới thêm

PK_L = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
LH_L = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
H_L = ["Đông", "Tây", "Nam", "Bắc", "ĐB", "ĐN", "TB", "TN"]
NT_L = ["Nguyên bản", "Cơ bản", "Full đồ"]
TG_L = ["Thấp", "Trung", "Cao"]
HT_L = ["Đang ở", "Đang cho thuê", "Để trống"] # Danh mục cho hiện trạng

def upload_img(f):
    try:
        api_key = None
        if "imgbb_api_key" in st.secrets:
            api_key = st.secrets["imgbb_api_key"]
        elif "gcp_service_account" in st.secrets and "imgbb_api_key" in st.secrets["gcp_service_account"]:
            api_key = st.secrets["gcp_service_account"]["imgbb_api_key"]
            
        if not api_key:
            st.error("Lỗi: Không tìm thấy API Key!")
            return ""
        
        f.seek(0)
        img_64 = base64.b64encode(f.read()).decode('utf-8')
        payload = {"key": api_key, "image": img_64}
        res = requests.post("https://api.imgbb.com/1/upload", payload, timeout=15)
        return res.json()['data']['url'] if res.status_code == 200 else ""
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
        if not r: return pd.DataFrame(), sh
        df = pd.DataFrame(r[1:], columns=[h.strip() for h in r[0]])
        if L8 in df.columns:
            df[L8] = pd.to_numeric(df[L8].str.replace(',', '.'), errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except: return pd.DataFrame(), None

df_raw, sh_obj = load_data()

if 'is_login' not in st.session_state: st.session_state.is_login = False

# --- HEADER ---
h1, h2 = st.columns([7, 3])
with h2:
    s1, s2 = st.columns([5, 1])
    with s1:
        if not st.session_state.is_login:
            p = st.text_input("A", type="password", label_visibility="collapsed", placeholder="Pass...")
            if p == "admin123":
                st.session_state.is_login = True
                st.rerun()
    with s2:
        if st.session_state.is_login and st.button("❌"):
            st.session_state.is_login = False
            st.rerun()
        elif not st.session_state.is_login and st.button("🔄"):
            st.cache_resource.clear()
            st.rerun()

is_adm = st.session_state.is_login

@st.dialog("📋 Chi tiết")
def show_dt(row, adm):
    c1, c2 = st.columns(2)
    with c1:
        if row.get(L9): st.image(row[L9], use_container_width=True)
        else: st.info("Chưa có ảnh thực tế")
    with c2:
        st.subheader(f"{row.get(L2)} - {row.get(L1)}")
        st.write(f"📐 {row.get(L4)}m2 | 🧭 {row.get(L7)}")
        st.markdown(f"### 💰 {row.get(L8, 0):.2f} Tỷ")
        st.info(f"📍 Hiện trạng: {row.get(L10, 'N/A')}")
        if row.get(L11): st.write(f"📝 Ghi chú: {row[L11]}")
        if adm: st.error(f"🔑 {L3}: {row.get(L3)}")
        st.divider()
        st.code(f"🏢 VINHOMES\n📍 {row.get(L1)}\n✨ {row.get(L2)}\n💰 {row.get(L8)} Tỷ\n🏠 {row.get(L10)}")

st.title("🏢 Kho Hàng Vinhomes")

if sh_obj is not None:
    t1, t2 = st.tabs(["📋 Danh sách", "➕ Thêm hàng"])
    with t1:
        f1, f2, f3 = st.columns(3)
        with f1: pk = st.multiselect(L1, PK_L)
        with f2: lh = st.multiselect(L2, LH_L)
        with f3: pr = st.slider(L8, 0.0, 15.0, (0.0, 15.0), 0.1)
        df = df_raw.copy()
        if pk: df = df[df[L1].isin(pk)]
        if lh: df = df[df[L2].isin(lh)]
        df = df[(df[L8] >= pr[0]) & (df[L8] <= pr[1])]
        d_df = df.drop(columns=[L3]) if L3 in df.columns else df
        st.write(f"Tìm thấy {len(df)} căn")
        sel = st.dataframe(d_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
        if sel and sel.selection.rows:
            show_dt(df.iloc[sel.selection.rows[0]], is_adm)

    with t2:
        if is_adm:
            with st.form("form_v16", clear_on_submit=True):
                i1, i2, i3 = st.columns(3)
                with i1:
                    v_ng = st.date_input("Ngày lên hàng")
                    v_lh = st.selectbox(L2, LH_L); v_pk = st.selectbox(L1, PK_L)
                with i2:
                    v_ma = st.text_input(L3); v_dt = st.number_input(L4, 0.0, step=0.1)
                    v_tg = st.selectbox(L5, TG_L)
                with i3:
                    v_nt = st.selectbox(L6, NT_L); v_hb = st.selectbox(L7, H_L)
                    v_gi = st.number_input(L8, 0.0, step=0.01)
                
                # --- Trường mới bổ sung ---
                c_new1, c_new2 = st.columns([1, 2])
                with c_new1: v_ht = st.selectbox(L10, HT_L)
                with c_new2: v_gc = st.text_input(L11, placeholder="VD: Chủ nhà thiện chí, có slot đỗ xe...")
                
                f_up = st.file_uploader("📸 Chọn ảnh", type=["jpg", "png", "jpeg"])
                
                if st.form_submit_button("🚀 Lưu dữ liệu"):
                    img_url = ""
                    if f_up:
                        with st.spinner("Đang tải ảnh..."):
                            img_url = upload_img(f_up)
                    
                    try:
                        cols = [c.strip() for c in sh_obj.row_values(1)]
                        new_row = [""] * len(cols)
                        data_map = {
                            "Ngày lên hàng": str(v_ng), L2: v_lh, L1: v_pk, L3: v_ma,
                            L4: v_dt, L5: v_tg, L6: v_nt, L7: v_hb, L8: v_gi, 
                            L9: img_url, L10: v_ht, L11: v_gc, "Trạng thái": "Đang bán"
                        }
                        for idx, col_name in enumerate(cols):
                            if col_name in data_map: new_row[idx] = data_map[col_name]
                        sh_obj.append_row(new_row)
                        st.success("✅ Đã lưu xong!")
                        st.cache_resource.clear()
                    except Exception as e: st.error(f"Lỗi Sheets: {e}")
        else: st.warning("Nhập Pass Admin để thêm hàng")
