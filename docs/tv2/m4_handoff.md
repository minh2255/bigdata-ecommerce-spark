# M4 — Bản nháp bàn giao cho TV4

Soạn ngày 11/11/2026. Chưa gửi tin cho TV4, chưa có xác nhận review hoặc nhận bàn giao. Các file mới và Ch.6 sửa vẫn ở working tree, chưa commit/push. Không coi tài liệu là bản cuối đã xử lý mọi phát hiện số liệu.

## Markdown cần ghép vào báo cáo

| File | Vị trí/nội dung ghép | Tình trạng |
|---|---|---|
| [ch02_1_bigdata.md](ch02_1_bigdata.md) | Ch.2.1: 5V, Data Lake, Parquet | Có bản nháp; còn đề xuất về độ chính xác số trong audit 5b |
| [ch03_du_lieu.md](ch03_du_lieu.md) | Ch.3: nguồn, schema, chất lượng và contract | Có bản nháp; còn đề xuất sửa thời gian, làm tròn và chi tiết thiếu nguồn |
| [ch06_kb3_kb5.md](ch06_kb3_kb5.md) | Ch.6: KB3 và KB5 | Đã sửa theo nguồn ở M3; cần review khi ghép |
| [phu_luc_schema.md](phu_luc_schema.md) | Phụ lục schema và ví dụ dữ liệu | Ví dụ khớp; dung lượng và tỷ lệ còn đề xuất sửa ở 5b |
| [ch08_bai_hoc_ai.md](ch08_bai_hoc_ai.md) | Ch.8: bài học và ghi chú dùng AI | Đã soạn; sinh viên cần đọc lại và điền đúng phần tự kiểm tra |

## Tài liệu hỗ trợ, không ghép nguyên văn vào thân báo cáo

- [demo_script.md](demo_script.md): kịch bản trình bày và lệnh chạy; còn chờ diễn tập và ảnh.
- [cau_hoi_bao_ve.md](cau_hoi_bao_ve.md): bộ câu hỏi bao phủ toàn pipeline; còn chờ tự ôn.
- [m3_screenshot_checklist.md](m3_screenshot_checklist.md): hướng dẫn ảnh và lệnh tạo DATA_DIR mới.
- [Data contract](../data_contract.md): luật dùng chung của nhóm.
- [Audit 5b](../evidence/tv2/audit_5b_review_20261111.md): danh sách điểm khớp/chưa đủ nguồn và đề xuất sửa. Bộ kiểm kê là thư mục `audit_5b_20261111_final`, không dùng bản thử không có hậu tố final. Audit 5b được chốt trước khi có demo/bộ câu hỏi/bản bàn giao; không mô tả nó là kiểm kê tự động các file mới hơn.
- [CSV KB3](../evidence/tv2/kb3.csv), [cấu hình KB3](../evidence/tv2/kb3_env.json), [CSV biểu đồ KB5](../evidence/tv2/m3_kb5_chart_data.csv).
- Evidence bổ sung: profiling raw/clean, cleaning_metrics_merged, slices, cây thư mục landing/raw; thư mục M1 và JSON kiểm chứng samples M2 trong `docs/evidence/tv2/`.

## Tin nhắn để người dùng copy gửi TV4

> TV2 gửi bản nháp bàn giao M4 để ghép báo cáo. Các Markdown chính trong `docs/tv2/`: `ch02_1_bigdata.md`, `ch03_du_lieu.md`, `ch06_kb3_kb5.md`, `phu_luc_schema.md`, `ch08_bai_hoc_ai.md`.
>
> Tài liệu hỗ trợ riêng: `demo_script.md`, `cau_hoi_bao_ve.md`, `m3_screenshot_checklist.md`; luật chung ở `docs/data_contract.md`. Số liệu/biểu đồ lấy từ `docs/evidence/tv2/`, đặc biệt `kb3.csv`, `kb3_env.json` và `m3_kb5_chart_data.csv`.
>
> Nhờ đọc `docs/evidence/tv2/audit_5b_review_20261111.md` trước khi chốt bản ghép. Số đếm chính khớp nhưng Ch.3/phụ lục còn đề xuất sửa độ chính xác, thời gian và dung lượng; vài chi tiết chưa có JSON/CSV nguồn. Chưa coi mọi số liệu là đã sạch vấn đề. Không kết luận cart giảm là số trùng riêng hoặc doanh thu không đổi sau dedup.
>
> Ảnh minh chứng, diễn tập demo, tự ôn và xác nhận review vẫn còn chờ. Các file mới cùng bản Ch.6 sửa đang ở máy TV2, chưa commit/push, nên chưa thể lấy toàn bộ bản mới bằng pull main. Mình sẽ thống nhất cách chuyển bản mới sau; tin này chưa có nghĩa file đã được TV4 nhận hoặc ghép xong.

## Trạng thái để cập nhật roadmap

- ✅ Đã có các Markdown báo cáo, kịch bản demo, bộ câu hỏi và tin nháp M4.
- ✅ Đã chạy full synthetic và kiểm chứng samples; đã đối chiếu KB3/KB5, tạo cây thư mục và audit số liệu.
- ⬜ Xử lý các đề xuất sửa còn mở của audit 5b, sinh viên đọc lại nội dung và phần khai báo AI.
- ⬜ Người dùng gửi tin M0/M1/M2/M3/M4; TV1 review profiling; TV4 xác nhận nhận/ghép bài.
- ⬜ Chụp ảnh, chạy thử cấu hình demo và diễn tập, tự ôn bộ câu hỏi.
- ⬜ Commit/chuyển bản mới theo quyết định sau của người dùng; không tự push/merge/mở PR.

Không đánh dấu M4 hoàn tất bàn giao khi mới có tin nháp.

## Hai vùng dữ liệu cũ cần quyết định

[Kiểm kê dọn dữ liệu](../evidence/tv2/cleanup_candidates_20261111.json) ghi hiện trạng, không thực hiện xóa.
`data/synthetic_tv2_test` không tồn tại. `data/synthetic_tv2_gen01` còn tồn tại và chứa báo cáo lần synthetic cũ; bằng chứng M1 mới nằm ở một DATA_DIR khác. Lệnh demo/checklist hiện tham chiếu DATA_DIR M1 mới.

Người dùng đã đồng ý dọn gen01 sau khi sao lưu báo cáo. Đã sao lưu toàn bộ reports vào `docs/evidence/tv2/archive_synthetic_tv2_gen01_20261111/reports`, kiểm tra SHA256 từng file; manifest nằm cạnh thư mục reports. Lệnh xóa bị cơ chế kiểm duyệt tự động từ chối với lý do `blocked by policy`, nên dữ liệu gốc vẫn còn và chưa xóa thành công. Không thử công cụ khác để vượt chặn.
