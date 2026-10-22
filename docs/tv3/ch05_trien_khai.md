# 5 Cài đặt và triển khai phần xử lý làm sạch

## 5.1 Phạm vi triển khai và trạng thái môi trường

Chương này trình bày môi trường đã sử dụng, đầu vào/đầu ra của TV3, cách triển khai cleaning và cách điều phối pipeline. Điểm đã kiểm chứng là ingest và cleaning trên dữ liệu giả cùng kiểm thử các điều kiện biên. Pipeline tích hợp đầy đủ còn phụ thuộc job profiling của TV2 và aggregation của TV4. Các phần chưa thực thi được được ghi đúng trạng thái, không tạo job thay thế để làm đủ chuỗi trên danh nghĩa.

Repo được clone vào D:/Desktop/BigData. Nhánh tv3/windows11-spark-setup được tạo từ main tại commit a86d31e796d7aeb7983a1d04b0b2cb9759ef3735 trước khi sửa mã nguồn. Các thay đổi chưa commit được giữ nguyên trong lần hoàn thiện bàn giao. Không thực hiện commit, push hoặc merge; nhóm trưởng vẫn chịu trách nhiệm review và tích hợp theo quy trình nhóm.

Máy kiểm thử chạy Windows 11 Home, có khoảng 16 GB RAM vật lý và 20 logical CPU. Docker Desktop dùng WSL2 với Linux engine, khoảng 7.6 GiB RAM khả dụng cho engine ở thời điểm kiểm tra. Docker 29.8.2, Compose v5.6.0 và hello-world đã chạy thành công. Image hiện có sử dụng Spark 3.5.9, Java 17 và Python 3.10.12. Hai worker mỗi worker khai báo hai core và 2048 MiB, tổng bốn core và 4096 MiB cho tài nguyên worker. Không suy tổng này thành bốn GiB heap thực tế đang dùng ở mọi thời điểm.

Dockerfile và docker-compose.yml của TV1 đã build và khởi động được nên được giữ nguyên. Các thư mục data, jobs và scripts được mount lần lượt vào /data, /opt/jobs và /opt/scripts. Bản mã nguồn chỉnh trên Windows được container nhìn thấy qua mount; thay đổi Python/Bash không yêu cầu build lại image. Thay đổi thư viện trong image mới cần được đánh giá build lại. Phiên hoàn thiện bàn giao chỉ sử dụng cụm hiện có, không thiết lập lại môi trường hoặc chạy lại các benchmark đã đạt.

## 5.2 Quy ước vùng dữ liệu và đầu vào

Mỗi lượt xử lý dùng một DATA_DIR riêng trong /data, bên trong có landing, raw, clean, agg, samples và reports. Vùng synthetic đã kiểm chứng là /data/synthetic_tv3_20261018_optimized. Vùng dự kiến cho tháng 10 thật là /data/real_oct_run01. Việc tách vùng tránh tình huống ingest đọc chung CSV giả và CSV Kaggle qua wildcard. DATA_KIND được dùng để khai báo synthetic hoặc real; source.json có thể ghi nguồn của fixture. Khai báo loại dữ liệu là dấu vết nguồn, không phải chứng nhận tính xác thực của file.

CSV đầu vào phải có đúng tên và thứ tự chín cột trong hướng dẫn. Ingest dùng schema cố định, tạo raw/events bằng Parquet. Cleaning kiểm tra kiểu của các cột bắt buộc trước khi xử lý: event_time/event_type/category_code/brand/user_session là string; product_id/category_id/user_id là bigint; price là double. File tên 2019-Oct.csv chỉ có 12 byte trong vùng guard_mixed là fixture chống trộn và đã được loại khỏi mọi kết quả dữ liệu thật.

<!-- page -->

## 5.3 Thực hiện các quy tắc làm sạch

