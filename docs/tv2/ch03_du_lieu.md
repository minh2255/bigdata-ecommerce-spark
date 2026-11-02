# Chương 3. Dữ liệu và yêu cầu

> Bản nháp TV2. Số trong mục 3.2 là kết quả quét toàn bộ file gốc (docs/data_contract.md, mục 7) và khớp với `profiling_raw.json` của 8 lát; số ở mục 3.3–3.4 lấy từ `cleaning_metrics.json` đã gộp (`data/real_oct_full/reports/`).

## 3.1 Nguồn dữ liệu

Đồ án dùng bộ dữ liệu công khai *eCommerce behavior data from multi category store* trên Kaggle, file `2019-Oct.csv` (hành vi người dùng của một cửa hàng trực tuyến đa ngành hàng trong tháng 10/2019). File có dung lượng 5.668.612.855 byte (khoảng 5,7 GB) và 42.448.764 dòng. Mỗi dòng là một sự kiện của một người dùng trên website; thời gian trải từ 2019-10-01 00:00:00 đến 2019-10-31 23:59:59 (UTC).

Bảng 3.1. Schema tầng raw (9 cột, đúng thứ tự trong file CSV)

| Cột | Kiểu | Ý nghĩa |
| --- | --- | --- |
| event_time | string | Thời điểm xảy ra sự kiện, dạng `2019-10-01 00:00:00 UTC` |
| event_type | string | Loại sự kiện: `view` (xem), `cart` (thêm giỏ), `purchase` (mua) |
| product_id | bigint | Mã sản phẩm |
| category_id | bigint | Mã danh mục |
| category_code | string | Danh mục dạng cây, ví dụ `electronics.smartphone` |
| brand | string | Thương hiệu |
| price | double | Giá sản phẩm |
| user_id | bigint | Mã người dùng |
| user_session | string | Mã phiên truy cập (UUID); một phiên có nhiều sự kiện |

Dòng ví dụ (đọc từ Parquet raw của lần chạy thử 3 triệu dòng) có trong Phụ lục A, `docs/tv2/phu_luc_schema.md`.

Dữ liệu được tổ chức thành các tầng landing → raw → clean → agg (xem mục 2.1.2). Tầng raw chỉ đổi định dạng CSV sang Parquet, không sửa nội dung, để luôn có thể làm sạch lại khi luật thay đổi.

## 3.2 Kết quả khảo sát chất lượng dữ liệu (profiling raw)

Nhóm không giả định dữ liệu "sạch". Trước khi viết luật làm sạch, TV2 quét toàn bộ 42.448.764 dòng và đếm từng loại bất thường. Kết quả:

Bảng 3.2. Các bất thường trên dữ liệu raw

| Hiện tượng | Số dòng | Tỷ lệ | Nhận xét |
| --- | --- | --- | --- |
| Dòng trùng cả 9 cột | 30.220 | 0,07% | Có thật; làm sai số đếm và doanh thu nếu để nguyên |
| `price = 0` | 68.673 | 0,16% | 68.523 dòng `view`, 150 dòng `cart`, **không có `purchase`** nên loại không làm lệch doanh thu |
| `user_session` rỗng | 2 | ≈ 0 | Cả hai là sự kiện `cart`; không gán được vào phiên nào |
| `category_code` null | 13.515.609 | 31,8% | Rất lớn; nếu loại dòng sẽ mất gần một phần ba dữ liệu |
| `brand` null | 6.113.008 | 14,4% | Như trên |
| `category_code` sâu 3 cấp | 36.242 | 0,09% | Clean chỉ giữ 2 cấp đầu |
| `price` âm, NaN, Infinity | 0 | 0 | Chưa gặp ở dữ liệu thật, nhưng luật vẫn giữ để chặn dữ liệu bẩn |
| `user_id` null hoặc ≤ 0 | 0 | 0 | Không cần luật ID dương |
| `user_session` không phải UUID | 0 | 0 | Không cần luật UUID |
| `event_time` sai định dạng | 0 | 0 | Mọi dòng parse được |

