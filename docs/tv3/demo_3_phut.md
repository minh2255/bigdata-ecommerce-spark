# Kịch bản demo TV3 trong khoảng ba phút

## Chuẩn bị trước giờ trình bày

Kiểm tra hai worker ALIVE và chọn một mã lượt mới. Dữ liệu demo luôn là synthetic, nêu rõ ngay khi bắt đầu. Chuẩn bị raw trước để thời gian ba phút tập trung vào cleaning, không chờ ingest hoặc cài môi trường.

```powershell
Set-Location D:/Desktop/BigData
$run = Get-Date -Format yyyyMMdd_HHmmss
$env:DATA_DIR = "/data/tv3_demo_$run"
$env:DATA_KIND = 'synthetic'
docker exec spark-master python3 /opt/scripts/check_cleaning.py fixture $env:DATA_DIR mixed
docker exec -e "DATA_DIR=$env:DATA_DIR" spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --driver-memory 2g /opt/jobs/00_ingest.py
```

Không chạy trước cleaning vào cùng vùng, vì job từ chối ghi đè. Nếu buổi demo dùng lại mẫu cũ, tạo mã lượt mới. Mở sẵn docs/evidence/tv3 để có minh chứng lịch sử nếu một ứng dụng thật chạy lâu; nói rõ khi đang xem ảnh/log đã lưu.

## Lời trình bày và thao tác

| Thời gian | Nội dung trình bày và hành động |
| --- | --- |
| 0:00–0:25 | Tôi phụ trách raw → clean. Đây là fixture synthetic 14 dòng, có lỗi chủ động; không phải Kaggle. Chỉ ra raw/events và vị trí clean sẽ được tạo. |
| 0:25–0:45 | Chạy clean-only ở lệnh dưới; giải thích full pipeline còn chờ profiling/aggregation, mode này chỉ gọi TV3. |
| 0:45–1:30 | Trong lúc Spark chạy, giải thích thứ tự bỏ trùng, parse UTC, loại event lạ, giá lỗi và thiếu định danh; brand/category được chuẩn hóa. NaN/Inf, session trắng và chuỗi rỗng là quy tắc mở rộng chờ TV2 xác nhận. |
| 1:30–2:00 | Đọc log theo các bước 14 → 13 → 12 → 11 → 6 → 3; chỉ ra removed và stage_seconds. Nếu chưa kết thúc, xem log đang chạy, không khẳng định kết quả trước khi có [EXIT] 0. |
| 2:00–2:35 | Mở metrics và thư mục event_date=2019-10-01; giải thích đây là phân vùng lưu trữ. Có thể mở Application UI khi còn driver, hoặc ảnh đã lưu và nêu nguồn ảnh. |
| 2:35–3:00 | Nêu kiểm tra đọc lại, không ghi đè, xử lý rỗng và giao diện TV4. Kết luận phạm vi cá nhân đã kiểm chứng; còn Kaggle/data contract/tích hợp/chạy máy khác. |

```powershell
& 'C:/Program Files/Git/bin/bash.exe' scripts/run_pipeline.sh --clean-only
$LASTEXITCODE
$local = 'D:/Desktop/BigData/data/' + $env:DATA_DIR.Substring('/data/'.Length)
Get-Content -LiteralPath "$local/reports/cleaning_metrics.json"
Get-ChildItem -LiteralPath "$local/clean/events"
```

Đường dẫn trên được ghép từ DATA_DIR do người trình bày vừa tạo; không dùng với DATA_DIR ngoài /data. Khi job lỗi, nói rõ bước lỗi và mở log; không đổi sang overwrite hoặc tạo kết quả giả để hoàn thành thời lượng. Thời gian fixture phụ thuộc máy và có thể dài hơn thời lượng dự kiến, nên cần tập trước buổi trình bày.

## Câu hỏi đáp ngắn

**Tại sao dropDuplicates trước chuẩn hóa?** Hướng dẫn yêu cầu bỏ hàng raw trùng hoàn toàn. Hai hàng khác nhau chỉ ở chữ hoa/thường có thể trở nên giống sau chuẩn hóa; đó là vấn đề cần data contract quyết định, không tự gộp thêm.

**Session có phải khóa duy nhất?** Không. Một phiên có nhiều sự kiện. Test valid-repeat giữ ba sự kiện khác nhau cùng session để kiểm tra điều này.

**Tại sao UTC?** Để kết quả event_date/event_hour không phụ thuộc múi giờ máy. TV4 cũng phải đặt session UTC khi đọc và phân tích timestamp.

**Tại sao có nhiều count?** Cần số liệu qua từng bước cho KB5. Count là action có chi phí; cache giúp giảm tính lại, nhưng tổng thời gian vẫn gồm hoạt động đo/ghi/đọc lại.

**Partition khác file như thế nào?** Partition lưu trữ là thư mục theo ngày; bên trong có thể có nhiều part file. Partition thực thi là phần dữ liệu của task. 31 file quan sát được không phải mục tiêu tối ưu cho Kaggle.

**Dữ liệu rỗng xử lý thế nào?** Trả SUCCESS_EMPTY, ghi Parquet rỗng có schema và readback 0; không tạo ngày/hàng giả. TV4 phải xử lý không có dữ liệu để tổng hợp.

**Giá trị NaN/Inf hoặc ID âm ra sao?** NaN/Inf bị loại theo mở rộng đang chờ xác nhận. user_id chỉ yêu cầu không null, nên ID âm chưa tự bị loại; không áp thêm luật dương hoặc UUID.

**Tại sao không collect toàn bộ?** Driver có bộ nhớ hữu hạn. Fixture nhỏ được giới hạn 10000 dòng; kiểm tra tập lớn dùng phép giảm phân tán và chỉ lấy scalar.

**Đã hoàn tất dữ liệu thật chưa?** Chưa. Cần CSV Kaggle, contract TV2, profiling/aggregation và xác nhận tái lập trên máy khác.
