# Checklist chạy lại bởi thành viên khác

Đây là checklist cần người khác thực sự thực hiện trên máy của họ. Toàn bộ ô bên dưới chưa được đánh dấu vì hiện chỉ có kiểm thử trên máy Windows của TV3. Không dùng kết quả kiểm thử tự động cùng máy để điền thay.

- [ ] Ghi người kiểm thử, máy/hệ điều hành, thời điểm và commit/nhánh nhận bàn giao.
- [ ] Có bản mã nguồn TV3 đã được nhóm chia sẻ/review hợp lệ; không tự động push/merge từ phiên này.
- [ ] Kiểm tra Docker/Compose và engine Linux/WSL2 phù hợp, không mặc định máy giống TV3.
- [ ] Khởi động image/cụm theo README, xác nhận hai worker ALIVE.
- [ ] Kiểm tra mount data/jobs/scripts và chọn DATA_DIR mới.
- [ ] Chạy fixture mixed qua --ingest-clean, ghi exit code và log.
- [ ] Chạy verify fixture và validate_cleaning; đối chiếu counts với verifier độc lập (fixture mới đã thêm timestamp lỗi và -Inf).
- [ ] Chạy clean-only từ raw mới, xác nhận không ingest lại và không gọi TV2/TV4.
- [ ] Chạy empty/all-invalid, đọc được schema Parquet và count bằng 0.
- [ ] Chạy lại cùng vùng bị chặn; không mất hoặc đổi dữ liệu/báo cáo đã tạo.
- [ ] Full mode: ghi exit code và kết quả; nếu nhánh thiếu job thì dừng trước ingest với exit 3 (ghi rõ job thiếu).
- [ ] Thử đường dẫn dữ liệu có khoảng trắng theo môi trường thực tế của máy đó.
- [ ] Đọc contract TV2 v1.0; kiểm tra UTC bắt buộc, NaN/Inf/session trắng/chuỗi rỗng.
- [ ] Với dữ liệu Kaggle thật: xác nhận nguồn/header/tài nguyên; máy RAM thấp chạy theo lát (phụ lục, mục chạy theo lát), lưu metrics/validation từng lát và đối chiếu tổng với `docs/evidence/tv2/cleaning_metrics_merged.json` (raw 42.448.764; written 42.349.872).
- [ ] Chạy --quality-check với generator TV2; compare_truth và validator đạt; profiling clean all_pass=true.
- [ ] TV4 xác nhận schema/UTC và đối chiếu KPI khi có aggregation.
- [ ] Người kiểm thử ghi các khác biệt, lỗi và cách sửa; TV3 cập nhật tài liệu nếu cần.

Mẫu biên bản: người kiểm thử; máy; phiên bản Docker/Compose/Spark; nhánh/commit; nguồn dữ liệu; DATA_DIR; lệnh; exit code; vị trí log; kết luận; các mục chưa thực hiện. Nếu chưa có dữ liệu thật, biên bản chỉ xác nhận synthetic, không đánh dấu phần Kaggle.


## Biên bản mẫu cho người kiểm thử

Người kiểm thử tự điền; để trống nếu chưa thực hiện. Không điền thay bằng kết quả tự động cùng máy.

| Mục | Nội dung điền |
| --- | --- |
| Người kiểm thử (họ tên) | |
| Ngày giờ bắt đầu / kết thúc | |
| Máy, hệ điều hành, RAM/CPU | |
| Phiên bản Docker / Compose / Spark | |
| Nhánh và commit nhận bàn giao | |
| Nguồn dữ liệu (synthetic/real) và DATA_KIND | |
| DATA_DIR đã dùng (mỗi lượt một vùng mới) | |
| Lệnh đã chạy | |
| Exit code | |
| Vị trí log pipeline | |
| Số dòng raw / clean / written đối chiếu | |
| Khác biệt so với tài liệu, lỗi và cách xử lý | |
| Mục checklist chưa thực hiện | |
| Kết luận (đạt / không đạt / chưa đủ điều kiện) | |
| Chữ ký người kiểm thử | |