Thành phần sự kiện: `view` 40.779.399 (96,1%), `cart` 926.516 (2,2%), `purchase` 742.849 (1,7%). Tỷ lệ này cũng là cơ sở của phễu chuyển đổi mà TV4 tính ở Chương 5.

Hai điểm đáng chú ý khi đọc bảng:

1. **Bẩn có thật nhưng ít**: lỗi cần loại chiếm dưới 0,3% số dòng, nhưng nếu không loại thì dòng trùng và giá 0 vẫn làm sai số đếm sự kiện và giá trung bình.
2. **Thiếu nhiều nhưng không phải lỗi**: `category_code` và `brand` thiếu rất nhiều. Đây là đặc điểm của nguồn, không phải lỗi nhập; xử lý bằng nhãn `unknown` thay vì xóa dòng.

Một lưu ý cho cả nhóm khi đọc số liệu: tỷ lệ lỗi trong lần chạy thử 3 triệu dòng đầu (trùng 1.435 = 0,048%; giá ≤ 0 4.694 = 0,16%) khác nhẹ so với toàn tháng (0,07% và 0,16%) vì 3 triệu dòng đầu chỉ phủ 1–3/10. Do đó số liệu báo cáo cuối cùng lấy từ lần chạy toàn bộ.

## 3.3 Yêu cầu làm sạch

Từ khảo sát trên, nhóm rút ra yêu cầu: dữ liệu clean phải (a) không còn dòng trùng, (b) không còn giá không hợp lệ, (c) xác định được người dùng và phiên của mọi sự kiện, (d) giữ lại các dòng chỉ thiếu thông tin mô tả (brand, danh mục), và (e) có thêm các cột thời gian để tính KPI theo ngày/giờ.

Những yêu cầu này được chốt thành **data contract** (`docs/data_contract.md`, phiên bản 1.0). Contract là luật chung: TV2 định nghĩa, TV3 cài đặt trong `jobs/02_cleaning.py`, TV4 dùng khi tính KPI.

Bảng 3.3. Tóm tắt các quy tắc của contract (áp dụng theo đúng thứ tự)

| # | Quy tắc | Khi vi phạm |
| --- | --- | --- |
| 1 | Không có hai dòng giống hệt nhau ở cả 9 cột | Giữ 1 bản |
| 2 | `event_time` đúng dạng `yyyy-MM-dd HH:mm:ss UTC` | Bỏ dòng |
| 3 | `event_type` ∈ {view, cart, purchase} | Bỏ dòng |
| 4 | `price` hữu hạn và > 0; `user_id` khác null; `user_session` không rỗng | Bỏ dòng |
| 5 | Tách `category_code` thành `cat_l1`, `cat_l2` | Thiếu → `unknown`, giữ dòng |
| 6 | `brand` trim + chữ thường | Thiếu → `unknown`, giữ dòng |
| 7 | Thêm `event_ts`, `event_date`, `event_hour`, `day_of_week` | — |

Một số quyết định đáng giải thích, vì cả nhóm từng hỏi:

- **Dedup trước chuẩn hóa.** Trùng được xét trên dòng raw. Hệ quả là sau bước 5–6 vẫn có thể có hai dòng clean giống nhau (ví dụ chỉ khác `Samsung` và `samsung`). Đó là hành vi đúng; TV4 không dedup lại.
- **Mọi thời gian theo UTC**, đặt `spark.sql.session.timeZone = UTC` ở mọi job, để KPI theo giờ không lệch giữa các máy.
- **ID dương và UUID chỉ ghi nhận, không loại.** Dữ liệu thật không có vi phạm nào (bảng 3.2), nên thêm luật loại chỉ làm phức tạp mà không đổi kết quả. Nếu sau này profiling phát hiện vi phạm, contract nâng lên v1.1.
- **`unknown` là nhãn quy ước, không phải thương hiệu thật.** KPI xếp hạng brand/danh mục nên loại `unknown` hoặc báo riêng.

