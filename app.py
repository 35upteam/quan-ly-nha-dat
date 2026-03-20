import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests, base64

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# Toàn bộ nhãn được viết ngắn nhất có thể
L_TYPE, L1, L2, L3 = "Phan loai", "Phan khu", "Loai hinh", "Ma can"
L4, L5, L6, L7, L8, L9 = "Dien tich", "Tang", "Noi that", "Huong", "Gia", "Anh"
L10, L11, L12 = "Hien trang", "Ghi chu", "Trang thai"

PK_L = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
LH_L = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
H_L = ["Dong", "Tay", "Nam", "Bac", "DB", "DN", "TB", "TN"]
NT_L = ["Nguyen ban", "Co ban", "Full do"]
TG_L = ["Thap", "Trung", "Cao"]
HT_L = ["Dang o", "Cho thue", "Trong"]

def up_img(fs):
    if not fs: return ""
    try:
        ak = st.secrets.get("imgbb_api_key") or st.secrets.get("gcp_service_account", {}).get("imgbb_api_key")
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
        df = pd.DataFrame(r[1:], columns=[h.strip() for h in r[0]])
        for cn in [L_TYPE, L1, L2, L3, L8, L12]:
            if cn not in df.columns: df[cn] = ""
        return df.iloc[::-1].reset_index(drop=True), sh
    except: return pd.DataFrame(), None

df_raw, sh_obj = load_data()
if 'is_login' not in st.session_state: st.session_state.is_login = False

h1, h2 = st.columns([7, 3])
with h1: st.title("Vinhomes")
with h2:
    if not st.session_state.is_login:
        p = st.text_input("P", type="password")
        if p == "admin123":
            st.session_state.is_login = True
            st.rerun()
    else:
        if st.button("Refresh"):
            st.cache_resource.clear()
            st.rerun()

is_adm = st.session_state.is_login

if sh_obj is not None:
    t1, t2, t3 = st.tabs(["Ban", "Thue", "Them"])
    def draw(df_in, ks):
        df_a = df_in[~df_in[L12].astype(str).str.contains("Da", na=False)]
        if df_a.empty: 
            st.info("Trong")
            return
        ca, cb = st.columns(2)
        with ca: pk = st.multiselect("Khu", PK_L, key=f"p{ks}")
        with cb: lh = st.multiselect("Loai", LH_L, key=f"l{ks}")
        if pk: df_a = df_a[df_a[L1].isin(pk)]
        if lh: df_a = df_a[df_a[L2].isin(lh)]
        scols = df_a.drop(columns=[L9, L_TYPE, L12, L3] if not is_adm else [L9, L_TYPE, L12], errors='ignore')
        sel = st.dataframe(scols, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key=f"d{ks}")

        @st.dialog(f"Detail {ks}")
        def show_dt(row):
            c1, c2 = st.columns([1.2, 1])
            with c1:
                ls = str(row.get(L9, "")).split(',') if row.get(L9) else []
                if ls and ls[0]:
                    if 'ci' not in st.session_state: st.session_state.ci = 0
                    ix = st.session_state.ci % len(ls)
                    st.image(ls[ix], use_container_width=True)
                    if len(ls) > 1:
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("<<", key=f"pr{ks}"):
                                st.session_state.ci -= 1
                                st.rerun()
                        with b2:
                            if st.button(">>", key=f"nx{ks}"):
                                st.session_state.ci += 1
                                st.rerun()
                else: st.info("No Img")
            with c2:
                st.write("Loai: ", row[L2])
                st.write("Gia: ", row[L8])
                if is_adm:
                    st.divider()
                    ck = f"cf_{row[L3]}"
                    if ck not in st.session_state: st.session_state[ck] = False
                    if not st.session_state[ck]:
                        if st.button("CHOT", use_container_width=True, key=f"bc{ks}"):
                            st.session_state[ck] = True
                            st.rerun()
                    else:
                        st.warning("Confirm?")
                        cy, cn = st.columns(2)
                        with cy:
                            if st.button("OK", key=f"y{ks}"):
                                try:
                                    h = [x.strip() for x in sh_obj.row_values(1)]
                                    ids = sh_obj.col_values(h.index(L3)+1)
                                    ridx = ids.index(row[L3])+1
                                    nv = "Da ban" if "Ban" in str(row[L_TYPE]) else "Da thue"
                                    sh_obj.update_cell(ridx, h.index(L12)+1, nv)
                                    st.session_state[ck] = False
                                    st.cache_resource.clear()
                                    st.rerun()
                                except: st.error("Error")
                        with cn:
                            if st.button("No", key=f"n{ks}"):
                                st.session_state[ck] = False
                                st.rerun()

        if sel and sel.selection.rows:
            st.session_state.ci = 0
            show_dt(df_a.iloc[sel.selection.rows[0]])

    with t1: draw(df_raw[df_raw[L_TYPE].str.contains("Ban", na=False)] if not df_raw.empty else pd.DataFrame(), "B")
    with t2: draw(df_raw[df_raw[L_TYPE].str.contains("thue", na=False, case=False)] if not df_raw.empty else pd.DataFrame(), "T")
    with t3:
        if is_adm:
            with st.form("f_add", clear_on_submit=True):
                tp = st.radio("Loai", ["Ban", "Cho thue"])
                i1, i2 = st.columns(2)
                with i1:
                    v_lh = st.selectbox(L2, LH_L)
                    v_pk = st.selectbox(L1, PK_L)
                    v_ma = st.text_input(L3)
                with i2:
                    v_gi = st.text_input(L8)
                    v_ht = st.selectbox(L10, HT_L)
                up = st.file_uploader("Anh", accept_multiple_files=True)
                if st.form_submit_button("Luu"):
                    imgs = up_img(up)
                    try:
                        h = [x.strip() for x in sh_obj.row_values(1)]
                        new = [""] * len(h)
                        dm = {L_TYPE:tp, L2:v_lh, L1:v_pk, L3:v_ma, L8:v_gi, L9:imgs, L12:"Dang ban"}
                        for idx, col in enumerate(h):
                            if col in dm: new[idx] = dm[col]
                        sh_obj.append_row(new)
                        st.success("OK")
                        st.cache_resource.clear()
                        st.rerun()
                    except: st.error("Loi")
