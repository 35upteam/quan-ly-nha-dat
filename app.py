def upload_img(f):
    try:
        # Kiểm tra chìa khóa ở cả 2 vị trí có thể xảy ra
        api_key = None
        if "imgbb_api_key" in st.secrets:
            api_key = st.secrets["imgbb_api_key"]
        elif "gcp_service_account" in st.secrets and "imgbb_api_key" in st.secrets["gcp_service_account"]:
            api_key = st.secrets["gcp_service_account"]["imgbb_api_key"]
            
        if not api_key:
            st.error("Lỗi: Vẫn chưa tìm thấy 'imgbb_api_key' trong Secrets!")
            return ""
        
        f.seek(0)
        img_64 = base64.b64encode(f.read()).decode('utf-8')
        payload = {"key": api_key, "image": img_64}
        res = requests.post("https://api.imgbb.com/1/upload", payload, timeout=15)
        
        if res.status_code == 200:
            return res.json()['data']['url']
        else:
            st.error(f"ImgBB báo lỗi: {res.text}")
            return ""
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return ""
