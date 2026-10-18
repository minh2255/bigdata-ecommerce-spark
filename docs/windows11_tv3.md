# Thiết lập Windows 11 và kiểm thử phần TV3

Tài liệu này lưu lịch sử thiết lập ban đầu. Gói TV3 đã được hoàn thiện tiếp tại
[docs/tv3_handoff.md](tv3_handoff.md): script có clean-only/ingest-clean, tự lưu log,
preflight có mã 4; --available hiện là alias ingest-clean. Bộ đối chiếu fixture
hiện giới hạn 10000 dòng; tập lớn dùng validate_cleaning.py, không nạp toàn bộ vào driver.
Các kiểm chứng lịch sử dưới đây không có nghĩa benchmark được chạy lại.

Repo được clone vào `D:/Desktop/BigData`. Nhánh làm việc
`tv3/windows11-spark-setup` được tạo từ `origin/main`, commit
`a86d31e796d7aeb7983a1d04b0b2cb9759ef3735`, trước khi sửa mã nguồn.
Thư mục ban đầu trống, không có thay đổi cục bộ cần di chuyển.
Không commit, push hoặc merge.

Đã đọc đầy đủ `D:/Desktop/BD_CaiDat.docx` (tài liệu hướng dẫn cài đặt mà yêu cầu
gọi là `3_Huong_dan_cai_dat.docx`), `BD_Project.docx` và `BD_PhanCong.docx`.
Áp dụng quy trình kỹ thuật trong tài liệu theo phạm vi người dùng yêu cầu;
không thực hiện hướng dẫn commit/PR/merge hay xóa dữ liệu trong tài liệu.

## Phạm vi TV3 và mã nguồn còn chờ

TV3 phụ trách `jobs/02_cleaning.py`, `scripts/run_pipeline.sh`, log từng bước
làm sạch, Ch.2.2, Ch.5 và phụ lục hướng dẫn chạy.
Lần thiết lập này hoàn thiện cleaning và pipeline; chưa soạn các chương báo cáo.

| Thành viên | Đã có / còn thiếu trên nhánh nền |
| --- | --- |
| TV1 | Có Dockerfile, Compose, ingest, benchmark và script thực nghiệm |
| TV2 | Thiếu generator, profiling, make_sample và data contract |
| TV3 | Đã bổ sung cleaning, pipeline có preflight, kiểm thử độc lập |
| TV4 | Thiếu aggregation, pandas_baseline và charts |

Generator dùng kiểm thử được trích từ tài liệu, lưu trong vùng `data/reports/`
bị Git bỏ qua. Nó không thay thế phần bàn giao của TV2. Biểu đồ TV3 chỉ biểu diễn
kiểm thử và benchmark; không thay thế biểu đồ KPI của TV4.

## Môi trường đã kiểm tra

Windows 11, RAM vật lý khoảng 16 GB, 20 logical CPU. Docker Desktop dùng WSL2,
Linux engine, tài nguyên engine khoảng 7.6 GiB / 20 CPU. WSL có distro
`docker-desktop` chạy version 2. Không cần cài thêm Ubuntu hoặc Python/Java/Spark
trên Windows. Không thay `.wslconfig`, không shutdown WSL.

Docker 29.8.2, Compose v5.6.0; `docker run --rm hello-world` thành công.
Dockerfile hiện có build được `apache/spark:3.5.9-java17-python3` với
Python 3.10.12, Java 17, Pandas 2.3.3, PyArrow 25.0.1, Matplotlib 3.10.9.
Không cần sửa Dockerfile hay Compose. Thêm `.dockerignore` để loại dữ liệu/Git
khỏi build context.

```powershell
Set-Location D:/Desktop/BigData
docker compose build spark-master
docker compose up -d --no-build
docker compose ps
Invoke-RestMethod http://localhost:8080/json/
```

Master UI `http://localhost:8080`, worker UI `http://localhost:8081` và `8082`.
Application UI `http://localhost:4040` chỉ có trong lúc job chạy.
Cả hai worker ALIVE, mỗi worker 2 core / 2048 MiB. Data Lake được mount vào
`/data` ở cả master và hai worker. Mã nguồn trên máy được mount vào `/opt/jobs`
và `/opt/scripts`, sửa Python/Bash không cần build lại image.

## Dữ liệu riêng và cách chạy

Tất cả kết quả lần này dùng **dữ liệu giả**, không dùng Kaggle. Các vùng test
nằm dưới `data/`, không ở `data/landing/` dùng cho dữ liệu thật. Mỗi lần chạy
chọn vùng mới để không ghi đè. Các tầng con vẫn là landing/raw/clean/agg/samples/reports.

```powershell
$env:DATA_DIR='/data/<vung-du-lieu-moi>'
# Đặt CSV vào D:/Desktop/BigData/data/<vung-du-lieu-moi>/landing/ trước.
& 'C:/Program Files/Git/bin/bash.exe' scripts/run_pipeline.sh --available
```

`--full` (mặc định) kiểm tra đủ job trước khi chạy. `--available` hiện là alias
`--ingest-clean`, chỉ chạy ingest và cleaning; không gọi profiling/KPI.
`--clean-only` chỉ chạy cleaning từ raw. Preflight chặn vùng đầu ra và báo cáo đã tồn tại,
CSV thiếu, hoặc file synthetic trộn với file tên khác. Kiểm tra tên chỉ là
hàng rào phụ; người chạy phải bảo đảm nguồn dữ liệu của mỗi vùng đồng nhất.

Ingest của TV1 vẫn dùng overwrite khi gọi trực tiếp; dùng pipeline có preflight
hoặc vùng DATA_DIR mới. Cleaning dùng errorifexists và không ghi đè báo cáo.

