import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests, base64, time

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# --- DANH SÁCH CỐ ĐỊNH ---
LIST_PK = ["S", "GS", "SA", "VIC", "Sola", "Imper", "Tonkin", "Canopy", "Masteri", "Lumier"]
LIST_LH = ["Studio", "1N", "1N+", "2N", "2N+", "3N"]

# --- NHÃN CỘT ---
L_DATE, L_LH, L_PK, L_MA = "Ngày lên hàng", "Loại hình", "Phân khu", "Mã căn"
L_DT, L_TANG, L_NT, L_HBC = "Diện tích", "Khoảng tầng", "Nội thất", "Hướng BC"
L_GIA, L_HT, L_TT, L_IMG = "Giá bán", "Hiện trạng", "Trạng thái", "Link ảnh"
L_TYPE, L_GC = "Phân loại", "Ghi chú"
V_SOLD, V_RENT = "Đã bán", "Đã thuê"

# --- HÀM TRỢ GIÚP ---
def up_img(fs):
    if not fs: return ""
    try:
        ak = st.secrets.get("imgbb_api_key")
        res = []
        for f in fs:
            f.seek(0); b6 = base64.b64encode(f.read()).decode('utf-8')
            r = requests.post("https://api.imgbb.com/1/upload", {"key": ak, "image": b6}, timeout=20)
            if r.status_code == 200: res.append(r.json()['data']['url'])
        return ",".join(res)
    except: return ""

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
            total = len(imgs); ix = st.session_state.ci % total
            st.image(imgs[ix], use_container_width=True, caption=f"Ảnh {ix+1}/{total}")
            if total > 1:
                b1, b2 = st.columns(2)
                with b1: st.button("⬅️ Trước", key=f"p_{mid}", on_click=change_img, args=(-1, total))
                with b2: st.button("Sau ➡️", key=f"n_{mid}", on_click=change_img, args=(1, total))
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
                        c_idx = list(df_raw.columns).index(L_TT) + 1
                        sh_obj.update_cell(int(row['sheet_row']), c_idx, V_SOLD if ks=="B" else V_RENT)
                        st.session_state[ck] = False; st.cache_resource.clear(); st.rerun()
                with cn:
                    if st.button("Hủy", use_container_width=True, key=f"no_{mid}"):
                        st.session_state[ck] = False; st.rerun()
        st.code(f"Mã: {mid if is_adm else 'Ẩn'}")

# --- GIAO DIỆN CHÍNH (HEADER INLINE) ---
# Chia làm 2 cột lớn: Cột 1 chứa tiêu đề, Cột 2 chứa cụm đăng nhập
head_c1, head_c2 = st.columns([6, 4], vertical_alignment="center")

with head_c1:
    st.markdown("<h4 style='margin:0; padding:0;'>🏢 Nguồn hàng Vinhomes Smart City - Mr. Ninh - 0912.791.925</h4>", unsafe_allow_html=True)

with head_c2:
    if not is_adm:
        # Chia nhỏ cột 2 để pass và nút nằm ngang
        c_in, c_bt = st.columns([2.5, 1.5], vertical_alignment="center")
        with c_in:
            p = st.text_input("", type="password", placeholder="Password...", label_visibility="collapsed", key="login_pass")
        with c_bt:
            if st.button("Đăng nhập", use_container_width=True):
                if p == "admin123":
                    st.session_state.is_login = True; st.rerun()
                else:
                    st.toast("Sai mật khẩu!", icon="❌")
    else:
        ca1, ca2 = st.columns([1, 1], vertical_alignment="center")
        with ca1:
            if st.button("🔄 Làm mới", key="btn_ref", use_container_width=True): 
                st.cache_resource.clear(); st.rerun()
        with ca2:
            if st.button("🔒 Thoát", key="btn_out", use_container_width=True, type="primary"): 
                st.session_state.is_login = False; st.rerun()

st.divider() # Ngăn cách header với nội dung bên dưới

