# Đối chiếu nguồn KB3/KB5 — 10/11/2026

Phạm vi: `docs/tv2/ch06_kb3_kb5.md`, không phải kiểm toán toàn bộ Markdown của bước 5b.
Không chạy lại benchmark hoặc job toàn tháng.

## KB3

- `kb3.csv`: dung lượng CSV `5668612855` byte, Parquet `1465175946` byte; size_ratio `3.869`.
- Giữ nguyên từng lần đo và mean trong bảng Ch.6, bỏ làm tròn thêm ở bảng và phần diễn giải.
- Mean count CSV/Parquet: `39.683` / `2.247` giây; speedup nguồn `17.663`.
- Mean sum(price) CSV/Parquet: `56.333` / `3.18` giây; speedup nguồn `17.717`.
- Mean/speedup trong CSV được job làm tròn ở độ chính xác nguồn; dùng dòng nguồn khi vẽ biểu đồ.
- `kb3_env.json`: repeats `3`, CPU trong container `8`, RAM trường nguồn `4.8`, Spark `3.5.9`, executor `2g`, driver `2g`, default_parallelism `2`. Đây là cấu hình lần benchmark cũ, khác driver `1g` của test M1 mới.
- `ingest_log.csv`: `42448764` dòng, `173.46` giây; đã thay giá trị làm tròn `173,5` trong Ch.6.
- RAM `4.8` trong JSON được code tính từ /proc/meminfo bằng phép chia 1024, nên về đơn vị là GiB dù tên trường là `mem_total_gb_in_container`. Không đổi JSON lịch sử.

## Dung lượng hiện tại

`landing_raw_tree_20261110.txt` liệt kê file thật và kích thước logic bằng stat.
Tổng raw tính cả dotfiles là `1476623078` byte; loại dotfiles còn `1465175946` byte, khớp KB3.
Job KB3 bỏ tên file bắt đầu bằng dấu chấm khi cộng dung lượng. Không so trực tiếp với du nếu du báo dung lượng cấp phát hoặc cộng cả CRC.

## KB5

- Các bước counts và tổng output các lát khớp nguồn JSON: raw `42448764`, dedup `42418544`, sau giá `42349874`, clean `42349872`.
- Raw trùng `30220`, giá <= 0 `68673`, session null `2`; clean các mục này đều `0`, `all_pass=true`.
- Tổng giảm `98892` là hiệu số raw và clean; giá bị loại sau dedup `68670`, chênh raw `3` dòng do giao với dedup.
- Thời gian cleaning lấy nguyên trường `cleaning_seconds_total=2552.5`; không thay bằng tổng tính lại từ các thời gian đã làm tròn của từng lát.
- Bỏ các phần trăm làm tròn thêm ở Ch.6; số đếm giữ nguyên. `m3_kb5_chart_data.csv` có cột nguồn và JSON field cho từng số.
- Bảng brand/category so sánh null ở raw với unknown ở clean; đây là hai trạng thái khác nhau, cần nhãn rõ trên biểu đồ. `category_code` gốc có thể vẫn null ở clean.

## Diễn giải đã sửa

- Không khẳng định doanh thu không đổi khi loại purchase trùng; chưa có tổng doanh thu trước/sau trong JSON/CSV nguồn này.
- `cart` giảm `28224` là tổng giảm qua mọi bước, không phải số trùng riêng của cart. Bỏ kết luận định lượng trùng theo event_type chưa có bảng chéo nguồn.
- Bỏ số lần thử OOM và mã lỗi chưa được JSON chứng minh; giữ việc hết bộ nhớ và chia lát theo note trong metrics.
- Đánh dấu cache và đường thực thi count bằng metadata là khả năng/giới hạn cần kiểm chứng, không coi thời gian đo là bằng chứng physical plan.

## Còn cần người dùng làm

Ảnh Spark UI/Master UI/JSON và gửi số liệu cho TV4 chưa được thực hiện.
Xem `docs/tv2/m3_screenshot_checklist.md`.
