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
        df = pd.DataFrame(raw[1:], columns=[str(h).strip() for h in raw[0]])
        if "Giá bán" in df.columns:
            df["Giá bán"] = pd.to_numeric(df["Giá bán"].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame(), None

df_raw, sheet_obj = load_data()

with st.sidebar:
    st.header("🔑 Phân quyền")
    pw = st.text_input("Mật khẩu Admin", type="password")
    is_admin = (pw == "admin123")
    if st.button("🔄 Cập nhật danh sách"):
        st.cache_resource.clear()
        st.rerun()

st.title("🏢 Kho Hàng Vinhomes Smart City")

if sheet_obj is not None:
    t1, t2 = st.tabs(["📋 Danh sách", "➕ Thêm hàng"])
    
    with t1:
        c1, c2, c3 = st.columns(3)
        with c1: pk_f = st.multiselect("Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
        with c2: lh_f = st.multiselect("Loại hình", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
        with c3: pr_f = st.slider("Giá (Tỷ)", 0.0, 15.0, (0.0, 15.0), step=0.1, format="%.2f")

        df = df_raw.copy()
        if pk_f: df = df[df['Phân khu'].isin(pk_f)]
        if lh_f: df = df[df['Loại hình'].isin(lh_f)]
        df = df[(df['Giá bán'] >= pr_f[0]) & (df['Giá bán'] <= pr_f[1])]

        st.write(f"🔍 Tìm thấy **{len(df)}** căn")
        # Sử dụng selection_mode="single-row" để chọn căn hộ
        sel = st.dataframe(df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

        if sel and sel.selection.rows:
            idx = sel.selection.rows[0]
            row = df.iloc[idx]
            
            # Chuẩn bị nội dung để copy
            copy_text = (
                f"🏢 CĂN HỘ VINHOMES SMART CITY\n"
                f"📍 Phân khu: {row.get('Phân khu')}\n"
                f"✨ Loại hình: {row.get('Loại hình')}\n"
                f"🧭 Hướng: {row.get('Hướng BC')}\n"
                f"🛋️ Nội thất: {row.get('Nội thất')}\n"
                f"💰 Giá bán: {row.get('Giá bán', 0):.2f} Tỷ\n"
                f"📞 Liên hệ xem nhà ngay!"
            )
            
            st.divider()
            col_a, col_b = st.columns([1, 2])
            with col_a:
                if row.get('Link ảnh'): st.image(row['Link ảnh'], use_container_width=True)
                else: st.info("Chưa có ảnh")
            with col_b:
                st.subheader(f"Chi tiết: {row.get('Loại hình')} - {row.get('Phân khu')}")
                # Nút copy tích hợp sẵn của Streamlit
                st.code(copy_text, language="text")
                st.info("💡 Bạn hãy bôi đen đoạn mã trên hoặc nhấn biểu tượng copy ở góc phải ô văn bản.")
                
                if is_admin:
                    st.error(f"🔑 MÃ CĂN HỘ: {row.get('Mã căn')}")

    with t2:
        if is_admin:
            with st.form("add_form", clear_on_submit=True):
                # ... (Giữ nguyên phần form thêm hàng như cũ)
                st.write("### 📝 Nhập thông tin căn hộ")
                f1, f2, f3 = st.columns(3)
                with f1:
                    ngay = st.date_input("Ngày")
                    loai = st.selectbox("Loại hình", ["Studio", "1PN+", "2PN", "2PN+", "3N"])
                    pkn = st.selectbox("Phân khu", ["S", "SA", "GS", "Mas", "Tonkin", "Canopy", "I", "Sola", "VIC"])
                with f2:
                    ma = st.text_input("Mã căn")
                    tg = st.selectbox("Tầng", ["Thấp", "Trung", "Cao"])
                    nt = st.selectbox("Nội thất", ["Nguyên bản", "Cơ bản", "Full đồ"])
                with f3:
                    hbc = st.selectbox("Hướng", ["Đông", "Tây", "Nam", "Bắc", "Đông Bắc", "Đông Nam", "Tây Bắc", "Tây Nam"])
                    gia = st.number_input("Giá (Tỷ)", min_value=0.0, step=0.01)
                    anh = st.text_input("Link ảnh")
                if st.form_submit_button("🚀 Lưu"):
                    try:
                        h_list = sheet_obj.row_values(1)
                        new_row = [""] * len(h_list)
                        m = {"Ngày lên hàng": str(ngay), "Loại hình": loai, "Phân khu": pkn, "Mã căn": ma, "Khoảng tầng": tg, "Nội thất": nt, "Hướng BC": hbc, "Giá bán": gia, "Link ảnh": anh, "Trạng thái": "Đang bán"}
                        for i, h in enumerate(h_list):
                            if h.strip() in m: new_row[i] = m[h.strip()]
                        sheet_obj.append_row(new_row)
                        st.success("Đã lưu!")
                        st.cache_resource.clear()
                    except Exception as e: st.error(f"Lỗi: {e}")
        else:
            st.warning("Vui lòng nhập mật khẩu Admin.")