if sh_obj is not None and not df_raw.empty:
    t1, t2, t3 = st.tabs(["🔴 Chuyển nhượng", "🟢 Cho thuê", "➕ Thêm hàng"])
    
    def draw(df_in, ks):
        df_a = df_in[~df_in[L_TT].astype(str).str.contains("Đã", na=False)]
        c1, c2, c3 = st.columns([3, 3, 4])
        with c1: pk = st.multiselect("Phân khu", LIST_PK, key=f"p{ks}")
        with c2: lh = st.multiselect("Loại hình", LIST_LH, key=f"l{ks}")
        with c3:
            mi, ma = float(df_in[L_GIA].min()), float(df_in[L_GIA].max())
            r_gia = st.slider("Giá (Tỷ)", mi, ma, (mi, ma), key=f"g{ks}")
        
        if pk: df_a = df_a[df_a[L_PK].isin(pk)]
        if lh: df_a = df_a[df_a[L_LH].isin(lh)]
        df_a = df_a[(df_a[L_GIA] >= r_gia[0]) & (df_a[L_GIA] <= r_gia[1])]
        
        st.markdown(f"<div style='padding: 15px 0px; font-weight: bold; font-size: 17px;'>🔍 Đang hiển thị: {len(df_a)} căn hộ phù hợp</div>", unsafe_allow_html=True)
        
        v_cols = [L_DATE, L_LH, L_PK, L_DT, L_GIA, L_TT]
        if is_adm: v_cols.append(L_MA)
        sel = st.dataframe(df_a[v_cols], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key=f"df{ks}")
        if sel and sel.selection.rows:
            st.session_state.ci = 0; show_dt(df_a.iloc[sel.selection.rows[0]], ks)

    with t1: draw(df_raw[df_raw[L_TYPE].astype(str).str.contains("Bán|Ban", na=False)], "B")
    with t2: draw(df_raw[df_raw[L_TYPE].astype(str).str.contains("Thuê|Thue", na=False)], "T")
    with t3:
        if is_adm:
            with st.form("f_add", clear_on_submit=True):
                tp = st.radio("Loại", ["Bán", "Cho thuê"], horizontal=True)
                i1, i2, i3 = st.columns(3)
                with i1:
                    v_lh = st.selectbox(L_LH, LIST_LH)
                    v_ma = st.text_input(L_MA)
                with i2:
                    v_pk = st.selectbox(L_PK, LIST_PK)
                    v_dt = st.number_input(L_DT, 0.0)
                with i3:
                    v_gi = st.number_input(L_GIA, step=0.1)
                    v_ht = st.selectbox(L_HT, ["Đang ở", "Để trống", "Cho thuê"])
                v_gc = st.text_input(L_GC); up = st.file_uploader("Ảnh", accept_multiple_files=True)
                if st.form_submit_button("🚀 ĐĂNG CĂN"):
                    if v_ma:
                        imgs = up_img(up)
                        try:
                            h = list(df_raw.columns); row_d = [""] * len(h)
                            dm = {L_TYPE:tp, L_DATE:str(pd.Timestamp.now().date()), L_LH:v_lh, L_PK:v_pk, L_MA:v_ma, L_DT:v_dt, L_GIA:v_gi, L_HT:v_ht, L_GC:v_gc, L_TT:"Đang bán", L_IMG:imgs}
                            for i, col in enumerate(h):
                                if col in dm: row_d[i] = dm[col]
                            sh_obj.append_row(row_d); st.cache_resource.clear(); st.rerun()
                        except: st.error("Lỗi Sheets")
        else:
            st.warning("### 🔐 Khu vực dành cho quản trị viên")
            st.info("""
            Chào bạn, chức năng **Thêm hàng** chỉ dành cho tài khoản Admin.
            **Để cộng tác hoặc ký gửi nguồn hàng, vui lòng:**
            * Liên hệ trực tiếp: **0912.791.925 (Mr. Ninh)**
            """)