## Quy tắc cleaning và kiểm thử

Theo mục 5.3 của BD_Project, chờ TV2 xác nhận data contract cuối:

1. Bỏ dòng trùng hoàn toàn theo toàn bộ schema raw.
2. Chuyển thời gian sang timestamp, dùng múi giờ UTC và loại thời gian không đọc được.
3. Chỉ giữ view/cart/purchase.
4. Chỉ giữ giá hữu hạn > 0, user_id không null, session không null/rỗng.
5. Tách cat_l1/cat_l2; giá trị null/rỗng thành unknown.
6. Brand trim + lowercase; null/rỗng thành unknown.
7. Thêm event_date/event_hour/day_of_week, bỏ event_time; ghi Parquet phân vùng ngày.

Giá NaN/vô cực và session chỉ có khoảng trắng được loại rõ ràng; xử lý chuỗi
rỗng của brand/category được bổ sung so với mẫu. Cần TV2 xác nhận các quy tắc này.
Mỗi giai đoạn có count và cache MEMORY_AND_DISK; các count phục vụ KB5 có chi phí,
không coi tổng thời gian cleaning là benchmark thuần. Repartition theo event_date
trước khi ghi tránh tạo file cho mỗi cặp task/ngày trên dữ liệu nhỏ.
Với dữ liệu thật có ngày quá lớn cần đánh giá lại kích thước file và độ lệch tải.

`scripts/check_cleaning.py` tạo fixture 14 dòng và đối chiếu toàn bộ giá trị đầu ra
bằng Python/PyArrow độc lập với phép biến đổi Spark, kiểm tra cả số dòng từng bước,
UTC và phân vùng. Fixture có dòng trùng, thời gian lỗi, event lạ, giá 0/âm/null/NaN/Inf,
ID null, session null/trắng, brand/category thiếu. Kỳ vọng còn đúng 3 dòng.

```powershell
docker exec spark-master python3 /opt/scripts/check_cleaning.py fixture /data/<fixture-moi>
$env:DATA_DIR='/data/<fixture-moi>'
& 'C:/Program Files/Git/bin/bash.exe' scripts/run_pipeline.sh --available
docker exec spark-master python3 /opt/scripts/check_cleaning.py verify /data/<fixture-moi>
```

## Thực nghiệm khi đã có clean

```powershell
$env:DATA_DIR='/data/<vung-clean-da-kiem-tra>'
& 'C:/Program Files/Git/bin/bash.exe' scripts/run_benchmarks.sh all
docker exec spark-master python3 /opt/scripts/plot_tv3_checks.py /data/<vung-clean-da-kiem-tra>
```

KB1: 0.1/0.25/0.5/1.0, KB2: 1/2/4 core, KB6: 8/50/200 partition;
mặc định mỗi cấu hình 3 lần, tổng 30 ứng dụng tuần tự. CSV giữ schema của TV1,
JSONL bổ sung cấu hình shuffle/AQE, application ID, số dòng mẫu, thời điểm và phương pháp.
Đã sửa benchmark từ count số nhóm sang collect bảng tổng hợp nhỏ để buộc Spark
tính cả count và sum(price). Đây là tổng giá trên mọi event, không phải doanh thu mua hàng.
Thời gian tính từ action, gồm đọc dữ liệu nhưng không gồm khởi động Spark hoặc
khám phá schema. Không so trực tiếp với số đo Pandas khác phạm vi thời gian.

KB1 sample vẫn quét file clean đầy đủ, không phải 4 bộ dữ liệu vật lý khác nhau.
KB6 giữ AQE mặc định bật, số partition cấu hình có thể được Spark gộp lúc chạy.
Mẫu giả nhỏ dễ bị chi phí điều phối/I/O chi phối; không suy ra Spark thắng Pandas
hoặc tăng core chắc chắn nhanh hơn trên dữ liệu thật.
KB3 chưa có job riêng trong repo; phiên này đo hỗ trợ bằng script tạm trong
`data/reports/tv3_setup_20261018/benchmark_storage_support.py`: cùng schema cố định,
read + count, 3 lượt cho mỗi định dạng, đổi thứ tự đọc, giữ OS cache. Count có thể
đọc metadata hoặc dùng column pruning; không coi là quét đầy đủ các cột.
KB4 thiếu baseline/sample;
KB5 chính thức thiếu hai báo cáo profiling của TV2. Log và validation TV3 là
minh chứng hỗ trợ KB5, không được gọi là profiling hoàn chỉnh của TV2.

## Dữ liệu Kaggle và phần cần người dùng thực hiện

Đăng nhập [dataset Kaggle](https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store),
tải `2019-Oct.csv` (giải nén nếu cần) rồi đặt trong một vùng mới, ví dụ
`D:/Desktop/BigData/data/real_oct_run01/landing/2019-Oct.csv`.
Giữ nguyên các vùng synthetic cũ. Không cần gửi API token vào chat.
Sau khi có file, đặt DATA_DIR=/data/real_oct_run01 và chạy pipeline.
Chỉ chạy --full khi TV2/TV4 đã bàn giao đủ job.

Giữ cụm chạy để kiểm tra UI sau khi thiết lập. Khi không dùng nữa:
`docker compose down` (không xóa dữ liệu mount).
Minh chứng của phiên và kết quả cuối xem `docs/tv3_setup_results.md`.
Nếu dùng AI cho đồ án, ghi công cụ, mục đích, thay đổi và kết quả tự kiểm tra
vào phụ lục theo phân công nhóm.
