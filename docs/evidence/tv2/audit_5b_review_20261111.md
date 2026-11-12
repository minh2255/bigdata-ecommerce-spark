# 5b — Đối chiếu số liệu toàn bộ Markdown TV2

Ngày kiểm tra: 11/11/2026. Phạm vi là mọi file `docs/tv2/*.md` tại thời điểm chạy script, kể cả checklist M3. Không sửa nội dung các chương trong bước này; các sửa đổi dưới đây là đề xuất. Thay đổi Ch.6 từ giai đoạn M3 vẫn được giữ nguyên.

## Cách đọc bằng chứng

Chạy từ gốc repo:

```powershell
python scripts/audit_tv2_numbers.py --out-dir docs/evidence/tv2/audit_5b_20261111_final
```

Output gồm `number_inventory.csv` (mọi token chứa chữ số, file/dòng/cột/ngữ cảnh), `source_index.json` (địa chỉ field JSON hoặc dòng/cột CSV) và `summary.json` (danh sách file đã đọc, SHA256, thống kê bao phủ). Chạy lại phải chọn thư mục output mới. Các bản Markdown được khóa bằng SHA256 trong summary; sau khi sửa cần chạy lại để có số dòng mới.

Dùng bộ có hậu tố `_final`. Bộ `audit_5b_20261111/` là bản chạy thử ban đầu, trước khi sửa chuẩn hóa số có dấu chấm phân cách hàng nghìn; không dùng bản đó để kết luận. Script loại chính các index/summary sinh ra khỏi danh sách nguồn thực nghiệm.

**Không coi số tình cờ bằng nhau là đã kiểm chứng.** Trạng thái `SOURCE_CANDIDATE_NOT_VERDICT` chỉ là gợi ý tìm nguồn, không phải PASS. CSV hiển thị tối đa tám nguồn ứng viên/token; index JSON giữ toàn bộ. `CONTEXT_REVIEW` gồm cả số không tìm thấy, tỷ lệ đã đổi đơn vị, số chương, ngày, port, ID, version và tham số lệnh. Phần trăm không tự chuyển thành tỷ lệ thập phân. Bảng dưới kiểm tra theo ngữ nghĩa để bổ sung cho inventory.

Nguồn dùng trực tiếp: JSON/CSV evidence toàn tháng, các lát, M1, M2, KB3; bản sao báo cáo thử nhỏ trong `audit_5b_sample3m/`. `audit_5b_sources_20261111.json` là snapshot mới từ đọc CSV header/hai dòng đầu, metadata thư mục và đọc lọc ví dụ Parquet bằng PyArrow. Không chạy job Spark, không quét lại dữ liệu toàn tháng để tính thống kê mới.

## Bảng đối chiếu theo file và nhóm số

Các đường dẫn nguồn dưới đây tương đối với `docs/evidence/tv2/` nếu không ghi khác.

