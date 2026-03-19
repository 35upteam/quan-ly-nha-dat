import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Kết nối Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Quan Ly Ky Gui").sheet1

st.set_page_config(page_title="Quản Lý Nhà Đất", layout="wide")
st.title("🏠 Hệ Thống Ký Gửi Nhà Đất")

# Nhập liệu
with st.sidebar.form("form_nhap"):
    st.header("Thêm Căn Hộ")
    m = st.text_input("Mã căn")
    c = st.text_input("Chủ nhà")
    s = st.text_input("SĐT")
    g = st.number_input("Giá (VNĐ)", step=1000000)
    d = st.number_input("Diện tích (m2)")
    btn = st.form_submit_button("Lưu vào Google Sheet")

if btn:
    sheet.append_row([m, c, s, g, d, "Đang rao"])
    st.sidebar.success("Đã lưu thành công!")

# Hiển thị và Tìm kiếm
data = sheet.get_all_records()
if data:
    df = pd.DataFrame(data)
    tk = st.text_input("🔍 Tìm tên chủ nhà hoặc mã căn")
    if tk:
        df = df[df.astype(str).apply(lambda x: x.str.contains(tk, case=False)).any(axis=1)]
    st.table(df)