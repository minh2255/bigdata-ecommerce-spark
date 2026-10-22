# Checklist chạy lại bởi thành viên khác

Đây là checklist cần người khác thực sự thực hiện trên máy của họ. Toàn bộ ô bên dưới chưa được đánh dấu vì hiện chỉ có kiểm thử trên máy Windows của TV3. Không dùng kết quả kiểm thử tự động cùng máy để điền thay.

- [ ] Ghi người kiểm thử, máy/hệ điều hành, thời điểm và commit/nhánh nhận bàn giao.
- [ ] Có bản mã nguồn TV3 đã được nhóm chia sẻ/review hợp lệ; không tự động push/merge từ phiên này.
- [ ] Kiểm tra Docker/Compose và engine Linux/WSL2 phù hợp, không mặc định máy giống TV3.
- [ ] Khởi động image/cụm theo README, xác nhận hai worker ALIVE.
- [ ] Kiểm tra mount data/jobs/scripts và chọn DATA_DIR mới.
- [ ] Chạy fixture mixed qua --ingest-clean, ghi exit code và log.
- [ ] Chạy verify fixture và validate_cleaning; đối chiếu counts 14 → 13 → 12 → 11 → 6 → 3.
- [ ] Chạy clean-only từ raw mới, xác nhận không ingest lại và không gọi TV2/TV4.
- [ ] Chạy empty/all-invalid, đọc được schema Parquet và count bằng 0.
- [ ] Chạy lại cùng vùng bị chặn; không mất hoặc đổi dữ liệu/báo cáo đã tạo.
- [ ] Full mode thiếu job dừng trước ingest; ghi rõ phụ thuộc đang thiếu.
- [ ] Thử đường dẫn dữ liệu có khoảng trắng theo môi trường thực tế của máy đó.
- [ ] TV2 xác nhận data contract và các mở rộng NaN/Inf/session trắng/chuỗi rỗng.
- [ ] Khi có Kaggle, xác nhận nguồn/header/tài nguyên, chạy vùng real mới và lưu metrics/validation.
- [ ] TV2 tạo profiling raw/clean chính thức; TV4 xác nhận schema/UTC và đối chiếu KPI.
- [ ] Người kiểm thử ghi các khác biệt, lỗi và cách sửa; TV3 cập nhật tài liệu nếu cần.

Mẫu biên bản: người kiểm thử; máy; phiên bản Docker/Compose/Spark; nhánh/commit; nguồn dữ liệu; DATA_DIR; lệnh; exit code; vị trí log; kết luận; các mục chưa thực hiện. Nếu chưa có dữ liệu thật, biên bản chỉ xác nhận synthetic, không đánh dấu phần Kaggle.
