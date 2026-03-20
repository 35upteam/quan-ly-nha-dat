import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(page_title="Vinhomes Manager", layout="wide")

@st.cache_resource
def load_data():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        ss = client.open_by_key("19E9yyhhzLG58UpCU1Y4HAJsFWxG4AoGtGWVi_DkyQdk")
        sh = ss.get_worksheet(0)
        raw = sh.get_all_values()
        if not raw or len(raw) < 1: return pd.DataFrame(), sh
        cols = [str(h).strip() for h in raw[0]]
        df = pd.DataFrame(raw[1:], columns=cols)
        if "Giá bán" in df.columns:
            df["Giá bán"] = pd.to_numeric(df["Giá bán"].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame(), None

df_raw, sheet_obj = load_data()

# --- GIAO DIỆN TRÊN CÙNG (ĐĂNG NHẬP & CẬP NHẬT) ---
header_col1, header_col2, header_col3 = st.columns([2, 5, 2])

with header_col1:
    pw = st.text_input("🔑 Đăng nhập (Mật khẩu Admin)", type="password", label_visibility="collapsed", placeholder="Mật khẩu Admin...")
    is_admin = (pw == "admin123")

with header_col3:
    if st.button("🔄 Cập nhật dữ liệu", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

st.divider()

# --- HỘP THOẠI HIỆN THÔNG TIN CĂN HỘ (DIALOG) ---
@st.dialog("Chi tiết căn hộ", width="large")
def show_details(row, admin_mode):
    copy_text = (
        f"🏢 CĂN HỘ VINHOMES SMART CITY\n"
        f"📍 Phân khu: {row.get('Phân khu')}\n"
        f"✨ Loại hình: {row.get('Loại hình')}\n"
        f"📐 Diện tích: {row.get('Diện tích')} m2\n"
        f"🧭 Hướng: {row.get('Hướng BC')}\n"
        f"🛋️ Nội thất: {row.get('Nội thất')}\n"
        f"💰 Giá bán: {row.get('Giá bán', 0):.2f} Tỷ\n"
        f"📞 Liên hệ xem nhà ngay!"
    )
    
    col_img, col_info = st.columns([1, 1])
    with col_img:
        if row.get('Link ảnh'):
            st.image(row['Link ảnh'], use_container_width=True)
        else:
            st.info("Căn hộ này chưa có ảnh thực tế.")
            
    with col_info:
        st.subheader(f"{row.get('Loại hình')} - {row.get('Phân khu')}")
        st.write(f"📐 **Diện tích:** {row.get('Diện tích')} m2")
        st.write(f"🧭 **Hướng:** {row.get('Hướng BC')} | 🛋️ **Nội thất:** {row.get('Nội thất')}")
        st.markdown(f"### 💰 Giá: {row.get('Giá bán', 0):.2f} Tỷ")
        
        st.write("---")
        st.write("📋 **Nội dung gửi khách:**")
        st.code(copy_text, language="text")
        
        if admin_mode:
            st.error(f"🔑 MÃ CĂN HỘ (BẢO MẬT): {row.get('Mã căn')}")

# --- GIAO DIỆN CHÍNH ---
st.title("🏢 Kho Hàng Vinhomes Smart City")

if sheet_obj is not None:
    tab_list, tab_add = st.tabs(["📋 Danh sách căn hộ", "➕ Thêm hàng mới"])
    
    with tab_list:
        # Bộ lọc dàn hàng ngang
        f1, f2, f3 = st.columns(3)
        with f1: pk_f = st.multiselect("Lọc Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
        with f2: lh_f = st.multiselect("Lọc Loại hình", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
        with f3: pr_f = st.slider("Lọc Giá (Tỷ)", 0.0, 15.0, (0.0, 15.0), step=0.1, format="%.1f")

        df = df_raw.copy()
        if pk_f: df = df[df['Phân khu'].isin(pk_f)]
        if lh_f: df = df[df['Loại hình'].isin(lh_f)]
        df = df[(df['Giá bán'] >= pr_f[0]) & (df['Giá bán'] <= pr_f[1])]

        st.info(f"💡 Nhấn vào một dòng để xem ảnh và lấy nội dung copy (Tìm thấy {len(df)} căn)")
        
        # Bảng dữ liệu
        sel = st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True, 
            on_select="rerun", 
            selection_mode="single-row"
        )

        # Nếu chọn dòng, hiện Dialog
        if sel and sel.selection.rows:
            show_details(df.iloc[sel.selection.rows[0]], is_admin)

    with tab_add:
        if is_admin:
            with st.form("form_add", clear_on_submit=True):
                st.write("### 📝 Thêm căn hộ mới vào hệ thống")
                c1, c2, c3 = st.columns(3)
                with c1:
                    n_ngay = st.date_input("Ngày lên hàng")
                    n_loai = st.selectbox("Loại hình", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
                    n_pk = st.selectbox("Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
                with c2:
                    n_ma = st.text_input("Mã căn (Bảo mật)")
                    n_dt = st.number_input("Diện tích (m2)", min_value=0.0, step=0.1)
                    n_tg = st.selectbox("Khoảng tầng", ["Thấp", "Trung", "Cao"])
                with c3:
                    n_nt = st.selectbox("Nội thất", ["Nguyên bản", "Cơ bản", "Full đồ"])
                    n_hbc = st.selectbox("Hướng ban công", ["Đông", "Tây", "Nam", "Bắc", "Đông Bắc", "Đông Nam", "Tây Bắc", "Tây Nam"])
                    n_gia = st.number_input("Giá bán (Tỷ)", min_value=0.0, step=0.01)
                
                n_anh = st.text_input("Link ảnh căn hộ")
                
                if st.form_submit_button("🚀 Xác nhận lưu hàng"):
                    try:
                        h_list = sheet_obj.row_values(1)
                        new_row = [""] * len(h_list)
                        m = {
                            "Ngày lên hàng": str(n_ngay), "Loại hình": n_loai, "Phân khu": n_pk, 
                            "Mã căn": n_ma, "Diện tích": n_dt, "Khoảng tầng": n_tg, 
                            "Nội thất": n_nt, "Hướng BC": n_hbc, "Giá bán": n_gia, 
                            "Link ảnh": n_anh, "Trạng thái": "Đang bán"
                        }
                        for i, h in enumerate(h_list):
                            if h.strip() in m: new_row[i] = m[h.strip()]
                        sheet_obj.append_row(new_row)
                        st.success("Đã thêm thành công! Nhấn 'Cập nhật' để làm mới bảng.")
                        st.cache_resource.clear()
                    except Exception as e: st.error(f"Lỗi: {e}")
        else:
            st.warning("🔒 Vui lòng nhập mật khẩu Admin ở góc trên bên trái để sử dụng tính năng này.")
