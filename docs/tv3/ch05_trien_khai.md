# 5 Cài đặt và triển khai phần xử lý làm sạch

## 5.1 Phạm vi triển khai và trạng thái môi trường

Chương này trình bày môi trường đã sử dụng, đầu vào/đầu ra của TV3, cách triển khai cleaning và cách điều phối pipeline. Đã kiểm chứng ingest, profiling raw/clean và cleaning trên synthetic cùng các điều kiện biên; TV2 đã chạy cleaning và profiling trên dữ liệu Kaggle thật (mục 5.8). Job `03_aggregation.py` của TV4 đã có trên `origin/main` và TV2 đã chạy `--full` thành công trên synthetic (`docs/evidence/tv2/m1_20261110_231427/run_summary.json`: mode `--full`, exit 0). Nhánh TV3 ban đầu tạo từ `origin/main` `1249075` nên chưa chứa file đó; ngày 16/11/2026 đã rebase lên `014777a` nên file đã có, nhưng TV3 chưa chạy `--full` trên cụm Spark. Các phần chưa thực thi được ghi đúng trạng thái, không tạo job thay thế để làm đủ chuỗi trên danh nghĩa.

Repo tại D:/Desktop/BigData. Nhánh codex/tv3-contract-quality được tạo từ origin/main 1249075 sau khi xác nhận PR #1 TV3 và PR #2 TV2 đã merge. Checkout ban đầu sạch. Phiên này chưa commit, push, mở PR hoặc merge; nhóm trưởng review thay đổi theo quy trình nhóm.

Máy kiểm thử chạy Windows 11 Home, có khoảng 16 GB RAM vật lý và 20 logical CPU. Docker Desktop dùng WSL2 với Linux engine, khoảng 7.6 GiB RAM khả dụng cho engine ở thời điểm kiểm tra. Docker 29.8.2, Compose v5.6.0 và hello-world đã chạy thành công. Image hiện có sử dụng Spark 3.5.9, Java 17 và Python 3.10.12. Hai worker mỗi worker khai báo hai core và 2048 MiB, tổng bốn core và 4096 MiB cho tài nguyên worker. Không suy tổng này thành bốn GiB heap thực tế đang dùng ở mọi thời điểm.

Dockerfile và docker-compose.yml của TV1 đã build và khởi động được nên được giữ nguyên. Các thư mục data, jobs và scripts được mount lần lượt vào /data, /opt/jobs và /opt/scripts. Bản mã nguồn chỉnh trên Windows được container nhìn thấy qua mount; thay đổi Python/Bash không yêu cầu build lại image. Thay đổi thư viện trong image mới cần được đánh giá build lại. Phiên hoàn thiện bàn giao chỉ sử dụng cụm hiện có, không thiết lập lại môi trường hoặc chạy lại các benchmark đã đạt.

## 5.2 Quy ước vùng dữ liệu và đầu vào

Mỗi lượt xử lý dùng một DATA_DIR riêng trong /data, bên trong có landing, raw, clean, agg, samples và reports. Vùng synthetic đã kiểm chứng là /data/synthetic_tv3_20261018_optimized. Vùng tháng 10 thật gồm /data/real_oct_run01 (landing và raw) và /data/real_oct_full (clean gộp từ 8 lát, mục 5.9; nguồn: `TV2_Plan_Roadmap.md`). Việc tách vùng tránh tình huống ingest đọc chung CSV giả và CSV Kaggle qua wildcard. DATA_KIND được dùng để khai báo synthetic hoặc real; source.json có thể ghi nguồn của fixture. Khai báo loại dữ liệu là dấu vết nguồn, không phải chứng nhận tính xác thực của file.

CSV đầu vào phải có đúng tên và thứ tự chín cột trong hướng dẫn. Ingest dùng schema cố định, tạo raw/events bằng Parquet. Cleaning kiểm tra kiểu của các cột bắt buộc trước khi xử lý: event_time/event_type/category_code/brand/user_session là string; product_id/category_id/user_id là bigint; price là double. File tên 2019-Oct.csv chỉ có 12 byte trong vùng guard_mixed là fixture chống trộn và đã được loại khỏi mọi kết quả dữ liệu thật.

