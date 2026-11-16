# Phụ lục hướng dẫn chạy TV3 trên Windows

## Môi trường và phạm vi lệnh

Các lệnh dưới đây chạy tại D:/Desktop/BigData trên nhánh TV3 hiện có. Cụm đã được cài và đang chạy; không cần build lại để chạy Python/Bash mới vì jobs và scripts dùng bind mount. Nếu Docker đã tắt, mở Docker Desktop, chờ Linux engine sẵn sàng rồi chạy docker compose up -d --no-build. Chỉ build khi image chưa có hoặc Dockerfile/thư viện thay đổi. Không chạy lại benchmark của các thành viên để kiểm tra cleaning.

```powershell
Set-Location D:/Desktop/BigData
git branch --show-current
git status --short
docker compose ps
$master = Invoke-RestMethod http://localhost:8080/json/
$master.workers | Select-Object state,cores,memory
```

Kỳ vọng nhánh codex/tv3-contract-quality, master và hai worker running, hai worker ALIVE. Log lịch sử hai worker không thay thế kiểm tra trạng thái hiện tại. Cổng Master UI là 8080, worker là 8081/8082, Application UI 4040 chỉ có khi driver đang chạy.

## Chạy mẫu hoàn toàn mới

Chọn một tên DATA_DIR mới cho mỗi lượt, không tái sử dụng tên đã có raw hoặc clean. Script fixture tạo dữ liệu nhỏ có nhãn synthetic và từ chối ghi đè file đã có.

```powershell
$run = Get-Date -Format yyyyMMdd_HHmmss
$env:DATA_DIR = "/data/tv3_demo_$run"
$env:DATA_KIND = 'synthetic'
docker exec spark-master python3 /opt/scripts/check_cleaning.py fixture $env:DATA_DIR mixed
& 'C:/Program Files/Git/bin/bash.exe' scripts/run_pipeline.sh --ingest-clean
$code = $LASTEXITCODE
if ($code -ne 0) { throw "Pipeline thất bại: exit=$code" }
docker exec spark-master python3 /opt/scripts/check_cleaning.py verify $env:DATA_DIR
docker exec -e "DATA_DIR=$env:DATA_DIR" spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --driver-memory 2g /opt/jobs/validate_cleaning.py
```

Fixture mixed mới có 22 dòng; kết quả theo giai đoạn là 22, 21, 14, 13, 7, 3, đọc lại 3. Không dùng bộ fixture này để minh họa quy mô Big Data. Bộ synthetic lớn cũ có 201995 dòng raw và 197973 dòng clean là minh chứng đã lưu, không cần sinh hoặc chạy lại trong demo.

## Chỉ chạy cleaning khi đã có raw

Đặt DATA_DIR tới vùng có raw/events, source.json hoặc DATA_KIND phù hợp, nhưng chưa có clean/events và báo cáo cleaning. Lệnh không ingest lại và không gọi job của TV2/TV4.

```powershell
$env:DATA_DIR = '/data/<vung-raw-chua-co-clean>'
$env:DATA_KIND = 'synthetic' # chỉ chọn real sau khi xác nhận nguồn thật
& 'C:/Program Files/Git/bin/bash.exe' scripts/run_pipeline.sh --clean-only
$LASTEXITCODE
```

Không trỏ clean-only vào vùng synthetic cũ đã có clean để chạy lại. Với một lần thử cần giữ raw nhưng làm cleaning lại, chuẩn bị một vùng mới và bàn giao/copy raw có kiểm soát; không sửa script thành overwrite. Không copy toàn bộ dataset lớn chỉ để demo nếu đã có mẫu phù hợp.

## Full pipeline khi đủ bốn job

```powershell
$env:DATA_DIR = '/data/<vung-input-moi>'
$env:DATA_KIND = 'real' # hoặc synthetic đúng theo nguồn của vùng
& 'C:/Program Files/Git/bin/bash.exe' scripts/run_pipeline.sh --full
$LASTEXITCODE
```

Full kiểm tra đủ 00_ingest.py, 01_profiling.py, 02_cleaning.py và 03_aggregation.py trước khi submit. Chuỗi chạy là ingest, profiling raw, cleaning, profiling clean, aggregation. `03_aggregation.py` của TV4 đã có trên `origin/main` và TV2 đã chạy `--full` thành công trên synthetic (`docs/evidence/tv2/m1_20261110_231427/run_summary.json`). Nếu một nhánh chưa có file đó thì exit 3 là kết quả đúng; không coi là lỗi Docker. Nhánh TV3 đã rebase lên `origin/main` nên có file này. --available còn được hỗ trợ nhưng chỉ là alias của --ingest-clean, không tự chạy các job thành viên khác đã xuất hiện.

