# Kịch bản demo TV2 — 3 phút

Mục tiêu: giới thiệu dataset → mở contract → chạy profiling raw trên synthetic nhỏ → đọc lỗi trùng/null/giá → trình chiếu bằng chứng toàn tháng.

Minh chứng toàn tháng dùng hai file JSON đã lưu trong `docs/evidence/tv2/`; có thể trình chiếu trực tiếp hoặc dùng ảnh theo [checklist M3](m3_screenshot_checklist.md).

## Chuẩn bị trước khi bấm giờ

1. Mở editor tại gốc repo, tăng cỡ chữ cho người xem đọc được.
2. Mở sẵn `docs/data_contract.md`, JSON synthetic M1 và hai JSON toàn tháng trong `docs/evidence/tv2/`. Chọn trước các trường cần nói; không cuộn tìm giữa buổi demo.
3. Mở `http://localhost:9090`, kiểm tra hai worker ALIVE. Chuẩn bị tab `http://localhost:4040`; tab chỉ truy cập được khi ứng dụng Spark đang chạy. Không chạy song song job khác.
4. Đặt sẵn hai JSON toàn tháng tại các trường số dòng, dòng trùng, giá lỗi và `invariants`; ảnh chụp các trường này cũng có thể dùng để trình chiếu.
5. Chạy block chuẩn bị dưới đây một lần. Block chỉ sao chép raw synthetic đã có vào DATA_DIR mới; chưa chạy profiling, không tạo lại dữ liệu thật và không ghi đè vùng cũ.

PowerShell, đứng tại `D:\BigData\bigdata-ecommerce-spark`:

```powershell
$repo = (Get-Location).Path
$source = Join-Path $repo 'data/synthetic_tv2_m1_20261110_231427'
if (!(Test-Path -LiteralPath "$source/raw/events")) { throw 'Thieu raw synthetic M1' }
$demoName = 'synthetic_tv2_demo_' + (Get-Date -Format 'yyyyMMdd_HHmm')
$demoHost = Join-Path $repo "data/$demoName"
if (Test-Path -LiteralPath $demoHost) { throw 'DATA_DIR da ton tai' }
New-Item -ItemType Directory -Path $demoHost -ErrorAction Stop | Out-Null
Copy-Item -LiteralPath "$source/raw" -Destination "$demoHost/raw" -Recurse -ErrorAction Stop
$demoDataDir = "/data/$demoName"
Write-Host "DATA_DIR cho buoi demo: $demoDataDir"
```

Nếu Docker đang dừng, chạy `docker compose up -d --no-build` trước buổi demo rồi kiểm tra lại worker; không đưa thời gian khởi động cụm vào phần trình bày. Giữ nguyên cửa sổ PowerShell chứa các biến trên.

## Timeline 180 giây

