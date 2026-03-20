# Hiển thị bảng và cho phép chọn dòng (Cập nhật cách viết an toàn)
    selection = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    # KIỂM TRA CHẮC CHẮN TRƯỚC KHI TRUY XUẤT
    if selection and hasattr(selection, 'selection') and len(selection.selection.get('rows', [])) > 0:
        idx = selection.selection.rows[0]
        row = f_df.iloc[idx] 
        
        st.divider()
        # ... (Phần hiển thị chi tiết bên dưới giữ nguyên) ...
