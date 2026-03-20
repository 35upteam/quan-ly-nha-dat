import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests, base64

st.set_page_config(page_title="App", layout="wide")

# KHAI BÁO NHÃN NGẮN
L_DATE = "Ngày lên hàng"
L_LH = "Loại hình"
L_PK = "Phân khu"
L_MA = "Mã căn"
L_DT = "Diện tích"
L_TANG = "Khoảng tầng"
L_NT = "Nội thất"
L_HBC = "Hướng BC"
L_GIA = "Giá bán"
L_HT = "Hiện trạng"
L_TT = "Trạng thái"
L_IMG = "Link ảnh"
L_TYPE = "Phân loại"
L_GC = "Ghi chú"

T_DONE = "Đã"
V_SOLD = "Đã bán"
V_RENT = "Đã thuê"

def up_img(fs):
    if not fs: return ""
    try:
        ak = st.secrets.get("imgbb_api_key")
        res = []
        for f in fs:
            f.seek(0)
            b6 = base64.b64encode(f.read()).decode('utf-8')
            r = requests.post("https://api.imgbb.com/1/upload", {"key": ak, "image": b6}, timeout=20)
            if r.status_code == 200:
                res.append(r.json()['data']['thumb']['url']) 
        return ",".join(res)
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
        h = [x.strip() for x in r[0]]
        df = pd.DataFrame(r[1:], columns=h)
        df['sheet_row'] = range(2, len(df) + 2)
        df[L_GIA] = pd.to_numeric(df[L_GIA], errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except: return pd.DataFrame(), None

df_raw, sh_obj = load_data()
if 'is_login' not in st.session_state:
    st.session_state.is_login = False

# HEADER
c1, c2 = st.columns([7, 3])
with c1:
    st.title("Vinhomes Manager")
with c2:
    if not st.session_state.is_login:
        p = st.text_input("Pass", type="password")
        if p == "admin123":
            st.session_state.is_login = True
            st.rerun()
    else:
        st.write("Admin OK")
        if st.button("Refresh"):
            st.cache_resource.clear()
            st.rerun()
        if st.button("Logout"):
            st.session_state.is_login = False
            st.rerun()

is_adm = st.session_state.is_login
if sh_obj is not None and not df_raw.empty:
    # TÁCH TABS RA TỪNG DÒNG ĐỂ CHỐNG NGẮT
    t_list = []
    t_list.append("CHUYỂN NHƯỢNG")
    t_list.append("CHO THUÊ")
    t_list.append("THÊM HÀNG")
    t1, t2, t3 = st.tabs(t_list)
    
    def draw(df_in, ks):
        df_a = df_in[~df_in[L_TT].astype(str).str.contains(T_DONE, na=False)]
        if df_a.empty:
            st.info("Trống")
            return
        
        s_ma = st.text_input("Tìm mã căn", key=f"s{ks}")
        
        # BỘ LỌC TÁCH DÒNG
        pk_opts = sorted(df_in[L_PK].unique())
        pk = st.multiselect("Khu", pk_opts, key=f"p{ks}")
        
        lh_opts = sorted(df_in[L_LH].unique())
        lh = st.multiselect("Loại", lh_opts, key=f"l{ks}")
        
        mi = float(df_in[L_GIA].min())
        ma = float(df_in[L_GIA].max())
        r_gia = st.slider("Giá", mi, ma, (mi, ma), key=f"g{ks}")
        
        if s_ma:
            df_a = df_a[df_a[L_MA].astype(str).str.contains(s_ma, case=False, na=False)]
        if pk:
            df_a = df_a[df_a[L_PK].isin(pk)]
        if lh:
            df_a = df_a[df_a[L_LH].isin(lh)]
        
        df_a = df_a[(df_a[L_GIA] >= r_gia[0]) & (df_a[L_GIA] <= r_gia[1])]

        v_cols = []
        v_cols.append(L_DATE)
        v_cols.append(L_LH)
        v_cols.append(L_PK)
        v_cols.append(L_DT)
        v_cols.append(L_GIA)
        v_cols.append(L_TT)
        if is_adm:
            v_cols.append(L_MA)
        
        sel = st.dataframe(df_a[v_cols], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key=f"df{ks}")

        @st.dialog("Chi tiết")
        def show_dt(row):
            rid = str(row.get(L_MA, "0"))
            c_l, c_r = st.columns([1, 1])
            with c_l:
                img_data = str(row.get(L_IMG, ""))
                imgs = img_data.split(',') if img_data else []
                if imgs and imgs[0]:
                    if 'ci' not in st.session_state:
                        st.session_state.ci = 0
                    ix = st.session_state.ci % len(imgs)
                    st.image(imgs[ix], use_container_width=True)
                    if len(imgs) > 1:
                        if st.button("Next", key=f"n_{rid}_{ks}"):
                            st.session_state.ci += 1
                            st.rerun()
                else:
                    st.info("No Image")
            with c_r:
                st.write(f"Khu: {row[L_PK]}")
                st.success(f"Giá: {row[L_GIA]} Tỷ")
                if is_adm:
                    ck = f"k_{rid}"
                    if ck not in st.session_state:
                        st.session_state[ck] = False
                    if not st.session_state[ck]:
                        if st.button("CHỐT CĂN", key=f"b_{rid}_{ks}"):
                            st.session_state[ck] = True
                            st.rerun()
                    else:
                        if st.button("XÁC NHẬN", key=f"y_{rid}_{ks}"):
                            try:
                                h_list = [x.strip() for x in sh_obj.row_values(1)]
                                idx = h_list.index(L_TT) + 1
                                val = V_SOLD if ks == "B" else V_RENT
                                sh_obj.update_cell(int(row['sheet_row']), idx, val)
                                st.session_state[ck] = False
                                st.cache_resource.clear()
                                st.rerun()
                            except:
                                st.error("Lỗi")
                        if st.button("Hủy", key=f"n_{rid}_{ks}"):
                            st.session_state[ck] = False
                            st.rerun()
                st.code(f"Ghi chú: {row.get(L_GC, '')}")
        
        if sel and sel.selection.rows:
            st.session_state.ci = 0
            show_dt(df_a.iloc[sel.selection.rows[0]])

    with t1:
        draw(df_raw[df_raw[L_TYPE].astype(str).str.contains("Bán|Ban|bán|ban", na=False)], "B")
    with t2:
        draw(df_raw[df_raw[L_TYPE].astype(str).str.contains("Thuê|Thue|thuê|thue", na=False)], "T")
    with t3:
        if is_adm:
            with st.form("f_add", clear_on_submit=True):
                tp = st.radio("Loại", ["Bán", "Cho thuê"])
                v_lh = st.selectbox(L_LH, ["Studio", "1PN+", "2PN", "3N"])
                v_pk = st.selectbox(L_PK, ["S", "SA", "GS", "Mas", "Tonkin", "VIC"])
                v_ma = st.text_input(L_MA)
                v_dt = st.number_input(L_DT, 0.0)
                v_gi = st.number_input(L_GIA, step=0.1)
                v_gc = st.text_input(L_GC)
                up = st.file_uploader("Ảnh", accept_multiple_files=True)
                if st.form_submit_button("LÊN HÀNG"):
                    if v_ma:
                        img_urls = up_img(up)
                        try:
                            h = [x.strip() for x in sh_obj.row_values(1)]
                            row_d = [""] * len(h)
                            dm = {L_TYPE:tp, L_DATE:str(pd.Timestamp.now().date()), L_LH:v_lh, L_PK:v_pk, L_MA:v_ma, L_DT:v_dt, L_GIA:v_gi, L_GC:v_gc, L_TT:"Đang hàng", L_IMG:img_urls}
                            for i, col in enumerate(h):
                                if col in dm: row_d[i] = dm[col]
                            sh_obj.append_row(row_d)
                            st.cache_resource.clear()
                            st.rerun()
                        except: st.error("Lỗi")
