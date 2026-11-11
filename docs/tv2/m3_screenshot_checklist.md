# M3 — Checklist chụp minh chứng cho TV2

Ảnh do người dùng tự chụp. Chưa đánh dấu hoàn thành khi chưa có file ảnh thật.
Lưu ảnh vào `docs/evidence/tv2/`; tránh đưa dữ liệu hoặc token vào Git.

## 1. Master UI

- [ ] Mở `http://localhost:9090`, kiểm tra hai worker ALIVE rồi chụp phần URL, Alive Workers và danh sách worker.
- [ ] Lưu `m3_master_9090_2workers.png`.
- Nếu cụm đang dừng: từ gốc repo chạy `docker compose up -d --no-build`, chờ worker đăng ký rồi kiểm tra lại.

## 2. Spark UI khi profiling đang chạy

Dùng raw synthetic nhỏ đã chạy M1, không dùng raw toàn tháng cho lần chụp ảnh.
Lệnh dưới sao chép raw vào DATA_DIR mới, không ghi đè vùng cũ. Chạy trong PowerShell từ gốc repo.
Một executor và tắt AQE với nhiều shuffle partition giúp có thêm thời gian quan sát;
đây là cấu hình dành cho chụp minh chứng, không dùng thời gian này thay benchmark KB3.

Chuẩn bị tab `http://localhost:4040` trước; nếu chưa có job thì tab chưa kết nối là bình thường.
Sau khi lệnh log báo SparkUI ở cổng 4040, refresh tab và chọn Jobs/Stages.

```powershell
$repo = (Get-Location).Path
$source = Join-Path $repo 'data/synthetic_tv2_m1_20261110_231427'
if (!(Test-Path -LiteralPath "$source/raw/events")) { throw 'Thieu raw synthetic M1' }
$runName = 'synthetic_tv2_capture_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + [guid]::NewGuid().ToString('N').Substring(0,8)
$target = Join-Path $repo "data/$runName"
if (Test-Path -LiteralPath $target) { throw 'DATA_DIR da ton tai' }
New-Item -ItemType Directory -Path $target -ErrorAction Stop | Out-Null
Copy-Item -LiteralPath "$source/raw" -Destination "$target/raw" -Recurse -ErrorAction Stop
$captureDataDir = "/data/$runName"
Write-Host "DATA_DIR=$captureDataDir"
docker exec -e "DATA_DIR=$captureDataDir" -e DATA_KIND=synthetic spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --driver-memory 1g --executor-memory 1g --conf spark.cores.max=1 --conf spark.executor.cores=1 --conf spark.sql.shuffle.partitions=800 --conf spark.sql.adaptive.enabled=false /opt/jobs/01_profiling.py raw
if ($LASTEXITCODE -ne 0) { throw "Profiling exit=$LASTEXITCODE; giu DATA_DIR de kiem tra" }
Write-Host "JSON moi: $target/reports/profiling_raw.json"
```

- [ ] Chụp khi Jobs/Stages đang có task chạy, thấy tên app `01_profiling_raw` và URL cổng 4040; lưu `m3_spark_4040_profiling_raw_synthetic.png`.
- [ ] Ghi DATA_DIR mới vào ghi chú ảnh để phân biệt với lần chạy toàn tháng.
- Không đảm bảo thời gian job cố định. Nếu bỏ lỡ, chạy lại cả block để có DATA_DIR mới; không chạy lại trên DATA_DIR đã có report.
- Không chạy đồng thời với job Spark khác vì UI có thể chuyển sang 4041 hoặc tranh RAM.

## 3. Hai JSON toàn tháng

Mở các bản evidence trong editor, bật hiển thị đường dẫn file. Có thể dùng tìm kiếm để đưa các trường cần chụp vào khung nhìn.

- [ ] `docs/evidence/tv2/profiling_raw.json`: chụp rows 42.448.764, duplicate_rows 30.220; lưu `m3_fullmonth_profiling_raw_rows.png`.
- [ ] Cùng file raw: chụp price_le_0 68.673; lưu `m3_fullmonth_profiling_raw_price.png`.
- [ ] `docs/evidence/tv2/profiling_clean.json`: chụp rows 42.349.872, duplicate_rows `0` và giá <= 0 bằng `0` (có thể chụp hai ảnh); đặt `m3_fullmonth_profiling_clean_rows.png`, `m3_fullmonth_profiling_clean_price.png`.
- [ ] Chụp khối invariants có `all_pass=true`; lưu `m3_fullmonth_profiling_clean_invariants.png`.

Các JSON toàn tháng là bằng chứng lịch sử. Ảnh UI synthetic mới không được ghi chú là job toàn tháng.

## 4. Cây thư mục

- [ ] Mở `docs/evidence/tv2/landing_raw_tree_20261110.txt`, chụp landing CSV và raw/events Parquet; lưu `m3_landing_raw_tree.png`.
- File text được tạo từ file thật, gồm kích thước byte. Tổng dùng cho KB3 loại dotfiles CRC, đã ghi rõ trong text và audit.

## 5. Tin bàn giao TV4

> TV2 gửi M3/KB3/KB5. KB3 lấy trực tiếp `docs/evidence/tv2/kb3.csv`: CSV/Parquet 5.668.612.855/1.465.175.946 byte, tỷ số 3,87×; mean count 39,7/2,2 giây (17,7×), mean sum(price) 56,3/3,2 giây (17,7×). Cấu hình lần đo ở `kb3_env.json`, driver 2g; đừng nhầm với driver 1g của M1.
>
> KB5 có CSV sẵn để vẽ: `docs/evidence/tv2/m3_kb5_chart_data.csv`, từng dòng kèm file và JSON field nguồn. Raw 42.448.764 → dedup 42.418.544 → sau giá 42.349.874 → clean 42.349.872. Raw trùng 30.220, giá <= 0 là 68.673, session null 2; clean đều 0, all_pass=true. Cleaning tổng 2.552,5 giây ≈ 42,5 phút.
>
> Ch.6 đã đối chiếu với nguồn: `docs/tv2/ch06_kb3_kb5.md`. Audit: `docs/evidence/tv2/m3_source_audit_20261110.md`. Không gắn số cart giảm 28.224 thành số trùng riêng của cart; không kết luận doanh thu không đổi sau dedup purchase. Nhãn brand/category cần phân biệt null raw và unknown clean.
>
> Cây thư mục thật đã có ở `docs/evidence/tv2/landing_raw_tree_20261110.txt`. Các file M3 mới và sửa Ch.6 hiện ở máy TV2, chưa commit/push. Ảnh UI/JSON đang chờ TV2 tự chụp theo checklist; chưa bàn giao ảnh.

- [ ] Người dùng gửi tin trên cho TV4.
- [ ] Chỉ đánh dấu đủ minh chứng ảnh sau khi kiểm tra ảnh đã lưu và đọc được.