Trong Git Bash, các biến có thể đặt như sau. Dấu nháy kép là bắt buộc khi giá trị có khoảng trắng.

```bash
cd /d/Desktop/BigData
export DATA_DIR='/data/tv3 demo moi'
export DATA_KIND=synthetic
bash scripts/run_pipeline.sh --clean-only
echo "$?"
```

Không dùng C:/Windows/system32/bash.exe khi WSL chỉ có distro Docker Desktop. PowerShell dùng Git Bash theo đường dẫn đầy đủ như trên. Pipeline tự bật MSYS_NO_PATHCONV, không cần đặt lại trong PowerShell.

## Chuẩn bị dữ liệu thật và tiếp tục

Đăng nhập Kaggle bằng trình duyệt của người dùng, tải 2019-Oct.csv từ dataset được chỉ định rồi giải nén vào D:/Desktop/BigData/data/real_oct_run01/landing/2019-Oct.csv. Không gửi mật khẩu hoặc API token trong chat. Trên máy TV3 thư mục này trống (TV2 đã có file thật ở máy TV2); fixture 12 byte nằm trong guard_mixed không phải file Kaggle.

```powershell
$csv = 'D:/Desktop/BigData/data/real_oct_run01/landing/2019-Oct.csv'
Get-Item -LiteralPath $csv | Select-Object FullName,Length
Get-Content -LiteralPath $csv -TotalCount 1
Get-PSDrive D | Select-Object Free
docker info --format 'CPUs={{.NCPU}} MemoryBytes={{.MemTotal}}'
```

Header phải đúng: event_time,event_type,product_id,category_id,category_code,brand,price,user_id,user_session. Cần cân nhắc không gian cho CSV, raw, clean, file tạm và log; dung lượng trống phải kiểm tra lại trước lượt thật, không dựa vào số cũ của phiên thiết lập. Nếu vùng real_oct_run01 đã có đầu ra, chọn một vùng mới và đặt CSV tại landing của vùng đó.

Lệnh dưới chạy nguyên khối; trên máy RAM 8 GB dễ hết bộ nhớ ở bước cleaning, khi đó dùng mục chạy theo lát bên dưới.

```powershell
$env:DATA_DIR = '/data/real_oct_run01'
$env:DATA_KIND = 'real'
& 'C:/Program Files/Git/bin/bash.exe' scripts/run_pipeline.sh --quality-check
if ($LASTEXITCODE -ne 0) { throw 'Dừng để kiểm tra log, không ghi đè vùng cũ' }
docker exec -e "DATA_DIR=$env:DATA_DIR" spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --driver-memory 2g /opt/jobs/validate_cleaning.py
```

Lệnh verify bằng PyArrow chỉ dành cho fixture tối đa 10000 dòng, không dùng cho CSV Kaggle. Validator Spark chỉ đưa số liệu tổng hợp về driver; nó kiểm tra schema, điều kiện hợp lệ, cột thời gian và số dòng với metrics. Các kiểm tra sâu về tính đầy đủ raw-to-clean và profiling chính thức cần được lên kế hoạch cùng TV2 khi có dữ liệu thật.

## Chạy theo lát cho máy RAM thấp (8 GB)

TV2 chạy `02_cleaning.py` nguyên khối trên 42.448.764 dòng bị hết bộ nhớ executor trên máy 8 GB nên phải chia 8 lát theo ngày (`docs/evidence/tv2/cleaning_metrics_merged.json`, `TV2_Plan_Roadmap.md`). TV3 chưa thử chạy nguyên khối trên máy nào khác, nên không khẳng định ngưỡng RAM đủ. Script `jobs/slice_raw_by_day.py` do TV2 viết, có trong repo từ `origin/main` (nhánh TV3 đã rebase). Lệnh dưới suy từ docstring và chưa được TV3 chạy thử. Điều kiện: đã ingest, có `/data/real_oct_run01/raw/events`.

Bước 1, tách raw thành 8 lát (cú pháp theo docstring của script: SRC_DIR, OUT_PREFIX và các khoảng ngày; khoảng ngày theo mẫu 1–4, 5–8, …, 29–31 của `docs/tv2/ch03_du_lieu.md`). Lát k ghi ra `/data/real_oct_s<k>/raw/events`; script bỏ qua lát đã có Parquet.

```powershell
docker exec -e SRC_DIR=/data/real_oct_run01 -e OUT_PREFIX=/data/real_oct_s spark-master python3 /opt/jobs/slice_raw_by_day.py 1-4 5-8 9-12 13-16 17-20 21-24 25-28 29-31
```

Bước 2, chạy cleaning từng lát với DATA_DIR riêng. Mỗi lát chạy tuần tự, không chạy song song để tránh tranh bộ nhớ, và dùng DATA_KIND=real vì các lát không có source.json.

