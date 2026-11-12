# Chương 3. Dữ liệu và yêu cầu

> Số liệu toàn tháng lấy từ `profiling_raw.json`, `profiling_clean.json` và `cleaning_metrics_merged.json` trong `docs/evidence/tv2/`. Số liệu tập thử lấy từ `docs/evidence/tv2/audit_5b_sample3m/`. Các tỷ lệ dạng thập phân được giữ nguyên độ chính xác của JSON nguồn.

## 3.1 Nguồn dữ liệu

Đồ án dùng bộ dữ liệu công khai *eCommerce behavior data from multi category store* trên Kaggle, file `2019-Oct.csv` (hành vi người dùng của một cửa hàng trực tuyến đa ngành hàng trong tháng 10/2019). File có dung lượng 5.668.612.855 byte và 42.448.764 dòng. Mỗi dòng là một sự kiện của một người dùng trên website; thời gian trải từ 2019-10-01 00:00:00 đến 2019-10-31 23:59:59 (UTC).

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

| Hiện tượng | Số dòng | Nhận xét |
| --- | --- | --- |
| Dòng trùng cả 9 cột | 30.220 | `duplicate_ratio = 0.000712`; cần dedup trước khi tính KPI |
| `price = 0` | 68.673 | Cũng là toàn bộ nhóm `price ≤ 0`; `price_le_0_ratio = 0.001618` |
| `user_session` thiếu (ô rỗng trong CSV, đọc thành null) | 2 | Không gán được vào phiên nào |
| `category_code` null | 13.515.609 | Giữ dòng, gán `unknown` ở các cột danh mục chuẩn hóa |
| `brand` null | 6.113.008 | Giữ dòng, chuẩn hóa thành `unknown` |
| `price` âm, NaN, Infinity | 0 | Mỗi bộ đếm đều bằng 0; luật vẫn kiểm tra các trường hợp này |
| `user_id` null hoặc ≤ 0 | 0 | Hai bộ đếm đều bằng 0; contract chỉ yêu cầu khác null |
| `user_session` không phải UUID | 0 | Profiling chỉ ghi nhận, contract không lọc theo UUID |
| `event_time` sai định dạng hoặc không parse được | 0 | Hai bộ đếm đều bằng 0 |

Thành phần sự kiện theo `event_type_counts`: `view` 40.779.399, `cart` 926.516, `purchase` 742.849. Đây là số sự kiện; phễu chuyển đổi cần đếm phiên phân biệt theo định nghĩa KPI, không lấy tỷ lệ số sự kiện thay cho tỷ lệ chuyển đổi phiên. Bộ evidence hiện chưa có bảng chéo lỗi theo `event_type` hoặc thống kê độ sâu danh mục, nên không dùng các chi tiết đó để kết luận về doanh thu hay số dòng trùng riêng của từng loại sự kiện.

Hai điểm đáng chú ý khi đọc bảng:

1. **Lỗi cần được xử lý theo thứ tự**: cleaning loại tổng cộng 98.892 dòng; các nhóm lỗi có thể giao nhau nên không cộng trực tiếp các bộ đếm raw.
2. **Thiếu nhiều nhưng không phải lỗi**: `category_code` và `brand` thiếu rất nhiều. Đây là đặc điểm của nguồn, không phải lỗi nhập; xử lý bằng nhãn `unknown` thay vì xóa dòng.

Một lưu ý cho cả nhóm khi đọc số liệu: lần chạy thử 3.000.000 dòng đầu có 1.435 dòng trùng (`duplicate_ratio = 0.000478`) và 4.694 dòng giá ≤ 0 (`price_le_0_ratio = 0.001565`), khác với toàn tháng (`0.000712` và `0.001618`). Tập thử chỉ phủ từ 2019-10-01 00:00:00 đến 2019-10-03 12:12:19 UTC. Do đó số liệu báo cáo toàn tháng lấy từ lần chạy toàn bộ.

## 3.3 Yêu cầu làm sạch

Từ khảo sát trên, nhóm rút ra yêu cầu: (a) loại các bản trùng của raw trước chuẩn hóa, (b) không còn giá không hợp lệ, (c) xác định được người dùng và phiên của mọi sự kiện, (d) giữ lại các dòng chỉ thiếu thông tin mô tả (brand, danh mục), và (e) có thêm các cột thời gian để tính KPI theo ngày/giờ.

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