Quy tắc tạm thời căn cứ mục 5.3 trong tài liệu đồ án, do repo chưa có data contract chính thức của TV2. Trước hết, dropDuplicates loại bản sao hoàn toàn theo các cột raw. Các sự kiện khác nhau của cùng một user_session vẫn được giữ nếu không trùng toàn bộ hàng. TV3 không coi session là khóa duy nhất và không gộp tất cả sự kiện của một phiên thành một hàng.

Tiếp theo, event_time được parse thành event_ts trong session UTC. Dòng không parse được bị loại và được tính vào số mất ở giai đoạn thời gian. Chỉ ba event_type view, cart và purchase được giữ. Bước giá giữ giá lớn hơn 0; bước định danh yêu cầu user_id không null và user_session không null. Quy tắc đang triển khai còn loại giá NaN/Inf và session chỉ chứa khoảng trắng. Đây là phần mở rộng cần TV2 xác nhận, không phải quyết định đã được toàn nhóm thống nhất.

Chương trình không áp đặt user_id dương, product_id dương hay định dạng UUID của session. Kiểm thử có user_id âm hợp lệ về mặt quy tắc hiện tại để tránh vô tình đưa thêm ràng buộc ngoài hướng dẫn. Nếu data contract sau này yêu cầu những ràng buộc đó, thay đổi phải có mô tả tác động và số dòng bị loại riêng. Không tự biến dữ liệu bất thường thành giá trị có vẻ hợp lệ bằng cách thay ID hoặc thay giá.

category_code được tách theo dấu chấm để tạo cat_l1 và cat_l2; cấp thứ ba trở đi không được đưa vào hai cột dẫn xuất này, nhưng category_code gốc vẫn giữ. cat_l1/cat_l2 null hoặc rỗng được gán unknown. Brand được trim và chuyển chữ thường; brand null/rỗng cũng thành unknown. Xử lý chuỗi rỗng của danh mục/thương hiệu là mở rộng cần xác nhận. Quy tắc này không khôi phục nhãn thật đã thiếu và không chứng minh dữ liệu không còn vấn đề ngữ nghĩa.

