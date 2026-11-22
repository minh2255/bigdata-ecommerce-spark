# Chương 6 (phần TV1). Thực nghiệm KB1, KB2 và KB6

> Số liệu lấy từ `docs/evidence/tv1/benchmark_final.csv` (42 lần đo) và `benchmark_runs.jsonl` (cấu hình từng lần chạy),
> chạy ngày 18/11/2026 trên dữ liệu Kaggle thật, tầng clean 42.349.872 dòng. Biểu đồ: `docs/evidence/tv1/kb*.png`
> (do `scripts/plot_tv1_benchmarks.py` vẽ từ chính CSV đó).

## 6.0 Phương pháp chung

Một truy vấn chuẩn do `jobs/04_benchmark.py` thực hiện: đọc `clean/events`, `groupBy(event_date, event_type)` tính
`count(*)` và `sum(price)`, rồi `collect()` bảng kết quả (tối đa 93 nhóm) về driver để Spark phải tính cả hai phép tổng hợp.
Thời gian chỉ đo phần action, không gồm khởi động Spark và đọc schema. Mỗi cấu hình chạy **3 lần**, mỗi lần là một ứng dụng
Spark riêng (3 `application_id` khác nhau trong JSONL). Cụm: 1 master + 2 worker (2 core, 2 GB mỗi worker), driver 2 GB,
`spark.sql.shuffle.partitions=200` và AQE bật, trừ khi KB đó thay đổi tham số.
`sum(price)` ở đây cộng giá của mọi loại sự kiện, không phải doanh thu nghiệp vụ.

Bảng dưới là trung bình, trung vị và độ lệch chuẩn của 3 lần; **với n = 3 độ lệch chuẩn chỉ để tham khảo và chưa làm kiểm định thống kê**.
Lần đầu của vài cấu hình chậm bất thường, nên có kèm trung vị.

## 6.1 KB1 – Ảnh hưởng của kích thước dữ liệu

**Mục tiêu.** Xem thời gian chạy tăng thế nào khi dữ liệu tăng. Hai cách cắt dữ liệu được đo.

**Cách 1 – `df.sample(fraction, seed=42)`** (nhãn `size`). Lấy ngẫu nhiên theo dòng.

| Tỷ lệ | Số dòng | TB (s) | Trung vị (s) | Độ lệch chuẩn (s) | 3 lần đo (s) |
|---|---|---|---|---|---|
| 0,10 | 4.238.351 | 60.11 | 52.56 | 20.63 | 83.46; 44.32; 52.56 |
| 0,25 | 10.591.674 | 46.96 | 45.09 | 9.64 | 57.39; 45.09; 38.39 |
| 0,50 | 21.176.258 | 47.02 | 47.13 | 2.47 | 47.13; 49.43; 44.50 |
| 1,00 | 42.349.872 | 44.79 | 45.50 | 3.15 | 41.35; 47.53; 45.50 |

**Cách 2 – lọc theo ngày** (nhãn `sizedays`, `BENCH_MODE=days`: giữ các ngày 1..⌈31×tỷ lệ⌉).

| Tỷ lệ | Số dòng | Số nhóm | TB (s) | Trung vị (s) | Độ lệch chuẩn (s) |
|---|---|---|---|---|---|
| 0,10 | 3.555.889 | 9 | 21.25 | 20.87 | 2.00 |
| 0,25 | 10.177.062 | 24 | 22.61 | 23.60 | 3.39 |
| 0,50 | 21.909.983 | 48 | 27.48 | 25.70 | 4.53 |
| 1,00 | 42.349.872 | 93 | 36.87 | 35.07 | 6.57 |

**Nhận xét.**
1. Với `sample()`, thời gian **gần như không đổi** (khoảng 45–47 s từ 25% đến 100% dữ liệu) dù số dòng tăng 4 lần. Điều này
   không có nghĩa Spark "mở rộng hoàn hảo": `sample()` lấy theo dòng nên vẫn phải đọc gần như toàn bộ file Parquet, chỉ bớt phần tổng hợp.
   Đây là cách giải thích hợp lý, chưa kiểm chứng riêng bằng Spark UI. Giá trị 60 s ở tỷ lệ 0,10 chủ yếu do lần đầu 83.46 s (có thể là cache hệ điều hành lạnh, chưa kiểm chứng); hai lần còn lại là 44.32 và 52.56 s, ngang các mức khác.
2. Khi lọc theo ngày, Spark chỉ cần đọc các thư mục `event_date` cần thiết (nhờ phân vùng của tầng clean), nên thời gian tăng theo dữ liệu:
   từ 21.25 s lên 36.87 s, tức khoảng **1.7×** khi số dòng tăng khoảng **11.9×**. Thời gian tăng chậm hơn dữ liệu nhiều, phù hợp với việc có chi phí cố định
   (lên lịch job, shuffle, khởi tạo task) chiếm phần lớn khi dữ liệu nhỏ.
3. Hạn chế: bốn kích thước là các lát của cùng một bộ dữ liệu chứ không phải bốn bộ độc lập; cách lọc theo ngày giữ các ngày đầu
   tháng nên không đại diện đều cho cả tháng; n = 3 và độ lệch lớn ở các mức nhỏ.

## 6.2 KB2 – Ảnh hưởng của số core

