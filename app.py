import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests, base64, time
from PIL import Image, ImageDraw, ImageFont # THÊM THƯ VIỆN NÀY ĐỂ VẼ ẢNH
import io

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

# --- HÀM TRỢ GIÚP (NÉN ẢNH) ---
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
    except: return ""

def change_img(step, total):
    st.session_state.ci = (st.session_state.get('ci', 0) + step) % total

# --- HÀM TẠO ẢNH CARD CHÀO HÀNG (MỚI - AN TOÀN) ---
def create_card(row, phone):
    try:
        # 1. Lấy ảnh đầu tiên
        imgs = str(row.get(L_IMG, "")).split(',') if row.get(L_IMG) else []
        if not imgs or not imgs[0]: return None
        
        r = requests.get(imgs[0], timeout=10)
        img = Image.open(io.BytesIO(r.content))
        if img.mode != 'RGB': img = img.convert('RGB')
        
        # 2. Định kích thước Card chuẩn (ví dụ: 1200x1600 cho Zalo/FB)
        target_w = 1200
        w_percent = (target_w / float(img.size[0]))
        target_h = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        # 3. Tạo khung vẽ
        card = Image.new('RGB', (target_w, target_h + 350), color=(255, 255, 255))
        card.paste(img, (0, 0))
        draw = ImageDraw.Draw(card)
        
        # 4. Vẽ Overlay màu xanh Vinhomes ở dưới
        vh_blue = (2, 62, 125) # Màu xanh Vinhomes
        draw.rectangle([(0, target_h), (target_w, target_h + 350)], fill=vh_blue)
        
        # 5. Định nghĩa Font chữ (Sử dụng Font mặc định nếu không có file font)
        # Để đẹp nhất, bạn nên upload file font 'Roboto-Bold.ttf' lên cùng thư mục code
        try:
            font_title = ImageFont.truetype("Roboto-Bold.ttf", 60)
            font_price = ImageFont.truetype("Roboto-Bold.ttf", 80)
            font_info = ImageFont.truetype("Roboto-Regular.ttf", 45)
        except:
            font_title = font_price = font_info = ImageFont.load_default()
            
        # 6. Viết thông tin
        # Tiêu đề
        text_title = f"🔥 HOT DEAL: {row[L_LH]} - {row[L_PK]} 🔥"
        draw.text((target_w/2, target_h + 40), text_title, fill=(255, 215, 0), font=font_title, anchor="mt") # Màu vàng Gold
        
        # Giá
        text_price = f"💰 GIÁ CHỈ: {row[L_GIA]} TỶ"
        draw.text((target_w/2, target_h + 120), text_price, fill=(255, 255, 255), font=font_price, anchor="mt")
        
        # Thông số chi tiết (2 cột)
        text_info_l = f"📐 Diện tích: {row[L_DT]}m²\n🧱 Tầng: {row[L_TANG]}\n🧭 Hướng: {row[L_HBC]}"
        draw.text((60, target_h + 230), text_info_l, fill=(255, 255, 255), font=font_info)
        
        text_info_r = f" Mã căn: {row[L_MA]}\n Nội thất: {row[L_NT]}\n 🚧 {row[L_HT]}"
        draw.text((650, target_h + 230), text_info_r, fill=(255, 255, 255), font=font_info)
        
        # Số điện thoại
        draw.text((target_w/2, target_h + 310), f"📞 LH Mr. Ninh: {phone}", fill=(255, 215, 0), font=font_info, anchor="mt")

        # 7. Xuất ảnh
        out = io.BytesIO()
        card.save(out, format="JPEG", quality=85)
        return out.getvalue()
    except Exception as e:
        print(f"Lỗi tạo card: {e}")
        return None

@st.cache_resource
