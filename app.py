import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests, base64, time, urllib.parse

st.set_page_config(page_title="Vinhomes Manager", layout="wide", page_icon="🏢")

# --- CẤU HÌNH NHÃN ---
L_DATE, L_LH, L_PK, L_MA = "Ngày lên hàng", "Loại hình", "Phân khu", "Mã căn"
L_DT, L_TANG, L_NT, L_HBC = "Diện tích", "Khoảng tầng", "Nội thất", "Hướng BC"
L_GIA, L_HT, L_TT, L_IMG = "Giá bán", "Hiện trạng", "Trạng thái", "Link ảnh"
L_TYPE, L_GC = "Phân loại", "Ghi chú"
V_SOLD, V_RENT = "Đã bán", "Đã thuê"

# --- HÀM TRỢ GIÚP ---
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

# --- XỬ LÝ CHẾ ĐỘ VIEW DÀNH CHO KHÁCH (Dựa trên URL) ---
# Lấy tham số 'id' từ URL (ví dụ: ?id=S1021505)
query_params = st.query_params
guest_view_id = query_params.get("id")

def show_guest_view(row):
    st.write("### 🏠 Thông tin chi tiết căn hộ")
    c1, c2 = st.columns([1.5, 1])
    with c1:
        imgs = str(row.get(L_IMG, "")).split(',') if row.get(L_IMG) else []
        if imgs and imgs[0]:
            if 'g_ci' not in st.session_state: st.session_state.g_ci = 0
            ix = st.session_state.g_ci % len(imgs)
            st.image(imgs[ix], use_container_width=True)
            if len(imgs) > 1:
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("⬅️ Trước"): st.session_state.g_ci -= 1; st.rerun()
                with b2:
                    if st.button("Sau ➡️"): st.session_state.g_ci += 1; st.rerun()
        else: st.info("Hình ảnh đang được cập nhật...")
    with c2:
        st.subheader(f"{row[L_LH]} - {row[L_PK]}")
        st.header(f"💰 {row[L_GIA]} Tỷ")
        st.divider()
        st.write(f"📐 **Diện tích:** {row[L_DT]}m²")
        st.write(f"🧭 **Hướng BC:** {row[L_HBC]}")
        st.write(f"🧱 **Khoảng tầng:** {row[L_TANG]}")
        st.write(f"🛋️ **Nội thất:** {row[L_NT]}")
        st.write(f"🚧 **Hiện trạng:** {row[L_HT]}")
        if row.get(L_GC): st.info(f"**Lưu ý:** {row[L_GC]}")
        st.success("Liên hệ trực tiếp để nhận ưu đãi và xem nhà!")

# Nếu có ID khách xem, hiện giao diện khách và dừng App tại đây
if guest_view_id and not df_raw.empty:
    target_row = df_raw[df_raw[L_MA] == guest_view_id]
    if not target_row.empty:
        show_guest_view(target_row.iloc[0])
        st.stop() # Dừng không chạy phần quản lý bên dưới
    else:
        st.error("Căn hộ này đã được bán hoặc không tồn tại.")
        st.stop()

# --- GIAO DIỆN QUẢN LÝ (CHO ADMIN & CTV) ---
if 'is_login' not in st.session_state: st.session_state.is_login = False
is_adm = st.session_state.is_login

@st.dialog("Chi tiết & Gửi khách")
def show_dt(row, ks):
    mid = str(row.get(L_MA, "0"))
    cl1, cl2 = st.columns([1.2, 1])
    with cl1:
        imgs = str(row.get(L_IMG, "")).split(',') if row.get(L_IMG) else []
        if imgs and imgs[0]:
            if 'ci' not in st.session_state: st.session_state.ci = 0
            ix = st.session_state.ci % len(imgs); st.image(imgs[ix], use_container_width=True)
            if len(imgs) > 1:
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("⬅️", key=f"p_{mid}"): st.session_state.ci -= 1; st.rerun()
                with b2:
                    if st.button("➡️", key=f"n_{mid}"): st.session_state.ci += 1; st.rerun()
    with cl2:
        st.subheader(f"{row[L_LH]} - {row[L_PK]}")
        st.success(f"{row[L_GIA]} Tỷ")
        
        # --- NÚT LẤY LINK GỬI KHÁCH ---
        base_url = "https://quan-ly-nha-dat.streamlit.app/" # Thay bằng link app thật của bạn
        share_url = f"{base_url}?id={mid}"
        st.text_input("Link gửi khách (Đã ẩn mã căn):", value=share_url)
        st.caption("Hãy copy link này gửi cho khách qua Zalo/Facebook")

        if is_adm:
            st.divider(); ck = f"ck_{mid}"
            if not st.session_state.get(ck, False):
                if st.button("✅ ĐÃ CHỐT", use_container_width=True, type="primary", key=f"bt_{mid}"):
                    st.session_state[ck] = True; st.rerun()
            else:
                st.warning("Xác nhận?"); cy, cn = st.columns(2)
                with cy:
                    if st.button("OK", type="primary", key=f"ok_{mid}"):
                        c_idx = list(df_raw.columns).index(L_TT) + 1
                        sh_obj.update_cell(int(row['sheet_row']), c_idx, V_SOLD if ks=="B" else V_RENT)
                        st.session_state[ck] = False; st.cache_resource.clear(); st.rerun()
                with cn:
                    if st.button("Hủy", key=f"no_{mid}"): st.session_state[ck] = False; st.rerun()
        st.code(f"Mã nội bộ: {mid if is_adm else 'Ẩn'}")

# --- PHẦN CÒN LẠI GIỮ NGUYÊN NHƯ BẢN CŨ ---
h1, h2 = st.columns([7, 3])
with h1: st.title("🏢 Vinhomes Manager")
with h2:
    if not is_adm:
        p = st.text_input("Admin", type="password", label_visibility="collapsed")
        if p == "admin123": st.session_state.is_login = True; st.rerun()
    else:
        st.info("✅ Admin")
        if st.button("Thoát"): st.session_state.is_login = False; st.rerun()

if sh_obj is not None and not df_raw.empty:
    t1, t2, t3 = st.tabs(["🔴 Bán", "🟢 Thuê", "➕ Thêm hàng"])
    def draw(df_in, ks):
        df_a = df_in[~df_in[L_TT].astype(str).str.contains("Đã", na=False)]
        c1, c2, c3 = st.columns([3, 3, 4])
        with c1: pk = st.multiselect("Phân khu", sorted(df_in[L_PK].unique()), key=f"p{ks}")
        with c2: lh = st.multiselect("Loại", sorted(df_in[L_LH].unique()), key=f"l{ks}")
        with c3:
            mi, ma = float(df_in[L_GIA].min()), float(df_in[L_GIA].max())
            r_gia = st.slider("Giá (Tỷ)", mi, ma, (mi, ma), key=f"g{ks}")
        if pk: df_a = df_a[df_a[L_PK].isin(pk)]
        if lh: df_a = df_a[df_a[L_LH].isin(lh)]
        df_a = df_a[(df_a[L_GIA] >= r_gia[0]) & (df_a[L_GIA] <= r_gia[1])]
        
        v_cols = [L_DATE, L_LH, L_PK, L_DT, L_GIA, L_TT]
        if is_adm: v_cols.append(L_MA)
        sel = st.dataframe(df_a[v_cols], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key=f"df{ks}")
        if sel and sel.selection.rows:
            st.session_state.ci = 0; show_dt(df_a.iloc[sel.selection.rows[0]], ks)

    with t1: draw(df_raw[df_raw[L_TYPE].astype(str).str.contains("Bán|Ban
