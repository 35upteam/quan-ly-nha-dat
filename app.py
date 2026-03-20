import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests, base64

st.set_page_config(page_title="Vinhomes", layout="wide")

# NHÃN CỘT
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
        cols = [h.strip() for h in r[0]]
        df = pd.DataFrame(r[1:], columns=cols)
        df['sheet_row'] = range(2, len(df) + 2)
        df[L_GIA] = pd.to_numeric(
