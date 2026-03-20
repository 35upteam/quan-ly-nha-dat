import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests
import base64

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# --- DANH MỤC NHÃN (Chống lỗi ngắt dòng) ---
L1, L2, L3 = "Phân khu", "Loại hình", "Mã căn"
L4, L5, L6 = "Diện tích", "Khoảng tầng", "Nội thất"
L7, L8, L9 = "Hướng BC", "Giá bán", "Link ảnh"

PK_L = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
LH_L = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
H_L = ["Đông", "Tây", "Nam", "Bắc", "Đông Bắc", "Đông Nam", "Tây Bắc", "Tây Nam"]
NT_L = ["Nguyên bản", "Cơ bản", "Full đồ"]
TG_L = ["Thấp", "Trung", "Cao"]

# --- HÀM TẢI ẢNH LÊN KHO IMGBB ---
def upload_img(file_buffer):
    try:
        api_key = st.secrets["imgbb_api_key"]
        url = "https://api.imgbb.com/1/upload"
        # Mã hóa ảnh sang base64 để gửi đi
        b64_image = base64.b64encode(file_buffer.read()).decode('utf-8')
        payload = {"key": api_key, "image": b64_image}
        res = requests.post(url, payload)
        if res.status_code == 200:
            return res.json()['data']['url']
        return ""
    except:
        return ""

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
        if L8 in df.columns:
            df[L8] = pd.to_numeric(df[L8].str.replace(',', '.'), errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except:
        return pd.DataFrame(), None

df_raw, sh_obj = load_data()

# --- LOGIN SESSION ---
if 'is_login' not in st.session_state: 
    st.session_state.is_login = False

# --- HEADER ADMIN ---
h1, h2 = st.columns([7, 3])
with h2:
    s1, s2 = st.columns([5, 1])
    with s1:
        if not st.session_state.is_login:
            p = st.text_input("A", type="password", label_visibility="collapsed", placeholder="Pass...")
            if p == "admin123":
                st.session_state.is_login = True
                st.rerun()
        else:
            st.markdown("<div style='text-align:right;padding-top:5px;'><span style='color:#28a745;font-size:18px;font-weight:bold;'>Admin Mode ✅</span></div>", unsafe_allow_html=True)
    with s2:
        if st.session_state.is_login:
            if st.button("❌"):
                st.session_state.is_login = False
                st.rerun()
        else:
            if st.button("🔄"):
                st.cache_resource.clear()
                st.rerun()

is_adm = st.session_state.is_login

# --- CỬA SỔ CHI TIẾT ---
@st.dialog("📋 Chi tiết căn hộ", width="large")
def show_dt(row, adm):
    c1, c2 = st.columns([1.2, 1])
    with c1:
        if row.get(L9): 
            st.image(row[L9], use_container_width=True, caption="Ảnh thực tế")
        else: 
            st.info("Căn này chưa cập nhật ảnh thực tế")
    with c2:
        st.subheader(f"🏢 {row.get(L2)} - {row.get(L1)}")
        st.write(f"📐 **Diện tích:** {row.get(L4)} m2")
        st.write(f"🧭 **Hướng:** {row.get(L7)} | 🛋️ **Nội thất:** {row.get(L6)}")
        st.markdown(f"### 💰 Giá: {row.get(L8, 0):.2f} Tỷ")
        if adm: st.error(f"🔑 MÃ CĂN (BẢO MẬT): {row.get(L3)}")
        st.divider()
        # Tạo mẫu tin đăng nhanh
        t = f"🏢 VINHOMES SMART CITY\n📍 Khu: {row.get(L1)}\n✨ Loại: {row.get(L2)}\n📐 DT: {row.get(L4)}m2\n💰 Giá: {row.get(L8)} Tỷ"
        st.code(t)

st.title("🏢 Kho Hàng Vinhomes")

if sh_obj is not None:
    t1, t2 = st.tabs(["📋 Danh sách", "➕ Thêm hàng mới"])
    
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
        st.write(f"🔍 Tìm thấy {len(df)} căn đang chào bán.")
        
        cfg = {"use_container_width": True, "hide_index": True, 
               "on_select": "rerun", "selection_mode": "single-row"}
        sel = st.dataframe(d_df, **cfg)
        
        if sel and sel.selection.rows:
            show_dt(df.iloc[sel.selection.rows[0]], is_adm)

    with t2:
        if is_adm:
            with st.form("form_v12", clear_on_submit=True):
                st.write("### 📝 Đăng thông tin căn hộ mới")
                i1, i2, i3 = st.columns(3)
                with i1:
                    v_ng = st.date_input("Ngày lên hàng")
                    v_lh = st.selectbox(L2, LH_L)
                    v_pk = st.selectbox(L1, PK_L)
                with i2:
                    v_ma = st.text_input(L3, placeholder="VD: S1.02.1505")
                    v_dt = st.number_input(L4, 0.0, step=0.1)
                    v_tg = st.selectbox(L5, TG_L)
                with i3:
                    v_nt = st.selectbox(L6, NT_L)
                    v_hb = st.selectbox(L7, H_L)
                    v_gi = st.number_input(L8, 0.0, step=0.01)
                
                # NÚT CHỌN ẢNH TỪ MÁY/ĐIỆN THOẠI
                file_up = st.file_uploader("📸 Tải ảnh căn hộ (JPG, PNG)", type=["jpg","png","jpeg"])
                
                if st.form_submit_button("🚀 Xác nhận lưu vào hệ thống"):
                    final_url = ""
                    if file_up:
                        with st.spinner("Đang tải ảnh lên kho lưu trữ..."):
                            final_url = upload_img(file_up)
                    
                    try:
                        headers = [x.strip() for x in sh_obj.row_values(1)]
                        new_row = [""] * len(headers)
                        # Khai báo từng dòng để tránh lỗi ngắt dòng GitHub
                        dm = {}
                        dm["Ngày lên hàng"] = str(v_ng)
                        dm[L2], dm[L1], dm[L3] = v_lh, v_pk, v_ma
                        dm[L4], dm[L5], dm[L6] = v_dt, v_tg, v_nt
                        dm[L7], dm[L8], dm[L9] = v_hb, v_gi, final_url
                        dm["Trạng thái"] = "Đang bán"
                        
                        for i, col in enumerate(headers):
                            if col in dm: new_row[i] = dm[col]
                        sh_obj.append_row(new_row)
                        st.success("✅ Đã lưu thông tin thành công!")
                        st.cache_resource.clear()
                    except Exception as e:
                        st.error(f"Lỗi khi lưu dữ liệu: {e}")
        else:
            st.warning("🔒 Vui lòng nhập mật khẩu Admin để sử dụng tính năng này.")
