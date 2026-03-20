import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests, base64, time
from PIL import Image, ImageDraw, ImageFont
import io

# Cấu hình trang nằm ở đầu tiên
st.set_page_config(page_title="Vinhomes Manager", layout="wide")

# --- DANH SÁCH CỐ ĐỊNH ---
LIST_PK = ["S", "GS", "SA", "VIC", "Sola", "Imper", "Tonkin", "Canopy", "Masteri", "Lumier"]
LIST_LH = ["Studio", "1N", "1N+", "2N", "2N+", "3N"]
LIST_TANG = ["Thấp", "Trung", "Cao"]
LIST_NT = ["Nguyên bản", "Cơ bản", "Đầy đủ nội thất"]
LIST_HBC = ["Đông", "Tây", "Nam", "Bắc", "Đông Nam", "Đông Bắc", "Tây Nam", "Tây Bắc"]

# --- NHÃN CỘT ---
L_DATE, L_LH, L_PK, L_MA = "Ngày lên hàng", "Loại hình", "Phân khu", "Mã căn"
L_DT, L_TANG, L_NT, L_HBC = "Diện tích", "Khoảng tầng", "Nội thất", "Hướng BC"
L_GIA, L_HT, L_TT, L_IMG = "Giá bán", "Hiện trạng", "Trạng thái", "Link ảnh"
L_TYPE, L_GC = "Phân loại", "Ghi chú"
V_SOLD, V_RENT = "Đã bán", "Đã thuê"

# --- HÀM TRỢ GIÚP 1: UPLOAD & NÉN ẢNH ---
def up_img(fs):
    if not fs: return ""
    try:
        ak = st.secrets.get("imgbb_api_key")
        res = []
        for f in fs:
            f.seek(0)
            img = Image.open(f)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            out = io.BytesIO()
            img.save(out, format="JPEG", quality=70, optimize=True)
            b6 = base64.b64encode(out.getvalue()).decode('utf-8')
            r = requests.post("https://api.imgbb.com/1/upload", {"key": ak, "image": b6}, timeout=20)
            if r.status_code == 200: res.append(r.json()['data']['url'])
        return ",".join(res)
    except:
        return ""

# --- HÀM TRỢ GIÚP 2: ĐỔI ẢNH SLIDE ---
def change_img(step, total):
    st.session_state.ci = (st.session_state.get('ci', 0) + step) % total

# --- HÀM TRỢ GIÚP 3: TẠO ẢNH CARD ---
def create_card(row, phone):
    try:
        imgs = str(row.get(L_IMG, "")).split(',') if row.get(L_IMG) else []
        if not imgs or not imgs[0]: return None
        
        r = requests.get(imgs[0], timeout=10)
        img = Image.open(io.BytesIO(r.content))
        if img.mode != 'RGB': img = img.convert('RGB')
        
        target_w = 1200
        w_percent = (target_w / float(img.size[0]))
        target_h = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        card = Image.new('RGB', (target_w, target_h + 350), color=(255, 255, 255))
        card.paste(img, (0, 0))
        draw = ImageDraw.Draw(card)
        
        vh_blue = (2, 62, 125) 
        draw.rectangle([(0, target_h), (target_w, target_h + 350)], fill=vh_blue)
        
        # Font mặc định (Sẽ đẹp hơn nếu bạn có file .ttf)
        f_title = f_price = f_info = ImageFont.load_default()
            
        draw.text((target_w/2, target_h + 40), f"HOT DEAL: {row[L_LH]} - {row[L_PK]}", fill=(255, 215, 0), font=f_title, anchor="mt")
        draw.text((target_w/2, target_h + 120), f"GIA: {row[L_GIA]} TY", fill=(255, 255, 255), font=f_price, anchor="mt")
        
        info_l = f"DT: {row[L_DT]}m2\nTang: {row[L_TANG]}\nHuong: {row[L_HBC]}"
        draw.text((60, target_h + 230), info_l, fill=(255, 255, 255), font=f_info)
        
        info_r = f"Ma: {row[L_MA]}\nNoi that: {row[L_NT]}\n{row[L_HT]}"
        draw.text((650, target_h + 230), info_r, fill=(255, 255, 255), font=f_info)
        
        draw.text((target_w/2, target_h + 310), f"LH Mr. Ninh: {phone}", fill=(255, 215, 0), font=f_info, anchor="mt")

        out = io.BytesIO()
        card.save(out, format="JPEG", quality=85)
        return out.getvalue()
    except:
        return None