Kết quả thực tế là **42.349.872 dòng clean**. Cụ thể: 42.448.764 → sau dedup 42.418.544 (loại 30.220 dòng trùng) → sau lọc giá 42.349.874 (loại 68.670 dòng giá ≤ 0; chênh 3 dòng so với bộ đếm raw do dedup trước đó) → sau lọc định danh 42.349.872 (loại 2 dòng `user_session` thiếu). Các bước lọc thời gian và loại sự kiện không loại thêm dòng. Tổng loại 98.892 dòng.

## 3.4 Cách kiểm chứng luật

Việc kiểm chứng có hai lớp, để không chỉ tin vào kết quả của chính job làm sạch:

1. **Dữ liệu giả có đáp án.** `scripts/generate_data.py` sinh dữ liệu cùng schema, cố ý chèn lỗi (trùng, giá 0/âm/NaN, `event_type` lạ, session trống, user trống…) và ghi số lượng thực tế vào `generate_data_truth.json`. `scripts/compare_truth.py` so với `cleaning_metrics.json`: đạt 5/5 mục; hai mục raw và trùng yêu cầu bằng tuyệt đối, ba mục còn lại dùng ngưỡng sai lệch cho phép vì lỗi có thể giao nhau. Lần M1 có raw 202.032 → clean 196.492; loại 2.032 dòng trùng và 424 `event_type` lạ.
2. **Dữ liệu thật, đối chiếu profiling với cleaning.** `01_profiling.py` đếm riêng trên raw và clean; so số đếm với các bước cleaning. JSON clean toàn tháng ghi nhận 7 bất biến đều đạt (`invariants.all_pass = true`) và 0 dòng trùng. Số dòng trùng được báo riêng, không phải điều kiện cấm trùng sau chuẩn hóa của contract. Kiểm tra phạm vi ngày so với raw chỉ được thêm khi có `profiling_raw.json` cùng DATA_DIR; không gán kiểm tra này cho JSON toàn tháng vốn chỉ có 7 bất biến. Job thoát mã 1 nếu bất biến được kiểm tra bị sai.

Kết quả thử trên 3.000.000 dòng đầu: raw 3.000.000 → sau dedup 2.998.565 → clean 2.993.871 (loại 1.435 dòng trùng và 4.694 dòng giá ≤ 0); profiling khớp cleaning, clean có 0 dòng trùng và 0 giá ≤ 0. Trên toàn bộ 42.448.764 dòng, raw có 30.220 dòng trùng, 68.673 dòng giá ≤ 0 và 2 session thiếu; cleaning lần lượt loại 30.220, 68.670 và 2 dòng ở các bước tương ứng. Cả 8 lát đều có `invariants.all_pass = true`, 0 dòng trùng và 0 giá ≤ 0 trong profiling clean.

**Lưu ý phương pháp.** Theo ghi chú trong `cleaning_metrics_merged.json`, cleaning toàn bộ 42.448.764 dòng trong một lần gặp lỗi hết bộ nhớ executor trên máy RAM 8 GB. Bộ nguồn này không xác nhận số lần lỗi, mã lỗi hoặc cấu hình executor của lần lỗi. Nhóm chia raw thành 8 lát theo ngày (1–4, 5–8, …, 29–31), từ 3.683.534 đến 6.158.388 dòng mỗi lát; chạy nguyên `02_cleaning.py` từng lát rồi gộp 31 thư mục `event_date`. Dedup được bảo toàn vì các bản trùng có cùng `event_time`, các lát không chồng lấn và bao phủ toàn tháng. Tổng thời gian cleaning lấy nguyên trường `cleaning_seconds_total`: **2552.5 giây**.

## 3.5 Hạn chế của dữ liệu

- Chỉ có một tháng (10/2019), nên không nhận định được tính mùa vụ.
- Không có thông tin người dùng (tuổi, vùng) hay trạng thái đơn hàng (hủy, hoàn); `purchase` được coi là giao dịch thành công.
- Raw có 13.515.609 dòng thiếu `category_code` và 6.113.008 dòng thiếu `brand`; khi loại nhóm `unknown` khỏi xếp hạng, KPI theo brand/danh mục chỉ phản ánh phần dữ liệu có nhãn.
- Dữ liệu một tháng đã bị công bố sẵn; không có cách kiểm tra lại với hệ thống nguồn để biết một dòng trùng là lỗi ghi hay hai hành vi thật giống hệt trong cùng một giây.