```powershell
foreach ($k in 1..8) {
  $env:DATA_DIR = "/data/real_oct_s$k"
  $env:DATA_KIND = 'real'
  & 'C:/Program Files/Git/bin/bash.exe' scripts/run_pipeline.sh --clean-only
  if ($LASTEXITCODE -ne 0) { throw "Lát $k lỗi, exit=$LASTEXITCODE" }
}
```

Mỗi lát tạo `clean/events` và `reports/cleaning_metrics.json` riêng (tám file metrics ứng với `docs/evidence/tv2/slices/s1..s8_cleaning_metrics.json`). Lát lỗi giữa chừng phải đổi sang DATA_DIR mới, không xóa hay ghi đè đầu ra cũ.

Bước 3, gộp. **Repo không có script gộp.** Theo ghi chú trong `cleaning_metrics_merged.json` và `TV2_Plan_Roadmap.md`, TV2 gộp kết quả tám lát vào `/data/real_oct_full` (clean/events và số liệu gộp) bằng thao tác ở máy TV2; script chạy lát `data/real_oct_run01/run_slices.sh` cũng không nằm trong repo. Vì các lát chia theo ngày và không chồng lấn, thư mục event_date của các lát không trùng nhau (suy ra từ cách chia). Không tự đoán lệnh gộp: người cần tái lập hỏi TV2 hoặc đối chiếu số liệu với `cleaning_metrics_merged.json` (tổng written 42.349.872, 31 thư mục event_date).

## Đọc đầu ra và mã lỗi

Đầu ra chuẩn là clean/events; báo cáo là reports/cleaning_metrics.json và cleaning_schema.json. Validator thêm cleaning_validation_spark.json. Pipeline log mới nằm trên host trong data/reports/tv3_pipeline_logs; dùng dòng [EXIT] để biết bước và exit code. Mỗi log có tên UTC và process ID để tránh ghi đè. Có thể đổi thư mục log bằng PIPELINE_LOG_DIR; đường dẫn có khoảng trắng phải được quote.

| Mã hoặc hiện tượng | Diễn giải và cách xử lý |
| --- | --- |
| 0 và DONE TV3/QUALITY | Phạm vi cá nhân thành công; chưa chứng minh full pipeline |
| 0 và DONE FULL | Cả năm bước full đã trả thành công; vẫn cần đối chiếu kết quả nghiệp vụ |
| 2 | Tham số/memory/master URL không hợp lệ; kiểm tra giá trị trước khi submit |
| 3 | Thiếu job/helper (ví dụ nhánh thiếu file từ origin/main); cập nhật nhánh hoặc chọn mode phù hợp, không tạo job rỗng |
| 4 | Preflight/config/container/input/đầu ra cũ không đạt; đọc thông báo trước [EXIT] |
| Mã submit khác 0 | Job thất bại, chuỗi dừng; giữ log và đầu ra một phần, chọn vùng mới khi chạy lại |
| SUCCESS_EMPTY | Job chạy xong nhưng clean có 0 dòng; kiểm tra nguồn và counts, downstream xử lý tập rỗng |
| Path does not exist | Kiểm tra DATA_DIR Linux trong container và mount /data, không truyền D:/... cho Spark |
| Initial job has not accepted resources | Kiểm tra worker/core/RAM và ứng dụng khác; không submit dồn nhiều job |
| UI 4040 không mở | Driver đã kết thúc hoặc chưa khởi tạo; dùng log và Master UI để đối chiếu |

## Chạy bộ kiểm thử bàn giao

```powershell
python tests/run_tv3_integration.py
if ($LASTEXITCODE -ne 0) { throw 'Fixture integration failed' }
```

Bộ tích hợp dùng Git Bash C:/Program Files/Git/bin/bash.exe; mỗi lượt tạo vùng dữ liệu
và log mới. Không chạy benchmark. Unit mock và Spark thật được ghi riêng. Thành viên
khác cần ghi máy, phiên bản, commit, thời điểm và kết quả thực tế của họ.

## Kiểm tra chất lượng theo contract TV2 v1.0

Docker phải chạy. Runner tạo DATA_DIR mới; lệnh và số đo ở docs/tv3_run_20261027.md.

```powershell
Set-Location D:/Desktop/BigData
python tests/run_quality_check.py 20000
if ($LASTEXITCODE -ne 0) { throw 'Quality integration failed' }
```




compare_truth kiểm tra exact tổng raw/dedup; các lỗi còn lại cho phép giao nhau với sai lệch tối đa 2% số lỗi chèn + 20 dòng. Verifier fixture đối chiếu đầy đủ giá trị và multiplicity.