**Cách đo.** Toàn bộ dữ liệu (tỷ lệ 1,0), giới hạn `--total-executor-cores` bằng 1, 2, 4 (cụm có tối đa 4 core: 2 worker × 2).

| Số core | TB (s) | Trung vị (s) | Độ lệch chuẩn (s) | 3 lần đo (s) | Tăng tốc so với 1 core (theo TB) |
|---|---|---|---|---|---|
| 1 | 54.92 | 47.14 | 15.19 | 72.42; 47.14; 45.20 | 1.00× |
| 2 | 36.02 | 36.89 | 4.28 | 31.37; 39.79; 36.89 | 1.52× |
| 4 | 38.13 | 38.27 | 1.28 | 39.33; 36.78; 38.27 | 1.44× |

**Nhận xét.**
1. Từ 1 lên 2 core thời gian giảm (theo trung bình 1.52×, theo trung vị 1.28×); đây là mức tăng tốc **dưới tuyến tính** (lý tưởng là 2×).
   Lần đo đầu của 1 core (72.42 s) làm trung bình cao; nếu chỉ lấy hai lần sau (47.14; 45.20) thì tăng tốc còn khoảng 1.26×.
2. Từ 2 lên 4 core **không cải thiện** (36.02 → 38.13 s; chênh lệch nằm trong biên dao động của các lần đo).
   Nguyên nhân chưa được kiểm chứng. Các giả thuyết hợp lý: bốn core dùng chung một ổ đĩa và RAM của một máy
   (truy vấn chủ yếu đọc Parquet nên có thể nghẽn I/O), RAM chỉ 2 GB mỗi worker, và chi phí điều phối; cần Spark UI hoặc đo I/O mới khẳng định được.
3. Kết luận thận trọng: trên máy này, thêm core giúp tới 2 core rồi bão hòa. Không suy ra được hành vi trên cụm nhiều máy.

## 6.3 KB6 – Ảnh hưởng của `spark.sql.shuffle.partitions`

**Cách đo.** Toàn bộ dữ liệu, dùng toàn bộ core của cụm (4 core), đặt `--conf spark.sql.shuffle.partitions` bằng 8, 50, 200 (200 là mặc định của Spark).

| Số partition | TB (s) | Trung vị (s) | Độ lệch chuẩn (s) | 3 lần đo (s) |
|---|---|---|---|---|
| 8 | 49.52 | 51.20 | 10.02 | 51.20; 38.77; 58.59 |
| 50 | 39.35 | 39.24 | 1.89 | 39.24; 41.29; 37.52 |
| 200 | 39.76 | 38.38 | 4.36 | 44.64; 36.26; 38.38 |

**Nhận xét.**
1. 50 và 200 partition cho kết quả gần như nhau (39.35 và 39.76 s). 8 partition chậm hơn khoảng 25% theo trung bình
   (49.52 s) và dao động mạnh nhất, nhưng khoảng giá trị của nó (38.77–58.59 s) **chồng lên** khoảng của hai cấu hình kia,
   nên với 3 lần đo chưa đủ để khẳng định 8 partition thật sự chậm hơn.
2. Hướng giải thích hợp lý (chưa kiểm chứng bằng Spark UI): ít partition thì mỗi task xử lý nhiều dữ liệu hơn và khó cân bằng tải giữa 4 core; nhiều partition hơn tăng chi phí
   lên lịch nhưng ở đây chưa thấy ảnh hưởng.
3. **AQE bật** (`aqe_enabled=true` trong JSONL), nên Spark có thể gộp partition khi chạy; con số cấu hình không đồng nghĩa số partition thực tế của stage.
   Truy vấn chỉ có hai khóa nhóm (tối đa 93 nhóm) nên lượng dữ liệu shuffle nhỏ, làm ảnh hưởng của tham số này có thể thấp hơn so với truy vấn nặng shuffle.

## 6.4 Tổng hợp và giới hạn

| Thực nghiệm | Kết quả chính | Mức tin cậy |
|---|---|---|
| KB1 (`sample`) | thời gian gần như phẳng, nhiều khả năng vì vẫn quét toàn bộ file | trung bình; lần đầu có thể là cache lạnh |
| KB1 (lọc ngày) | tăng 1.7× khi dữ liệu tăng 11.9× | khá; xu hướng rõ nhưng n = 3 |
| KB2 | 1→2 core nhanh hơn 1.28–1.52×; 2→4 không đổi | trung bình; chưa xác định nguyên nhân bão hòa |
| KB6 | 50 ≈ 200 partition; 8 có thể chậm hơn | thấp; khoảng dao động chồng nhau |

Giới hạn chung: mỗi cấu hình chỉ 3 lần, dao động lớn (độ lệch chuẩn tới 15–20 s ở vài cấu hình); chạy trên một máy với cụm giả lập nên
các worker tranh chấp tài nguyên; không xóa cache hệ điều hành giữa các lần; truy vấn chuẩn chỉ là một phép `groupBy` đơn giản.
Các kết luận chỉ áp dụng cho truy vấn, dữ liệu và cấu hình này. Số liệu cũ trên synthetic nằm ở
`benchmark_kb1_kb2_kb6_v1.csv` và không dùng trong chương này (file đó cần TV1 xác nhận nguồn gốc nếu muốn trích dẫn).
