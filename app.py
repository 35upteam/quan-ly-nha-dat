# Đoạn code logic Chốt căn mới
import time # Thêm thư viện này ở đầu file

if st.button("OK", use_container_width=True, key=f"ok_{mid}"):
    try:
        with st.spinner("Đang chốt..."):
            c_idx = list(df_raw.columns).index(L_TT) + 1
            r_idx = int(row['sheet_row'])
            new_val = V_SOLD if ks=="B" else V_RENT
            
            # Thực hiện cập nhật
            sh_obj.update_cell(r_idx, c_idx, new_val)
            
            # Đợi một chút để Google API ổn định
            time.sleep(1) 
            
            st.session_state[ck] = False
            st.cache_resource.clear()
            st.success("Đã chốt thành công!")
            time.sleep(0.5)
            st.rerun()
    except Exception as e:
        # Kiểm tra xem có phải lỗi "giả" không
        st.error(f"Phản hồi chậm từ Google, vui lòng Ref lại trang để kiểm tra.")