Từ event_ts, job tạo event_date kiểu date, event_hour kiểu int từ 0 đến 23 và day_of_week kiểu string theo mẫu E. Cột event_time gốc được bỏ khỏi clean; các cột định danh, event_type, price, category_code và user_session được giữ. event_ts là timestamp, được diễn giải theo session UTC; khi TV4 đọc bằng Spark cũng cần giữ UTC để không đổi ranh giới ngày/giờ theo cấu hình máy khác. [Data Types 3.5.9](https://spark.apache.org/docs/3.5.9/sql-ref-datatypes.html), [Datetime Patterns 3.5.9](https://spark.apache.org/docs/3.5.9/sql-ref-datetime-pattern.html)

## 5.4 Log và số liệu hỗ trợ KB5

Sau mỗi bước, chương trình ghi tên giai đoạn, số dòng còn lại, số loại so với bước trước và thời gian action của giai đoạn. cleaning_metrics.json ghi thêm tổng thời gian, application ID, múi giờ, loại dữ liệu, trạng thái rỗng và các quy tắc đang chờ xác nhận. cleaning_schema.json lưu schema đầu ra. Thời gian từng giai đoạn không phải các phép benchmark độc lập: cache, khởi tạo kế hoạch và tài nguyên được dùng trong cùng ứng dụng; tổng còn bao gồm ghi/đọc lại dữ liệu và các chi phí khác.

Bộ synthetic cũ đã kiểm chứng có 1995 dòng trùng và 2027 dòng giá không hợp lệ sau bỏ trùng. Bảng số liệu này được bàn giao cho TV2 làm dữ liệu hỗ trợ KB5. TV3 không tạo profiling_raw.json hoặc profiling_clean.json giả; tỷ lệ null từng cột và phân bố sự kiện chính thức vẫn chờ job profiling của TV2.

<!-- page -->

## 5.5 Ghi Parquet và bảo toàn dữ liệu

Với dữ liệu sạch không rỗng, job giữ giải pháp repartition theo event_date rồi partitionBy event_date đã được kiểm chứng trên máy Windows. Mode errorifexists từ chối đường dẫn đầu ra đã tồn tại. Báo cáo metrics và schema cũng dùng chế độ tạo mới; không ghi đè nội dung cũ. Nếu một lần xử lý thất bại giữa chừng và để lại đầu ra chưa hoàn tất, người chạy chọn DATA_DIR mới, giữ log để chẩn đoán trước khi quyết định xử lý vùng cũ.

Đầu ra không rỗng của bộ synthetic lớn có 31 thư mục ngày và 31 file Parquet. Cách ghi này được giữ vì đã xử lý được sự cố hàng nghìn file nhỏ ở lượt đầu, không phải vì một file/ngày là mục tiêu tối ưu cố định. Dữ liệu Kaggle chưa có để đánh giá lại kích thước file và tải lệch theo ngày. Các thay đổi tiếp theo về số partition phải dựa trên số đo, không dựa vào kỳ vọng rằng nhiều hoặc ít file luôn nhanh hơn.

Trường hợp raw rỗng hoặc mọi hàng bị loại cần xử lý riêng. Khi không có hàng, không có giá trị ngày để tạo thư mục phân vùng. Job ghi một file Parquet rỗng chứa đầy đủ schema ngay dưới clean/events, để lệnh đọc thông thường vẫn trả DataFrame có cột đúng và count bằng 0. Metrics ghi SUCCESS_EMPTY và empty_output=true. Không tạo một ngày giả hoặc một hàng giả để làm xuất hiện partition. Trạng thái rỗng là kết quả cần downstream xử lý, không đồng nghĩa với dữ liệu kinh doanh đã sẵn sàng có KPI.

## 5.6 Điều phối pipeline và kiểm tra trước khi chạy

Full mode giữ đúng chuỗi ingest → profiling raw → cleaning → profiling clean → aggregation. Trước khi submit, script kiểm tra các file job cần thiết ở host và trong mount container, Compose config, container master đang chạy, tham số memory/master URL, phạm vi DATA_DIR và đầu vào. Với CSV, helper kiểm tra header/thứ tự cột và phát hiện tên synthetic trộn với tên khác. Với clean-only, helper yêu cầu raw/events có Parquet và có thông tin nguồn. Kiểm tra tên file không phát hiện được mọi dữ liệu giả bị đổi tên, nên người cung cấp vẫn phải chịu trách nhiệm xác nhận nguồn.

--ingest-clean chỉ chạy ingest hiện có của TV1 và cleaning TV3; --clean-only chỉ chạy cleaning từ raw. Hai mode này không gọi profiling hoặc aggregation và ghi rõ DONE TV3. --available được giữ làm alias của --ingest-clean để không làm hỏng lệnh cũ; tài liệu mới dùng tên mode tường minh. Không xem mode cá nhân thành công là full pipeline thành công. Full hiện dừng với exit 3 do thiếu 01_profiling.py và 03_aggregation.py.

DATA_DIR và DATA_KIND được truyền vào từng docker exec bằng các phần tử mảng Bash có quote, giúp đường dẫn có khoảng trắng vẫn là một đối số. Git Bash đặt MSYS_NO_PATHCONV=1 để giữ đường dẫn Linux bên trong container. Compose config dùng đường dẫn tương đối docker-compose.yml sau khi script chuyển về repo; cách này tránh lỗi /d/... bị Docker hiểu sai khi chuyển đổi MSYS đã tắt. Cả đường dẫn repo và đường dẫn dữ liệu có khoảng trắng đều được đưa vào phạm vi kiểm thử, nhưng mức kiểm tra tương ứng được công bố riêng.

<!-- page -->

## 5.7 Xử lý lỗi và lưu minh chứng

Mỗi lần gọi pipeline tự tạo một log mới trên host trong data/reports/tv3_pipeline_logs. Log chứa mode, bước đang chạy, tên job, DATA_DIR và exit code cuối. Script dùng set -euo pipefail và kiểm tra kết quả spark-submit; job lỗi sẽ dừng chuỗi và giữ mã thoát đó. Quy ước 2 dành cho tham số không hợp lệ, 3 cho thiếu mã nguồn, 4 cho cấu hình/container/đầu vào hoặc hàng rào dữ liệu không đạt; mã khác từ submit được truyền nguyên. Người chạy PowerShell đọc $LASTEXITCODE ngay sau lệnh Bash; Git Bash đọc $? ngay sau lệnh.

Kiểm thử mock điều khiển shell cố ý làm Docker/submit trả lỗi để kiểm tra nhánh xử lý và thứ tự dừng. Những mock này chỉ tồn tại trong sandbox kiểm thử, không được đặt vào jobs của sản phẩm và không tạo kết quả Spark. Kiểm thử tích hợp thật dùng cụm hiện có, chạy fixture mixed, empty, all-invalid và valid-repeat trong DATA_DIR mới. Mỗi trường hợp được đối chiếu độc lập bằng Python/PyArrow, kiểm tra schema/điều kiện bằng các phép giảm Spark và thử chạy lại để xác nhận dữ liệu/báo cáo được bảo vệ.

Trường hợp valid-repeat giữ các sự kiện khác nhau của cùng một session, có thời gian gần ranh giới ngày và user_id âm để kiểm tra đúng phạm vi quy tắc. Fixture empty kiểm tra header nhưng không có dòng; all-invalid kiểm tra đầu vào có hàng nhưng clean bằng 0. Đây là các kiểm thử nhỏ nhằm bắt lỗi logic và giao diện. Job validate_cleaning cho dữ liệu lớn chỉ trả số liệu tổng hợp về driver; nó không đối chiếu toàn bộ từng hàng raw với clean như bộ fixture và không thay thế profiling chính thức.

## 5.8 Tích hợp với TV2 và TV4

TV2 nhận số dòng từng bước, số loại và các quy tắc mở rộng để xác nhận data contract, sau đó chạy profiling raw/clean thật. TV4 nhận đường dẫn gốc clean/events, schema 14 cột dự kiến, quy ước UTC/ngày/thứ, trạng thái rỗng và phạm vi loại trùng. Đọc đường dẫn gốc giúp Spark nhận diện event_date từ thư mục; không đọc một part file riêng rồi suy rằng cột ngày bị mất. Các metadata về số dòng, nguồn dữ liệu và lần chạy phải đi kèm dữ liệu bàn giao.

Các sửa đổi benchmark TV1 từ phiên trước được giữ nguyên và ghi riêng: force phép tổng hợp bằng collect bảng nhóm nhỏ, ghi cấu hình/timing JSONL và truyền DATA_DIR qua script benchmark. Chúng không được tính là sản phẩm cá nhân TV3 trong gói này và không được chạy lại. Biểu đồ KPI, baseline Pandas và job aggregation vẫn thuộc TV4. Tài liệu bàn giao phân biệt lịch sử thiết lập với phần TV3 vừa hoàn thiện để tránh nhầm trách nhiệm.

Chưa có 2019-Oct.csv thật ở vùng dự án hoặc thư mục được hướng dẫn. Vị trí chờ là D:/Desktop/BigData/data/real_oct_run01/landing/2019-Oct.csv. Sau khi người dùng đăng nhập Kaggle, tải và giải nén vào đó, cần xác nhận header, dung lượng trống/tài nguyên rồi chạy --ingest-clean với DATA_KIND=real trong vùng mới. Hiện chưa có clean/events Kaggle, chưa có kiểm thử trên máy thành viên khác và chưa có xác nhận data contract của TV2. Các phần độc lập đã chuẩn bị không được dùng để đánh dấu toàn bộ nhiệm vụ TV3 đã hoàn tất.