<!-- page -->

## 5.3 Thực hiện các quy tắc làm sạch

Quy tắc căn cứ docs/data_contract.md v1.0 của TV2, đã merge trong PR #2. Dedup chỉ xét đúng chín cột raw trước chuẩn hóa. Các sự kiện khác nhau của cùng một user_session vẫn được giữ nếu không trùng toàn bộ hàng. TV3 không coi session là khóa duy nhất và không gộp tất cả sự kiện của một phiên thành một hàng.

Tiếp theo, event_time được parse thành event_ts trong session UTC. Dòng không parse được bị loại và được tính vào số mất ở giai đoạn thời gian. Chỉ ba event_type view, cart và purchase được giữ. Bước giá giữ giá lớn hơn 0; bước định danh yêu cầu user_id không null và user_session không null. Quy tắc đang triển khai còn loại giá NaN/Inf và session chỉ chứa khoảng trắng. Các điều kiện này đã được contract v1.0 xác nhận. Timestamp phải khớp đầy đủ yyyy-MM-dd HH:mm:ss UTC; thiếu hậu tố, sai định dạng và ngày không hợp lệ đều bị loại.

Chương trình không áp đặt user_id dương, product_id dương hay định dạng UUID của session. Kiểm thử có user_id âm hợp lệ về mặt quy tắc hiện tại để tránh vô tình đưa thêm ràng buộc ngoài hướng dẫn. Nếu data contract sau này yêu cầu những ràng buộc đó, thay đổi phải có mô tả tác động và số dòng bị loại riêng. Không tự biến dữ liệu bất thường thành giá trị có vẻ hợp lệ bằng cách thay ID hoặc thay giá.

category_code được tách theo dấu chấm để tạo cat_l1 và cat_l2; cấp thứ ba trở đi không được đưa vào hai cột dẫn xuất này, nhưng category_code gốc vẫn giữ. cat_l1/cat_l2 null hoặc rỗng được gán unknown. Brand được trim và chuyển chữ thường; brand null/rỗng cũng thành unknown. Xử lý chuỗi rỗng của danh mục/thương hiệu tuân theo contract v1.0. Quy tắc này không khôi phục nhãn thật đã thiếu và không chứng minh dữ liệu không còn vấn đề ngữ nghĩa.

