import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# Khai bao danh sach co icon
PK_L = ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"]
LH_L = ["Studio", "1PN+", "2PN", "2PN+", "3N"]
H_L = ["Đông", "Tây", "Nam", "Bắc", "Đông Bắc", "Đông Nam", "Tây Bắc", "Tây Nam"]
NT_L = ["Nguyên bản", "Cơ bản", "Full đồ"]
TG_L = ["Thấp", "Trung", "Cao"]

@st.cache_resource
def load_data():
    try:
        s = st.secrets["gcp_service_account"]
        sc = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        c = ServiceAccountCredentials.from_json_keyfile_dict(s, sc)
        g = gspread.authorize(c)
        k = "19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk"
        ss = g.open_by_key(k)
        sh = ss.get_worksheet(0)
        r = sh.get_all_values()
        if not r or len(r) < 1: return pd.DataFrame(), sh
        df = pd.DataFrame(r[1:], columns=[h.strip() for h in r[0]])
        if "Giá bán" in df.columns:
            df["Giá bán"] = pd.to_numeric(df["Giá bán"].str.replace(',', '.'), errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame(), None

df_raw, sh_obj = load_data()

# Header Login (Góc phải)
c1, c2 = st.columns([7, 3])
with c2:
    p_in = st.text_input("Mật khẩu Admin", type="password", label_visibility="collapsed", placeholder="Nhập pass...")
    is_adm = (p_in == "admin123")
    bc1, bc2 = st.columns(2)
    with bc1:
        if is_adm: st.success("ADMIN ✅")
    with bc2:
        if st.button("🔄 Refresh"):
            st.cache_resource.clear()
            st.rerun()

@st.dialog("📋 Thông tin chi tiết căn hộ", width="large")
def show_dt(row, adm):
    c_img, c_txt = st.columns([1, 1])
    with c_img:
        if row.get('Link ảnh'): st.image(row['Link ảnh'], use_container_width=True)
        else: st.info("Chưa có ảnh thực tế")
    with c_txt:
        st.subheader(f"🏢 {row.get('Loại hình')} - {row.get('Phân khu')}")
        st.write(f"📐 **Diện tích:** {row.get('Diện tích')} m2")
        st.write(f"🧭 **Hướng:** {row.get('Hướng BC')} | 🛋️ **Nội thất:** {row.get('Nội thất')}")
        st.markdown(f"### 💰 Giá: {row.get('Giá bán', 0):.2f} Tỷ")
        if adm: st.error(f"🔑 MÃ CĂN: {row.get('Mã căn')}")
        st.divider()
        # Nội dung copy
        t = f"🏢 CĂN HỘ VINHOMES SMART CITY\n"
        t += f"📍 Phân khu: {row.get('Phân khu')}\n"
        t += f"✨ Loại hình: {row.get('Loại hình')}\n"
        t += f"📐 Diện tích: {row.get('Diện tích')} m2\n"
        t += f"💰 Giá: {row.get('Giá bán', 0):.2f} Tỷ\n"
        t += f"📞 Liên hệ em xem nhà ngay!"
        st.code(t, language="text")

st.title("🏢 Kho Hàng Vinhomes Smart City")
if sh_obj is not None:
    t1, t2 = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])
    
    with t1:
        col1, col2, col3 = st.columns(3)
        with col1: f_p = st.multiselect("Phân khu", PK_L)
        with col2: f_l = st.multiselect("Loại hình", LH_L)
        with col3: f_g = st.slider("Giá bán (Tỷ)", 0.0, 15.0, (0.0, 15.0), 0.1)

        df = df_raw.copy()
        if f_p: df = df[df['Phân khu'].isin(f_p)]
        if f_l: df = df[df['Loại hình'].isin(f_l)]
        df = df[(df['Giá bán'] >= f_g[0]) & (df['Giá bán'] <= f_g[1])]

        d_df = df.copy()
        if 'Mã căn' in d_df.columns: d_df = d_df.drop(columns=['Mã căn'])
        
        st.write(f"🔍 Tìm thấy **{len(df)}** căn hộ phù hợp")
        s = st.dataframe(d_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
        
        if s and s.selection.rows:
            show_dt(df.iloc[s.selection.rows[0]], is_adm)

    with t2:
        if is_adm:
            with st.form("add_f", clear_on_submit=True):
                st.write("### 📝 Nhập thông tin căn mới")
                i1, i2, i3 = st.columns(3)
                with i1:
                    n_y = st.date_input("Ngày lên hàng")
                    n_l = st.selectbox("Loại hình", LH_L)
                    n_p = st.selectbox("Phân khu", PK_L)
                with i2:
                    n_m = st.text_input("Mã căn (Bảo mật)")
                    n_s = st.number_input("Diện tích (m2)", 0.0, step=0.1)
                    n_t = st.selectbox("Tầng", TG_L)
                with i3:
                    n_n = st.selectbox("Nội thất", NT_L)
                    n_h = st.selectbox("Hướng BC", H_L)
                    n_g = st.number_input("Giá bán (Tỷ)", 0.0, step=0.01)
                n_a = st.text_input("Link ảnh căn hộ")
                if st.form_submit_button("🚀 Lưu vào hệ thống"):
                    try:
                        h = [x.strip() for x in sh_obj.row_values(1)]
                        r = [""] * len(h)
                        m = {"Ngày lên hàng": str(n_y), "Loại hình": n_l, "Phân khu": n_p, "Mã căn": n_m, "Diện tích": n_s, "Khoảng tầng": n_t, "Nội thất": n_n, "Hướng BC": n_h, "Giá bán": n_g, "Link ảnh": n_a, "Trạng thái": "Đang bán"}
                        for i, x in enumerate(h):
                            if x in m: r[i] = m[x]
                        sh_obj.append_row(r)
                        st.success("✅ Đã lưu thành công!")
                        st.cache_resource.clear()
                    except Exception as e: st.error(e)
        else:
            st.warning("🔒 Vui lòng nhập mật khẩu Admin ở góc trên bên phải để thêm hàng.")