| Thời điểm | Thời lượng | Thao tác | Lời nói gợi ý |
|---|---:|---|---|
| 00:00–00:20 | 20 giây | Mở đầu, chỉ tên dataset và schema trong contract | “Em phụ trách dữ liệu và chất lượng dữ liệu. Bộ dữ liệu ghi lại hành vi thương mại điện tử tháng 10 năm 2019, gồm 42,4 triệu sự kiện, dung lượng CSV khoảng 5,7 GB. Mỗi dòng là một lượt xem, thêm vào giỏ hoặc mua hàng. Phần minh họa dùng dữ liệu giả nhỏ có chủ ý chèn lỗi.” |
| 00:20–00:45 | 25 giây | Contract mục quy tắc và hệ quả | “Contract thống nhất UTC, dedup cả dòng raw trước chuẩn hóa; loại giá không hợp lệ và thiếu định danh bắt buộc. Brand hoặc danh mục thiếu được giữ lại với nhãn unknown ở các cột chuẩn hóa. Session có nhiều sự kiện, không phải khóa duy nhất.” |
| 00:45–01:10 | 25 giây | Chạy lệnh profiling ở mục dưới; chuyển sang Spark UI khi có 4040 | “Em chạy profiling raw trên Parquet synthetic đã ingest. DATA_DIR này mới, nên kết quả cũ được giữ nguyên. Job đo số dòng, dòng trùng, null, giá lỗi và phân bố sự kiện.” |
| 01:10–01:45 | 35 giây | Khi job chạy, mở JSON synthetic M1 đã chuẩn bị để giải thích các trường | “Đây là kết quả đã lưu cho cùng dữ liệu raw: khoảng 202 nghìn dòng, hơn 2 nghìn dòng trùng và khoảng 2,3 nghìn dòng giá không dương. Có 220 dòng thiếu giá, 198 dòng thiếu phiên và 212 dòng có phiên chỉ chứa khoảng trắng. Chuỗi nan đã thành null khi đọc CSV, nên cần xem riêng các bộ đếm.” |
| 01:45–02:10 | 25 giây | Nếu job xong, đọc JSON mới bằng lệnh tóm tắt; nếu chưa xong dùng phương án dự phòng | “Em đối chiếu các chỉ số đếm của JSON mới với raw đã chuẩn bị. Thời gian và application ID có thể thay đổi giữa các lần chạy; ở đây em kiểm chứng chất lượng dữ liệu, không đo benchmark.” |
| 02:10–02:45 | 35 giây | Mở JSON toàn tháng hoặc ảnh chụp các trường kết quả | “Dữ liệu thật được xử lý theo từng lát ngày vì giới hạn bộ nhớ. Trong 42,4 triệu dòng raw có khoảng 30 nghìn dòng trùng và hơn 68 nghìn dòng giá không hợp lệ. Sau làm sạch còn khoảng 42,35 triệu dòng; số dòng trùng và giá không dương đều bằng 0. Tất cả kiểm tra chất lượng đều đạt.” |
| 02:45–03:00 | 15 giây | Chỉ sơ đồ tầng trong contract hoặc cây thư mục | “Dữ liệu đi từ landing CSV sang raw Parquet, qua cleaning và profiling để kiểm chứng, rồi aggregation tạo KPI. TV2 bàn giao contract, báo cáo chất lượng và samples để các phần KPI, benchmark dùng chung dữ liệu đã kiểm tra.” |

Các thời lượng trên là kế hoạch trình bày, tổng 180 giây; không phải thời gian job đã đo.

## Lệnh chạy ở mốc 00:45

Trong chính cửa sổ PowerShell đã chuẩn bị:

```powershell
$demoTimer = [System.Diagnostics.Stopwatch]::StartNew()
docker exec -e "DATA_DIR=$demoDataDir" -e DATA_KIND=synthetic spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --driver-memory 1g --executor-memory 1g --conf spark.executor.cores=1 --conf spark.cores.max=2 --conf spark.sql.shuffle.partitions=32 /opt/jobs/01_profiling.py raw
$demoExit = $LASTEXITCODE
$demoTimer.Stop()
Write-Host "Submit-to-exit seconds: $($demoTimer.Elapsed.TotalSeconds)"
Write-Host "Profiling exit=$demoExit; JSON=$demoHost/reports/profiling_raw.json"
```

Cấu hình này dành cho demo nhỏ, khác cấu hình benchmark KB3 và khác lệnh kéo dài thời gian chụp ảnh M3.

### Kết quả chạy thử ngày 11/11/2026

| Mục | Kết quả |
|---|---|
| DATA_DIR mới | `/data/synthetic_tv2_demo_20261111_0107` |
| Exit code | `0` |
| Thời gian từ submit đến khi lệnh kết thúc, gồm khởi động Spark | 51,5 giây |
| JSON | `data/synthetic_tv2_demo_20261111_0107/reports/profiling_raw.json` |
| Log | `data/synthetic_tv2_demo_20261111_0107/profiling_demo.log` |
| Bản ghi thời gian và exit code | `data/synthetic_tv2_demo_20261111_0107/demo_run_result.json` |