Từ event_ts, job tạo event_date kiểu date, event_hour kiểu int từ 0 đến 23 và day_of_week kiểu string theo mẫu E. Cột event_time gốc được bỏ khỏi clean; các cột định danh, event_type, price, category_code và user_session được giữ. event_ts là timestamp, được diễn giải theo session UTC; khi TV4 đọc bằng Spark cũng cần giữ UTC để không đổi ranh giới ngày/giờ theo cấu hình máy khác. [Data Types 3.5.9](https://spark.apache.org/docs/3.5.9/sql-ref-datatypes.html), [Datetime Patterns 3.5.9](https://spark.apache.org/docs/3.5.9/sql-ref-datetime-pattern.html)

## 5.4 Log và số liệu hỗ trợ KB5

Sau mỗi bước, chương trình ghi tên giai đoạn, số dòng còn lại, số loại so với bước trước và thời gian action của giai đoạn. cleaning_metrics.json ghi thêm tổng thời gian, application ID, múi giờ, loại dữ liệu, trạng thái rỗng và nguồn luật và phiên bản contract 1.0. cleaning_schema.json lưu schema đầu ra. Thời gian từng giai đoạn không phải các phép benchmark độc lập: cache, khởi tạo kế hoạch và tài nguyên được dùng trong cùng ứng dụng; tổng còn bao gồm ghi/đọc lại dữ liệu và các chi phí khác.

Bộ synthetic cũ đã kiểm chứng có 1995 dòng trùng và 2027 dòng giá không hợp lệ sau bỏ trùng. Bảng số liệu này được bàn giao cho TV2 làm dữ liệu hỗ trợ KB5. Job 01_profiling.py của TV2 hiện tạo profiling_raw.json và profiling_clean.json thật trong mode --quality-check; kết quả mới ở docs/tv3_run_20261027.md. Baseline trên là synthetic lịch sử.

<!-- page -->

## 5.5 Ghi Parquet và bảo toàn dữ liệu

Với dữ liệu sạch không rỗng, job giữ giải pháp repartition theo event_date rồi partitionBy event_date đã được kiểm chứng trên máy Windows. Mode errorifexists từ chối đường dẫn đầu ra đã tồn tại. Báo cáo metrics và schema cũng dùng chế độ tạo mới; không ghi đè nội dung cũ. Nếu một lần xử lý thất bại giữa chừng và để lại đầu ra chưa hoàn tất, người chạy chọn DATA_DIR mới, giữ log để chẩn đoán trước khi quyết định xử lý vùng cũ.

Đầu ra không rỗng của bộ synthetic lớn có 31 thư mục ngày và 31 file Parquet. Cách ghi này được giữ vì đã xử lý được sự cố hàng nghìn file nhỏ ở lượt đầu, không phải vì một file/ngày là mục tiêu tối ưu cố định. Dữ liệu Kaggle chưa có để đánh giá lại kích thước file và tải lệch theo ngày. Các thay đổi tiếp theo về số partition phải dựa trên số đo, không dựa vào kỳ vọng rằng nhiều hoặc ít file luôn nhanh hơn.

Trường hợp raw rỗng hoặc mọi hàng bị loại cần xử lý riêng. Khi không có hàng, không có giá trị ngày để tạo thư mục phân vùng. Job ghi một file Parquet rỗng chứa đầy đủ schema ngay dưới clean/events, để lệnh đọc thông thường vẫn trả DataFrame có cột đúng và count bằng 0. Metrics ghi SUCCESS_EMPTY và empty_output=true. Không tạo một ngày giả hoặc một hàng giả để làm xuất hiện partition. Trạng thái rỗng là kết quả cần downstream xử lý, không đồng nghĩa với dữ liệu kinh doanh đã sẵn sàng có KPI.

## 5.6 Điều phối pipeline và kiểm tra trước khi chạy

Full mode giữ đúng chuỗi ingest → profiling raw → cleaning → profiling clean → aggregation. Trước khi submit, script kiểm tra các file job cần thiết ở host và trong mount container, Compose config, container master đang chạy, tham số memory/master URL, phạm vi DATA_DIR và đầu vào. Với CSV, helper kiểm tra header/thứ tự cột và phát hiện tên synthetic trộn với tên khác. Với clean-only, helper yêu cầu raw/events có Parquet và có thông tin nguồn. Kiểm tra tên file không phát hiện được mọi dữ liệu giả bị đổi tên, nên người cung cấp vẫn phải chịu trách nhiệm xác nhận nguồn.

--ingest-clean chỉ chạy ingest hiện có của TV1 và cleaning TV3; --clean-only chỉ chạy cleaning từ raw. Hai mode này không gọi profiling hoặc aggregation và ghi rõ DONE TV3. --available được giữ làm alias của --ingest-clean để không làm hỏng lệnh cũ; tài liệu mới dùng tên mode tường minh. Không xem mode cá nhân thành công là full pipeline thành công. Mode --quality-check chạy ingest, profiling raw, cleaning và profiling clean. Sau khi rebase lên `origin/main` (16/11/2026), thư mục jobs đã có 03_aggregation.py nên kiểm tra thiếu job của `--full` không còn dừng ở exit 3; TV3 chưa chạy `--full` thật trên cụm Spark để xác nhận.

DATA_DIR và DATA_KIND được truyền vào từng docker exec bằng các phần tử mảng Bash có quote, giúp đường dẫn có khoảng trắng vẫn là một đối số. Git Bash đặt MSYS_NO_PATHCONV=1 để giữ đường dẫn Linux bên trong container. Compose config dùng đường dẫn tương đối docker-compose.yml sau khi script chuyển về repo; cách này tránh lỗi /d/... bị Docker hiểu sai khi chuyển đổi MSYS đã tắt. Unit test có repo chứa khoảng trắng; Spark integration có DATA_DIR chứa khoảng trắng.

<!-- page -->

## 5.7 Xử lý lỗi và lưu minh chứng

Mỗi lần gọi pipeline tự tạo một log mới trên host trong data/reports/tv3_pipeline_logs. Log chứa mode, bước đang chạy, tên job, DATA_DIR và exit code cuối. Script dùng set -euo pipefail và kiểm tra kết quả spark-submit; job lỗi sẽ dừng chuỗi và giữ mã thoát đó. Quy ước 2 dành cho tham số không hợp lệ, 3 cho thiếu mã nguồn, 4 cho cấu hình/container/đầu vào hoặc hàng rào dữ liệu không đạt; mã khác từ submit được truyền nguyên. Người chạy PowerShell đọc $LASTEXITCODE ngay sau lệnh Bash; Git Bash đọc $? ngay sau lệnh.

Kiểm thử mock điều khiển shell cố ý làm Docker/submit trả lỗi để kiểm tra nhánh xử lý và thứ tự dừng. Những mock này chỉ tồn tại trong sandbox kiểm thử, không được đặt vào jobs của sản phẩm và không tạo kết quả Spark. Kiểm thử tích hợp thật dùng cụm hiện có, chạy fixture mixed, empty, all-invalid, valid-repeat và contract trong DATA_DIR mới. Mỗi trường hợp được đối chiếu độc lập bằng Python/PyArrow, kiểm tra schema/điều kiện bằng các phép giảm Spark và thử chạy lại để xác nhận dữ liệu/báo cáo được bảo vệ.

Trường hợp valid-repeat giữ các sự kiện khác nhau của cùng một session, có thời gian gần ranh giới ngày và user_id âm để kiểm tra đúng phạm vi quy tắc. Fixture empty kiểm tra header nhưng không có dòng; all-invalid kiểm tra đầu vào có hàng nhưng clean bằng 0. Đây là các kiểm thử nhỏ nhằm bắt lỗi logic và giao diện. Job validate_cleaning cho dữ liệu lớn chỉ trả số liệu tổng hợp về driver; nó không đối chiếu toàn bộ từng hàng raw với clean như bộ fixture và không thay thế profiling chính thức.

## 5.8 Kết quả trên dữ liệu Kaggle thật

TV2 đã chạy cleaning trên tháng 10/2019 thật (raw 42.448.764 dòng). Số liệu dưới đây lấy nguyên từ `docs/evidence/tv2/cleaning_metrics_merged.json` (gộp từ 8 lát, mục 5.9); TV3 không chạy lại bước này và không tính lại số liệu.

Bảng 5.1. Số dòng qua các bước cleaning trên dữ liệu thật (tổng 8 lát)

| Bước | Số dòng còn lại | Loại so với bước trước |
| --- | --- | --- |
| raw | 42.448.764 | – |
| after_dedup | 42.418.544 | 30.220 |
| after_timestamp | 42.418.544 | 0 |
| after_event_type | 42.418.544 | 0 |
| after_price | 42.349.874 | 68.670 |
| after_identity | 42.349.872 | 2 |
| written (đọc lại) | 42.349.872 | 0 |

Tổng thời gian cleaning là **2552.5 giây**, lấy nguyên trường `cleaning_seconds_total` (tổng thời gian của tám lát, mỗi lát từ 166.162 đến 392.682 giây). Đầu ra có **31 thư mục event_date** (nguồn: `docs/evidence/tv2/audit_5b_sources_20261111.json`, trường `full_clean_partition_dates`). Các bước timestamp và event_type không loại dòng nào trên tập này. Số dòng loại ở bước giá (68.670) thấp hơn 3 so với số dòng giá ≤ 0 trong profiling raw (68.673). Hai số không mâu thuẫn: profiling raw đếm trước dedup nên còn tính các bản sao của dòng lỗi giá, còn cleaning loại giá sau dedup (TV2 cũng ghi nhận điều này; repo không có số liệu tách riêng từng dòng bị trùng). Bảng không cộng các bộ đếm lỗi giao nhau như tập rời nhau.

Profiling clean theo từng lát cho `invariants.all_pass = true`, 0 dòng trùng và 0 dòng giá ≤ 0 (`docs/tv2/ch03_du_lieu.md`, `docs/evidence/tv2/slices/`). Thời gian 2552.5 giây là thời gian xử lý trên máy 8 GB đã cấu hình trong mục 5.9, không phải phép đo hiệu năng độc lập.

## 5.9 Cleaning vượt bộ nhớ và chia lát theo ngày

Khi chạy cleaning một lần trên toàn bộ 42.448.764 dòng, máy RAM 8 GB (WSL được cấp 5 GB theo `TV2_Plan_Roadmap.md`) bị hết bộ nhớ executor, theo ghi chú trong `cleaning_metrics_merged.json`. Executor 2 GB là cấu hình cụm dùng cho các lần đo benchmark (`kb3_env.json`); repo không có log của lần lỗi nên không xác nhận được cấu hình, số lần lỗi hay mã lỗi của lần đó, và báo cáo không nêu các thông tin này (theo audit 5b của TV2). Kết quả chính thức là kết quả của cách chia lát bên dưới.

Cách xử lý của TV2: dùng `jobs/slice_raw_by_day.py` tách `raw/events` thành 8 lát theo ngày (ngày 1–4, 5–8, …, 29–31 theo `docs/tv2/ch03_du_lieu.md`), mỗi lát nằm ở một DATA_DIR riêng dạng `/data/real_oct_s<k>/raw/events` với k từ 1 đến 8. Sau đó chạy nguyên `02_cleaning.py`, không sửa logic, cho từng lát, rồi gộp kết quả vào `/data/real_oct_full`. Số dòng raw mỗi lát từ 3.683.534 đến 6.158.388.

Bảng 5.2. Số dòng và thời gian theo lát (nguồn: `cleaning_metrics_merged.json`, trường slices)

| Lát | Raw | Written | Giây |
| --- | --- | --- | --- |
| 1 | 4.980.066 | 4.970.309 | 392.682 |
| 2 | 5.219.882 | 5.206.753 | 322.26 |
| 3 | 5.606.859 | 5.592.259 | 382.097 |
| 4 | 6.158.388 | 6.140.662 | 377.607 |
| 5 | 5.848.091 | 5.836.241 | 271.46 |
| 6 | 5.519.915 | 5.507.337 | 289.63 |
| 7 | 5.432.029 | 5.420.133 | 350.636 |
| 8 | 3.683.534 | 3.676.178 | 166.162 |

**Vì sao chia lát vẫn đúng.** Dedup xét đủ chín cột raw, trong đó có event_time. Hai dòng trùng hoàn toàn luôn có cùng event_time nên cùng ngày và nằm trong cùng một lát; các lát không chồng lấn và phủ toàn tháng. Vì vậy dedup từng lát cho cùng tập dòng bị loại như dedup cả tháng. Các bước còn lại (timestamp, event_type, giá, định danh, chuẩn hóa) là lọc hoặc biến đổi từng dòng nên không phụ thuộc cách chia. Đây là lập luận từ cấu trúc luật; TV3 không chạy lại bản nguyên khối để so trực tiếp.

**Nguyên nhân khả dĩ của lỗi bộ nhớ (giải thích, chưa đo riêng).** Hai yếu tố trong `02_cleaning.py` có thể làm tăng áp lực bộ nhớ: dropDuplicates trên chín cột cần shuffle toàn bộ dữ liệu theo khóa, và job có 6 điểm checkpoint, mỗi điểm persist MEMORY_AND_DISK rồi count, nên tại một thời điểm hai DataFrame trung gian có thể cùng được giữ. Chưa có phép đo hoặc log tách riêng từng yếu tố nên đây chỉ là giải thích khả dĩ, không phải kết luận nguyên nhân.

**Hạn chế.** Script tách lát `jobs/slice_raw_by_day.py` có trong repo sau khi rebase; TV3 đã chạy thử trên synthetic (không phải dữ liệu thật). Script chạy từng lát (`data/real_oct_run01/run_slices.sh`) và bước gộp vào `/data/real_oct_full` không có trong repo; theo `TV2_Plan_Roadmap.md` đó là thao tác của TV2 trên máy TV2. Số liệu gộp đã có trong JSON nhưng TV3 chưa xác nhận lại việc gộp bằng một lần chạy độc lập.

## 5.10 Tích hợp với TV2 và TV4

TV2 đã bàn giao contract v1.0 và profiling; tích hợp TV2–TV3 chạy theo mode --quality-check, không thay tên metrics mà compare_truth đang sử dụng. TV4 nhận đường dẫn gốc clean/events (với dữ liệu thật là /data/real_oct_full/clean/events, gộp từ 8 lát), schema 14 cột, quy ước UTC/ngày/thứ, trạng thái rỗng và phạm vi loại trùng. Đọc đường dẫn gốc giúp Spark nhận diện event_date từ thư mục; không đọc một part file riêng rồi suy rằng cột ngày bị mất. Các metadata về số dòng, nguồn dữ liệu và lần chạy phải đi kèm dữ liệu bàn giao.

Các sửa đổi benchmark TV1 từ phiên trước được giữ nguyên và ghi riêng: force phép tổng hợp bằng collect bảng nhóm nhỏ, ghi cấu hình/timing JSONL và truyền DATA_DIR qua script benchmark. Chúng không được tính là sản phẩm cá nhân TV3 trong gói này và không được chạy lại. Biểu đồ KPI, baseline Pandas và job aggregation vẫn thuộc TV4. Tài liệu bàn giao phân biệt lịch sử thiết lập với phần TV3 vừa hoàn thiện để tránh nhầm trách nhiệm.

File 2019-Oct.csv thật (5.668.612.855 byte, 42.448.764 dòng, header đúng chín cột theo `TV2_Plan_Roadmap.md`) đã được TV2 tải về vùng /data/real_oct_run01 và xử lý ở mục 5.8–5.9. Máy TV3 chưa chạy lại bước này. Các việc chưa có xác nhận là TV4 nhận bàn giao và đối chiếu KPI trên clean thật, kiểm thử tái lập trên máy thành viên khác, cùng ảnh Spark UI lúc cleaning thật chạy. Các phần độc lập đã chuẩn bị không được dùng để đánh dấu toàn bộ nhiệm vụ TV3 đã hoàn tất.

Lần kiểm chứng 16/11/2026 sau rebase lên `origin/main` `014777a`: `run_pipeline.sh --full` trên synthetic 20.000 dòng (vùng `/data/synthetic_tv3_full_20261116_120201`) trả exit 0 với 20.203 raw → 20.000 → 19.948 → 19.675 → 19.627 clean, năm bảng KPI của TV4 đều có `_SUCCESS` (chưa kiểm nội dung KPI). Cùng raw được tách 8 lát bằng `slice_raw_by_day.py` (tổng 20.203 dòng) và chạy `--clean-only` từng lát; tổng written của 8 lát là 19.627, bằng lần chạy nguyên khối. Đây là synthetic, không thay cho dữ liệu thật.

Lần kiểm chứng 27/10/2026 chạy generator TV2 20.000 dòng: 20.203 raw → 20.000 dedup → 19.627 clean; cleaning 41,578 giây. Profiling clean all_pass=true, compare_truth và validator đạt (0 vi phạm). Đây là synthetic trên cùng máy; kết quả Kaggle ở mục 5.8 do TV2 chạy. Chi tiết application ID, log, lệnh và giới hạn xem docs/tv3_run_20261027.md.