| File / vị trí | Số hoặc nhóm số trong tài liệu | Nguồn và trường đối chiếu | Kết luận / đề xuất |
|---|---|---|---|
| ch02_1_bigdata, Volume và diễn giải | 5.668.612.855 byte; 42.448.764 dòng | kb3.csv: size/csv; profiling_raw.json: rows | Khớp số nguyên. Các chỗ 5,7 GB là làm tròn thêm; dùng byte nguồn để tuân thủ yêu cầu giữ nguyên độ chính xác. |
| ch02_1_bigdata, schema và thực nghiệm | 9 cột; ba lần đo | profiling_raw.json: columns.length; kb3_env.json: repeats | Khớp. |
| ch02_1_bigdata, tài nguyên/cấu trúc | 8 GB máy, hai worker, bốn tầng, 5V, version 1.0/1.1, số chương/job | 8 GB là ràng buộc người dùng, không phải số benchmark JSON; worker theo compose; tầng/schema/contract theo mã và tài liệu | Là cấu hình, lý thuyết, định danh hoặc giả định tương lai; không gán nhầm là kết quả thực nghiệm. Nhận định Pandas không thể nạp toàn bộ chưa được KB4 trong nguồn TV2 này chứng minh; nên nói nguy cơ vượt RAM. |
| ch03_du_lieu, 3.1 | dung lượng, rows, khoảng thời gian và schema | kb3.csv: size/csv; profiling_raw.json: rows, timestamp_min/max, columns | Khớp các số chính. Bỏ 5,7 GB làm tròn thêm hoặc ghi chính xác byte. Ngày ví dụ là định dạng/giá trị minh họa, không phải số lượng. |
| ch03_du_lieu, bảng 3.2 | 30.220; 68.673; 2; 13.515.609; 6.113.008 và các bộ đếm 0 | profiling_raw.json: duplicate_rows, price.price_zero, nulls.user_session/category_code/brand, ids, event_time, price | Số đếm khớp. Các tỷ lệ 0,07%, 0,16%, gần 0, 31,8%, 14,4% là trình bày làm tròn thêm. Đề xuất bỏ cột tỷ lệ hoặc dùng trường tỷ lệ nguồn dạng thập phân và nêu tên trường. |
| ch03_du_lieu, bảng 3.2 chi tiết | giá 0 gồm 68.523 view + 150 cart; hai session thiếu đều cart; category sâu 3 cấp 36.242 (0,09%) | Các số chi tiết này có trong docs/data_contract.md mục 7, nhưng chưa có JSON/CSV nguồn tương ứng trong bộ evidence đã kiểm tra | CHƯA ĐỦ NGUỒN máy đọc được. Không kết luận sai, cũng không đánh dấu khớp. Đề xuất bỏ chi tiết/ghi chờ bảng chéo nguồn; không dùng contract làm bằng chứng thực nghiệm độc lập. |
| ch03_du_lieu, thành phần sự kiện | 40.779.399 view; 926.516 cart; 742.849 purchase | profiling_raw.json: event_type_counts | Số đếm khớp. 96,1% / 2,2% / 1,7% không có dưới dạng field nguồn và đã làm tròn; đề xuất giữ số đếm, không ghi tỷ lệ mới. Không dùng tỷ lệ số sự kiện thay cho funnel distinct sessions. |
| ch03_du_lieu, so tập nhỏ | raw 3.000.000; dedup 2.998.565; clean 2.993.871; trùng 1.435; giá 4.694; ngày 1–3/10 | audit_5b_sample3m/cleaning_metrics.json: counts, removed; profiling_raw.json: timestamp_min/max, duplicate_rows, price.price_le_0 | Khớp số đếm và phạm vi ngày. 0,048%/0,16% là làm tròn thêm; tỷ lệ JSON lần nhỏ là duplicate_ratio=0.000478 và price_le_0_ratio=0.001565. |
| ch03_du_lieu, yêu cầu và contract | 7 quy tắc, 9 cột, giờ 0–23, phiên bản, các số thứ tự | cleaning_schema JSON; profiling_clean.json: columns, event_hour_range; docs/data_contract.md và code | Là cấu trúc/ràng buộc; không trộn với số liệu đo. Dedup trước chuẩn hóa có thể tạo clean giống nhau; không yêu cầu dedup clean lại. |
| ch03_du_lieu, 3.3 | raw 42.448.764 → dedup 42.418.544 → giá 42.349.874 → clean 42.349.872; loại 30.220/68.670/2; tổng 98.892, chênh 3 | cleaning_metrics_merged.json: counts; hiệu số các bước | Khớp. Dự kiến 42,35 triệu và 0,23% là làm tròn; đề xuất thay phần dự kiến bằng kết quả thực tế và bỏ tỷ lệ làm tròn. Không cộng các bộ đếm lỗi giao nhau như tập rời nhau. |
| ch03_du_lieu, synthetic | 5/5; raw 202.032 → clean 196.492; trùng 2.032; event lạ 424 | m1_20261110_231427/generate_data_truth.json, cleaning_metrics.json; compare_truth logic và lần chạy đã ghi nhận | Khớp. Năm mục là số phép đối chiếu; ba mục dùng ngưỡng near, không phải tất cả bằng tuyệt đối. |
| ch03_du_lieu, 3.4 toàn tháng | 8 lát; bất biến clean bằng 0; 31 thư mục ngày | cleaning_metrics_merged.json: slices.length; slices/*profiling_clean.json; audit_5b_sources_20261111.json: full_clean_partition_dates.length | Khớp. Các số 42,4 triệu, 3,7–6,2 triệu/lát là làm tròn; nếu cần khoảng chính xác dùng min/max counts.raw từ các lát: 3683534–6158388. |
| ch03_du_lieu, OOM/thời gian | hai lần liên tiếp; executor 2 GB; máy 8 GB; 2.553 giây, khoảng 42,5 phút | note JSON gộp có OOM nhưng không có số lần; kb3_env.json executor_memory=2g thuộc lần benchmark; cleaning_seconds_total=2552.5 | CHƯA ĐỦ NGUỒN cho số lần OOM và cấu hình của lần lỗi. Thay thời gian bằng 2552.5 giây; bỏ số lần lỗi nếu chưa có log. Giữ 8 GB là cấu hình người dùng cung cấp. |
| ch03_du_lieu, hạn chế | một tháng 10/2019, 31,8% thiếu danh mục, 14,4% thiếu brand | profiling_raw.json: timestamp_min/max, nulls | Tháng khớp; tỷ lệ là làm tròn thêm. Đề xuất dùng số đếm 13515609 và 6113008 hoặc dẫn field/số nguồn. |
| ch06_kb3_kb5, bảng 6.1–6.2 và ingest | mọi dung lượng, lần đo, mean, speedup; 173.46 giây | kb3.csv từng dòng; ingest_log.csv: seconds | Khớp sau sửa M3; không sửa thêm. 3.869 là ratio đã làm tròn trong CSV nguồn, được giữ nguyên; không tính lại ratio từ mean đã làm tròn. |
| ch06_kb3_kb5, môi trường | 3 lần, 8 CPU, 4.8 GiB, executor/driver 2g, Spark 3.5.9 | kb3_env.json; code mem_total_gb tính theo GiB | Khớp; driver 2g của KB3 khác 1g lần M1, không gộp cấu hình. |
| ch06_kb3_kb5, bảng 6.3–6.4 và giải thích | tất cả counts/nulls/event counts/distinct approx, 7 invariants, 2552.5 giây, hiệu số | profiling_raw/clean.json; cleaning_metrics_merged.json; số key invariants bỏ all_pass | Khớp; distinct là xấp xỉ. Tổng giảm theo event_type 70592/28224/76 là hiệu số, không phải trùng riêng; văn bản đã ghi rõ. |
| phu_luc_schema, cây thư mục | 383 MB landing, 95 MB raw, 150 MB clean | audit_5b_sources_20261111.json: sizes | KHÔNG KHỚP theo đơn vị ghi trong tài liệu. Byte thực: landing 400957999, raw 98256658, clean 155044118, loại dotfiles. Đề xuất thay bằng byte chính xác và nói rõ cách cộng; không tự đổi đơn vị/làm tròn. |
| phu_luc_schema, schema/định dạng | 9 raw; 14 clean = 8 giữ + 6 thêm; thứ tự 1–14; category_id ví dụ 19 chữ số | audit_5b_sources JSON: raw_schema/clean_schema; audit_5b_sample3m/cleaning_schema.json | Khớp số cột và số chữ số ví dụ. Schema lúc ghi đặt event_date trước event_hour/day_of_week; đọc lại cột partition xuống cuối, tài liệu đã phân biệt đúng. |
| phu_luc_schema, hai dòng CSV và bảng ví dụ | IDs, giá 35.79/33.20/33.2; UUID, ngày/giờ 00:00:00 và 00:00:15, event_hour 0 | audit_5b_sources_20261111.json: csv_first_two_rows, raw_example_rows, clean_example_rows | Khớp các giá trị thật. 33.20 và 33.2 cùng giá trị số, là biểu diễn double, không phải làm tròn kết quả đo. Các chữ số trong UUID không phải chỉ số để cộng/so sánh. |
| phu_luc_schema, tỷ lệ unknown | toàn tháng 14,27%/31,82%, 6.043.456/13.475.214 dòng; tập nhỏ 14,5%/31,4% | profiling_clean.json: unknown_ratio; audit_5b_sample3m/profiling_clean.json: unknown_ratio | Số đếm khớp; tỷ lệ bị làm tròn thêm. Đề xuất dùng nguyên field brand=0.142703, cat_l1=0.318188 toàn tháng; 0.145106/0.314483 tập nhỏ, ghi rõ đây là tỷ lệ dạng thập phân. |
| phu_luc_schema, số kỹ thuật khác | 3 giá trị event_type, 2 cấp danh mục, seed 42, 1 file/mẫu, giờ 0–23, int khoảng 2,1 tỷ | samples_log.csv và m2 JSON xác nhận file/rows; seed trong jobs/make_sample.py; contract và kiểu dữ liệu | Là schema/tham số/giới hạn kiểu, không phải số thực nghiệm. Muốn viết giới hạn int chính xác dùng định nghĩa int32, không coi 2,1 tỷ là số từ dataset. |
| phu_luc_schema, phần trăm raw và suy luận parse | 31,8%/14,4%; nan/inf thành null | profiling_raw.json: nulls; M1 generator và raw profile chỉ kiểm chứng nan | Bỏ làm tròn tỷ lệ hoặc dùng counts; thu hẹp phát biểu parse về nan đã quan sát, không coi mọi cách viết inf đều đã được test. |
| ch08_bai_hoc_ai, dữ liệu/bộ nhớ | 8/5 GB, 8 lát, counts, 2552.5, M1 1g/2g/1/800 | 8/5 là ràng buộc người dùng; JSON gộp; M1 run_summary.json | Số liệu đúng nguồn; cấu hình người dùng không gán thành phép đo RAM mới. |
| ch08_bai_hoc_ai, null/NaN/cart | 218; 220; các 0; 68673/68670/chênh 3; cart 926516/898292/chênh 28224 | M1 truth/raw/clean; profiling toàn tháng; hiệu số counts | Khớp. Văn bản ghi đúng giới hạn suy luận, không khẳng định số trùng riêng cart. |
| ch08_bai_hoc_ai, số định danh | mục 8.1–8.5, phiên bản 1.0, tên job, M1/M2/KB3 | cấu trúc tài liệu và contract/source | Không phải chỉ số đo; có trong inventory để không bỏ sót chữ số. |
| m3_screenshot_checklist, số liệu bàn giao và JSON cần chụp | counts, mean KB3, ratios, 2552.5 và 28224 | profiling JSON, kb3.csv, cleaning_metrics_merged.json | Khớp; ảnh vẫn là việc chưa thực hiện, không phải minh chứng đã có. |
| m3_screenshot_checklist, lệnh/định danh | 9090/4040/4041/7077, cấu hình 1g/1/800, date stamp, mã 0, độ dài GUID 8, đường dẫn M1 | docker-compose và override, command block, M1 path | Port/tham số/giá trị dự kiến, không phải kết quả job mới. Block chụp ảnh chưa chạy trong lần audit. |

## Kết luận và việc sửa đề xuất

Không thấy lệch số đếm chính của profiling/cleaning, số KB3 sau sửa M3 hoặc giá trị ví dụ trong phụ lục. Có vấn đề về độ chính xác trình bày, dung lượng phụ lục, nguồn chi tiết bảng chéo và phát biểu số lần OOM. Việc kiểm tra đã thực hiện, nhưng không đánh dấu toàn bộ báo cáo là đã khớp nguồn.

Ưu tiên sửa: thay ba dung lượng phụ lục bằng byte snapshot; thay thời gian cleaning Ch.3 bằng 2552.5; bỏ số lần OOM chưa có log; bỏ/đánh dấu chờ nguồn các số bảng chéo; dùng nguyên tỷ lệ nguồn dạng thập phân hoặc chỉ giữ số đếm thay vì làm tròn thêm. Chưa áp dụng các đề xuất này trong bước 5b.

Để kiểm tra lại các chi tiết chưa có nguồn, bổ sung CSV đếm trực tiếp theo event_type/trạng thái lỗi và category depth từ một lần chạy có DATA_DIR mới, hoặc tìm log/JSON lịch sử tương ứng. Không chạy toàn tháng một lần trên máy hạn chế RAM. Đây là thiếu bằng chứng, không phải xác nhận những số đó sai.

## Xác nhận thủ công còn cần từ TV2

Người dùng cần đọc danh sách phát hiện và tự kiểm tra nguồn trước khi ghép báo cáo. Nội dung copy để ghi chú với TV4:

> TV2 đã rà số liệu toàn bộ Markdown. Các số đếm chính/KB3 khớp; còn đề xuất sửa độ chính xác tỷ lệ, thời gian Ch.3, dung lượng phụ lục và bỏ chi tiết chưa có nguồn JSON/CSV. Xem `docs/evidence/tv2/audit_5b_review_20261111.md`; chưa coi bản báo cáo là đã sạch mọi vấn đề. Các file audit mới hiện ở máy TV2, chưa commit/push.