# --- LOAD DATA (ĐÃ FIX LỀ) ---
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
        if not r: return pd.DataFrame(), None
        h = [x.strip() for x in r[0]]
        df = pd.DataFrame(r[1:], columns=h)
        df['sheet_row'] = range(2, len(df) + 2)
        df[L_GIA] = pd.to_numeric(df[L_GIA], errors='coerce').fillna(0)
        return df.iloc[::-1].reset_index(drop=True), sh
    except:
        return pd.DataFrame(), None

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
            st.image(imgs[ix], use_container_width=True)
            if total > 1:
                b1, b2 = st.columns(2)
                with b1: st.button("⬅️ Trước", key=f"p_{mid}", on_click=change_img, args=(-1, total))
                with b2: st.button("Sau ➡️", key=f"n_{mid}", on_click=change_img, args=(1, total))
        
        st.divider()
        c_data = create_card(row, "0912.791.925")
        if c_data:
            st.download_button("📷 Tải Card chào hàng", data=c_data, file_name=f"Card_{mid}.jpg", mime="image/jpeg", use_container_width=True)

    with cl2:
        st.subheader(f"{row[L_LH]} - {row[L_PK]}")
        st.success(f"💰 Giá: {row[L_GIA]} Tỷ")
        st.write(f"📐 Diện tích: {row[L_DT]}m² | 🧭 BC: {row[L_HBC]}")
        st.write(f"🧱 Tầng: {row[L_TANG]} | Nội thất: {row[L_NT]}")
        if is_adm:
            st.divider(); ck = f"ck_{mid}"
            if not st.session_state.get(ck, False):
                if st.button("✅ ĐÃ CHỐT", use_container_width=True, type="primary", key=f"bt_{mid}"):
                    st.session_state[ck] = True; st.rerun()
            else:
                if st.button("Xác nhận OK", type="primary", use_container_width=True, key=f"ok_{mid}"):
                    c_idx = list(df_raw.columns).index(L_TT) + 1
                    sh_obj.update_cell(int(row['sheet_row']), c_idx, V_SOLD if ks=="B" else V_RENT)
                    st.session_state[ck] = False; st.cache_resource.clear(); st.rerun()
        st.code(f"Mã: {mid if is_adm else 'Ẩn'}")

# --- GIAO DIỆN CHÍNH ---
st.markdown("<h4>🏢 Vinhomes Smart City - Mr. Ninh - 0912.791.925</h4>", unsafe_allow_html=True)

if not is_adm:
    with st.expander("Admin Login"):
        p = st.text_input("Pass", type="password")
        if st.button("Vào"):
            if p == "admin123": st.session_state.is_login = True; st.rerun()
else:
    if st.button("🔒 Thoát Admin"): st.session_state.is_login = False; st.rerun()

st.divider()

if sh_obj is not None:
    t1, t2, t3 = st.tabs(["🔴 Chuyển nhượng", "🟢 Cho thuê", "➕ Thêm hàng"])
    
    def draw(df_in, ks):
        df_a = df_in[~df_in[L_TT].astype(str).str.contains("Đã", na=False)]
        if ks == "B":
            c1, c2, c3 = st.columns([3, 3, 4])
            with c3: r_gia = st.slider("Giá (Tỷ)", 0.0, 10.0, (0.0, 10.0), key=f"g{ks}")
            df_a = df_a[(df_a[L_GIA] >= r_gia[0]) & (df_a[L_GIA] <= r_gia[1])]
        else:
            c1, c2 = st.columns(2)
            
        with c1: pk = st.multiselect("Phân khu", LIST_PK, key=f"p{ks}")
        with c2: lh = st.multiselect("Loại hình", LIST_LH, key=f"l{ks}")
        
        if pk: df_a = df_a[df_a[L_PK].isin(pk)]
        if lh: df_a = df_a[df_a[L_LH].isin(lh)]
        
        v_cols = [L_DATE, L_LH, L_PK, L_DT, L_GIA, L_TT]
        if is_adm: v_cols.append(L_MA)
        sel = st.dataframe(df_a[v_cols], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key=f"df{ks}")
        if sel and sel.selection.rows:
            show_dt(df_a.iloc[sel.selection.rows[0]], ks)

    with t1: draw(df_raw[df_raw[L_TYPE].str.contains("Bán|Ban", na=False)], "B")
    with t2: draw(df_raw[df_raw[L_TYPE].str.contains("Thuê|Thue", na=False)], "T")
    with t3:
        if is_adm:
            with st.form("f_add", clear_on_submit=True):
                tp = st.radio("Loại", ["Bán", "Cho thuê"], horizontal=True)
                i1, i2, i3 = st.columns(3)
                with i1:
                    v_lh = st.selectbox(L_LH, LIST_LH)
                    v_ma = st.text_input(L_MA)
                    v_tang = st.selectbox(L_TANG, LIST_TANG)
                with i2:
                    v_pk = st.selectbox(L_PK, LIST_PK)
                    v_dt = st.number_input(L_DT, 0.0)
                    v_nt = st.selectbox(L_NT, LIST_NT)
                with i3:
                    v_gi = st.number_input(L_GIA, step=0.1)
                    v_hbc = st.selectbox(L_HBC, LIST_HBC)
                    v_ht = st.selectbox(L_HT, ["Đang ở", "Để trống", "Cho thuê"])
                up = st.file_uploader("Ảnh", accept_multiple_files=True)
                if st.form_submit_button("🚀 ĐĂNG CĂN"):
                    if v_ma:
                        imgs = up_img(up)
                        try:
                            h = [col.strip() for col in df_raw.columns if col != 'sheet_row']
                            dm = {L_TYPE:tp, L_DATE:str(pd.Timestamp.now().date()), L_LH:v_lh, L_PK:v_pk, L_MA:v_ma, L_DT:str(v_dt), L_GIA:v_gi, L_HT:v_ht, L_TT:"Đang bán", L_IMG:imgs, L_TANG:v_tang, L_NT:v_nt, L_HBC:v_hbc}
                            row_d = [dm.get(c, "") for c in h]
                            sh_obj.append_row(row_d)
                            st.cache_resource.clear(); st.rerun()
                        except: st.error("Lỗi Sheets")