Với số đo này, chạy ở mốc 00:45 sẽ kết thúc khoảng 01:37, trước phần đọc JSON mới lúc 01:45. Thời gian thực tế có thể thay đổi theo tải máy; nếu chưa xong thì dùng JSON đã chuẩn bị theo phương án dự phòng. Một lần submit trước đó tại `data/synthetic_tv2_demo_20261111_0106` đã tạo JSON thành công nhưng phần ghi đo bị PowerShell ngắt khi nhận log INFO trên stderr, nên không dùng lần đó để báo thời gian hoặc exit code.

Lệnh đọc JSON mới khi file đã xuất hiện và job thành công:

```powershell
if ($demoExit -ne 0) { throw "Profiling that bai, exit=$demoExit; xem log goc" }
$profile = Get-Content -LiteralPath "$demoHost/reports/profiling_raw.json" -Raw -Encoding UTF8 | ConvertFrom-Json
[PSCustomObject]@{
    DataDir = $profile.data_dir
    Status = $profile.status
    Rows = $profile.rows
    Duplicates = $profile.duplicate_rows
    PriceLe0 = $profile.price.price_le_0
    PriceNull = $profile.price.price_null
    SessionNull = $profile.nulls.user_session
    SessionBlank = $profile.blank_strings.user_session
} | Format-List
```

Không gõ lệnh đọc khi profiling còn chiếm terminal. Có thể mở terminal khác để kiểm tra file, nhưng biến PowerShell không tự truyền sang cửa sổ mới; khi đó dùng DATA_DIR đã in ra để xác định đường dẫn.

## Phương án dự phòng để giữ đúng thời lượng

Nếu đến 01:45 job vẫn chạy hoặc có lỗi, giữ log và nói rõ:

> “Lần chạy trực tiếp chưa hoàn tất/đang gặp lỗi. Em dùng JSON M1 đã lưu để trình bày cấu trúc kết quả; đây không phải output của lần chạy đang mở.”

Mở `docs/evidence/tv2/m1_20261110_231427/profiling_raw.json` đã chuẩn bị; không đứng chờ hoặc sửa cấu hình trong phần ba phút. Nếu job lỗi, đọc nguyên văn lỗi sau phần trình bày, không báo thành công. Không chạy lại trên DATA_DIR đã có output; lần thử tiếp dùng lại block chuẩn bị để tạo tên mới.

Khi trình chiếu hai JSON toàn tháng, giới thiệu đây là kết quả đã lưu từ lần chạy dữ liệu thật.

## Nguồn cho các số nói trong demo

| Nhóm số | File nguồn và trường |
|---|---|
| Dung lượng CSV | `docs/evidence/tv2/kb3.csv`, dòng `size,csv` |
| Rows/trùng/giá toàn tháng | `docs/evidence/tv2/profiling_raw.json`: rows, duplicate_rows, price.price_le_0 |
| Clean toàn tháng và bất biến | `docs/evidence/tv2/profiling_clean.json`: rows, duplicate_rows, price.price_le_0, invariants.all_pass |
| Các số synthetic và thời gian M1 | `docs/evidence/tv2/m1_20261110_231427/profiling_raw.json`: rows, duplicate_rows, price, nulls.user_session, blank_strings.user_session, profile_seconds |
| Số lát/nguyên nhân chia lát | `docs/evidence/tv2/cleaning_metrics_merged.json`: slices, note |

## Diễn tập trước buổi trình bày

- [ ] Mở thử hai JSON toàn tháng hoặc ảnh chụp theo checklist M3.
- [ ] Tập nói với đồng hồ, thao tác chuyển editor/terminal/browser trong 180 giây.
- [ ] Kiểm tra Docker và các file kết quả dùng trong demo.
- [ ] Tự giải thích được các trường JSON, đặc biệt null khác chuỗi trắng và giá lỗi có thể bị nhân bản.