Dự kiến từ khảo sát: clean ≈ 42.448.764 − 30.220 − ~68.673 − 2 ≈ 42,35 triệu dòng. Con số thực tế: **42.349.872 dòng clean**, khớp dự kiến. Cụ thể: 42.448.764 → sau dedup 42.418.544 (loại 30.220 dòng trùng) → sau lọc giá 42.349.874 (loại 68.670 dòng giá ≤ 0; 3 dòng giá 0 còn lại đã nằm trong số dòng trùng) → sau lọc định danh 42.349.872 (loại 2 dòng `user_session` rỗng). Tổng loại 98.892 dòng (0,23%).

## 3.4 Cách kiểm chứng luật

Việc kiểm chứng có hai lớp, để không chỉ tin vào kết quả của chính job làm sạch:

1. **Dữ liệu giả có đáp án.** `scripts/generate_data.py` sinh dữ liệu cùng schema, cố ý chèn lỗi (trùng, giá 0/âm/NaN, `event_type` lạ, session trống, user trống…) và ghi số lượng thực tế vào `generate_data_truth.json`. `scripts/compare_truth.py` so số lỗi đã chèn với `cleaning_metrics.json`: kết quả đạt 5/5 mục (raw 202.032 → clean 196.492; bỏ đúng 2.032 dòng trùng và 424 `event_type` lạ).
2. **Dữ liệu thật, hai lần quét độc lập.** Một lần quét toàn bộ để chọn luật (bảng 3.2); một lần `01_profiling.py` trên raw và clean để kiểm tra các bất biến của clean (không còn trùng, giá > 0, không null ở các cột bắt buộc, `event_hour` ∈ [0, 23], ngày nằm trong 1–31/10/2019). Job thoát với mã 1 nếu một bất biến sai.

Kết quả thử trên 3 triệu dòng đầu: raw 3.000.000 → sau dedup 2.998.565 → clean 2.993.871 (loại 1.435 dòng trùng và 4.694 dòng giá ≤ 0); số liệu profiling khớp log cleaning, và tầng clean có 0 dòng trùng, 0 giá ≤ 0. Kết quả cho toàn bộ 42,4 triệu dòng như ở mục 3.3: số loại bỏ trùng khớp từng con số của lần quét ban đầu (30.220 dòng trùng, 68.673 dòng giá ≤ 0, 2 session rỗng), và cả 8 lát đều đạt mọi bất biến của clean (0 dòng trùng, 0 giá ≤ 0).

**Lưu ý phương pháp.** Chạy cleaning một lần trên 42,4 triệu dòng làm executor (2 GB) hết bộ nhớ trên máy 8 GB, hai lần liên tiếp. Nhóm chia raw thành 8 lát theo ngày (1–4, 5–8, …, 29–31; 3,7–6,2 triệu dòng mỗi lát), chạy nguyên `02_cleaning.py` cho từng lát rồi gộp 31 thư mục `event_date`. Cách chia này không làm sai dedup vì hai dòng trùng có cùng `event_time` nên luôn nằm trong cùng một lát. Tổng thời gian cleaning 8 lát là 2.553 giây (≈ 42,5 phút).

## 3.5 Hạn chế của dữ liệu

- Chỉ có một tháng (10/2019), nên không nhận định được tính mùa vụ.
- Không có thông tin người dùng (tuổi, vùng) hay trạng thái đơn hàng (hủy, hoàn); `purchase` được coi là giao dịch thành công.
- 31,8% sự kiện không có danh mục và 14,4% không có brand, nên KPI theo brand/danh mục chỉ phản ánh phần dữ liệu có nhãn.
- Dữ liệu một tháng đã bị công bố sẵn; không có cách kiểm tra lại với hệ thống nguồn để biết một dòng trùng là lỗi ghi hay hai hành vi thật giống hệt trong cùng một giây.
