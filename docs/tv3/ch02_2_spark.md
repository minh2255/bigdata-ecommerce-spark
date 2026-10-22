# 2.2 Apache Spark và cơ chế xử lý phân tán

## 2.2.1 Vai trò của Spark trong đồ án

Đồ án xử lý dữ liệu hành vi thương mại điện tử theo luồng landing → raw → clean → agg. Phần TV3 bắt đầu khi bảng raw/events đã được tạo và kết thúc khi clean/events cùng báo cáo làm sạch đã sẵn sàng. Apache Spark cung cấp môi trường thực thi cho các phép lọc, chuẩn hóa và loại trùng trên những phần dữ liệu được phân phối cho executor. Dữ liệu trung gian và đầu ra được lưu bằng Parquet để các ứng dụng tiếp theo có thể đọc lại mà không phụ thuộc vào tiến trình Python đã tạo chúng.

PySpark là giao diện Python để biểu diễn phép xử lý bằng Spark. Trong chương trình cleaning, đối tượng DataFrame mô tả dữ liệu theo tên cột và kiểu dữ liệu. Các lệnh filter, withColumn và dropDuplicates tạo phép biến đổi trên DataFrame; chúng không tương đương việc nạp toàn bộ bảng vào một đối tượng Pandas trong bộ nhớ của Python driver. Cách biểu diễn có schema giúp Spark SQL biết cấu trúc phép tính để lập và tối ưu kế hoạch thực thi. SQL và DataFrame sử dụng cùng engine xử lý có cấu trúc. [Spark SQL 3.5.9](https://spark.apache.org/docs/3.5.9/sql-programming-guide.html)

Lựa chọn DataFrame phù hợp với dữ liệu đầu vào gồm chín cột đã biết. Ví dụ, product_id và user_id có kiểu long, price có kiểu double, còn event_time ban đầu là string. TV3 không dùng suy luận schema để tự quyết định lại kiểu của raw. Job kiểm tra các cột bắt buộc và kiểu đã đọc từ Parquet; schema khác hướng dẫn sẽ làm chương trình dừng thay vì tiếp tục xử lý với ý nghĩa cột không chắc chắn. Đây là hàng rào tích hợp với ingest, không phải một data contract chính thức đã được TV2 phê duyệt.

## 2.2.2 Driver executor master và worker

Một ứng dụng Spark gồm driver điều phối và các executor thực thi task. Cluster manager cấp tài nguyên cho ứng dụng; driver gửi task tới executor. Worker là nơi có thể chạy executor, còn executor thuộc về một ứng dụng cụ thể. Vì vậy, số worker không đồng nghĩa với số executor của mọi ứng dụng tại mọi thời điểm. [Cluster Mode Overview 3.5.9](https://spark.apache.org/docs/3.5.9/cluster-overview.html)

Trong cấu hình đã kiểm tra, một container chạy Standalone Master và hai container chạy Worker. Mỗi worker khai báo hai core và 2 GiB cho Spark. Lệnh spark-submit được gọi từ container spark-master ở client mode mặc định, nên driver của cleaning nằm trong container đó; tiến trình Master và driver vẫn có vai trò khác nhau. Executor được khởi tạo trên worker để thực thi dữ liệu. Python Standalone không sử dụng cluster deploy mode trong cách chạy này. [Submitting Applications 3.5.9](https://spark.apache.org/docs/3.5.9/submitting-applications.html)

Các container cùng mount thư mục dự án data vào /data. Do đó, đường dẫn /data/... phải có cùng nội dung trên driver và worker. Đây là cụm nhiều tiến trình/container trên một máy Windows, không phải nhiều máy vật lý độc lập. Cấu hình chứng minh việc điều phối và phân phối task, nhưng chưa chứng minh khả năng chịu lỗi của lưu trữ phân tán hay mở rộng ngang sang nhiều máy.

<!-- page -->

## 2.2.3 Lazy evaluation transformation và action

Spark sử dụng cơ chế đánh giá trì hoãn: phép biến đổi được ghi nhận trước, còn việc tính toán được kích hoạt khi một action cần kết quả. Sự phân biệt này giải thích vì sao việc tạo một chuỗi filter có thể rất nhanh, trong khi count hoặc ghi Parquet mới làm xuất hiện nhiều job và task trên giao diện ứng dụng. Một action cũng không nhất thiết tương ứng duy nhất một stage. [RDD Programming Guide 3.5.9](https://spark.apache.org/docs/3.5.9/rdd-programming-guide.html)

Trong cleaning, câu lệnh raw.dropDuplicates() mô tả yêu cầu loại bản sao theo toàn bộ cột raw. Các withColumn tiếp theo mô tả việc chuyển event_time sang event_ts và tạo cột thời gian. Điều kiện filter mô tả các dòng được giữ lại. Những phép biến đổi này được kết hợp thành kế hoạch, thay vì yêu cầu lập trình viên tự chia dữ liệu và gửi từng nhóm bản ghi sang worker. Đối với dữ liệu batch, dropDuplicates mặc định xét toàn bộ cột khi không truyền subset. [API dropDuplicates 3.5.9](https://spark.apache.org/docs/3.5.9/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.dropDuplicates.html)

TV3 cố ý đặt count sau từng giai đoạn để có số liệu giải thích cho KB5. Ví dụ, bộ synthetic đã kiểm chứng có 201995 dòng raw, còn 200000 dòng sau bỏ trùng và 197973 dòng sau lọc giá. Các số đếm này là action thật, có chi phí thực thi. Vì vậy, 32.46 giây của bản cleaning ban đầu được hiểu là thời gian xử lý có ghi số liệu kiểm tra và ghi/đọc lại đầu ra; không gọi đó là thời gian của riêng phép lọc hay một phép đo tối ưu thuần túy.

Để giảm tính lại toàn bộ chuỗi trước mỗi count, chương trình persist giai đoạn đang kiểm tra bằng MEMORY_AND_DISK, materialize bằng count, rồi unpersist giai đoạn trước. Việc persist không có nghĩa mọi dữ liệu luôn nằm hoàn toàn trong RAM; mức lưu trữ được chỉ định cho phép sử dụng đĩa khi cần. Cache chỉ phục vụ ứng dụng hiện tại và được giải phóng khi kết thúc. [API persist 3.5.9](https://spark.apache.org/docs/3.5.9/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.persist.html)

Spark SQL cho phép diễn đạt cùng loại phép xử lý có cấu trúc bằng câu truy vấn SQL hoặc DataFrame. Phần cleaning dùng các hàm có sẵn như trim, lower, split, hour và to_date, không chuyển từng dòng sang vòng lặp Python trên driver. Phần tổng hợp KPI bằng SQL thuộc TV4; TV3 chuẩn bị cột và kiểu dữ liệu cho giao diện đó. Chương trình chỉ đưa các số đếm hoặc bản ghi kiểm tra nhỏ về driver, không collect hoặc toPandas toàn bộ tập dữ liệu lớn.

## 2.2.4 Job stage và task trong minh chứng

Giao diện Jobs cho biết các action đang hoặc đã thực hiện; Stages cho biết các giai đoạn cùng số task; SQL/DataFrame giúp đối chiếu kế hoạch xử lý có cấu trúc. Ảnh đã chụp trong lần chạy synthetic thể hiện task trên hai worker. Khi trình bày, cần phân biệt ảnh quan sát trực tiếp này với một tuyên bố về tốc độ trên dữ liệu Kaggle. Application UI ở cổng 4040 chỉ tồn tại trong vòng đời driver; Master UI ở 8080 tiếp tục hiển thị các worker khi ứng dụng đã xong.

<!-- page -->

## 2.2.5 Shuffle và hai nghĩa của partition

Shuffle là việc phân phối lại dữ liệu giữa các partition để các bản ghi cần xử lý cùng nhau được đưa về vị trí phù hợp. Nó có thể phát sinh trao đổi dữ liệu, I/O và chi phí bộ nhớ. Trong cleaning, loại trùng toàn bộ bảng và repartition theo ngày là các điểm cần quan sát khi đánh giá chi phí. Với dữ liệu lớn, không thể chỉ nhìn số câu lệnh Python để ước lượng thời gian; cần xem kế hoạch, số task và dữ liệu trao đổi thực tế.

Partition của quá trình thực thi là phần dữ liệu mà task xử lý. Partition của bảng lưu trên đĩa là cách tổ chức thư mục theo giá trị cột, ví dụ event_date=2019-10-01. Hai khái niệm có liên hệ nhưng không đồng nhất: thêm partitionBy khi ghi không tự bảo đảm một ngày có một file, và một thư mục ngày có thể chứa nhiều part file. Spark có thể nhận diện cột phân vùng từ cấu trúc thư mục khi đọc đường dẫn gốc của bảng. [Parquet Files 3.5.9](https://spark.apache.org/docs/3.5.9/sql-data-sources-parquet.html)

Trong lần thử ban đầu, nhiều partition thực thi cùng ghi các ngày khác nhau, tạo khoảng 6200 file nhỏ. Bước commit trên bind mount Windows chậm nên ứng dụng đó được chủ động dừng; log được giữ và không tính là lần chạy thành công. TV3 sau đó thêm repartition(event_date) trước khi ghi. Lần chạy lại dùng cùng CSV, có _SUCCESS và 31 file cho 31 ngày. API repartition thực hiện phân phối lại theo các biểu thức cột đã chỉ định. [API repartition 3.5.9](https://spark.apache.org/docs/3.5.9/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.repartition.html)

Quan sát này chỉ hỗ trợ lựa chọn hiện tại cho dữ liệu synthetic nhỏ trên máy đã kiểm tra. Nó không chứng minh một file mỗi ngày là cấu hình tối ưu cho dữ liệu thật. Nếu một ngày có quá nhiều bản ghi, gom theo ngày có thể tạo tải lệch hoặc file lớn. Khi có Kaggle, cần đo kích thước file, thời gian ghi, spill và tài nguyên trước khi quyết định điều chỉnh số partition hay chiến lược ghi. AQE cũng có thể thay đổi partition lúc thực thi; không được suy số task thực tế chỉ từ một giá trị cấu hình. [Performance Tuning 3.5.9](https://spark.apache.org/docs/3.5.9/sql-performance-tuning.html)

## 2.2.6 Thời gian UTC và ranh giới dữ liệu lớn

Job đặt spark.sql.session.timeZone=UTC, bỏ hậu tố UTC trước khi parse theo mẫu yyyy-MM-dd HH:mm:ss, rồi tạo ngày và giờ từ event_ts. try_to_timestamp trả null cho đầu vào không parse được để bước lọc loại bỏ có kiểm soát. day_of_week được định dạng bằng E và có giá trị chữ viết tắt như Mon hoặc Tue; không phải số thứ tự ngày trong tuần. [API try_to_timestamp 3.5.9](https://spark.apache.org/docs/3.5.9/api/python/reference/pyspark.sql/api/pyspark.sql.functions.try_to_timestamp.html), [Datetime Patterns 3.5.9](https://spark.apache.org/docs/3.5.9/sql-ref-datetime-pattern.html)

Ranh giới của kiểm thử cũng cần được công bố. Bộ fixture nhỏ được đối chiếu toàn bộ giá trị bằng Python/PyArrow, có giới hạn 10000 dòng trước khi nạp danh sách. Kiểm tra tập dữ liệu lớn dùng các phép giảm phân tán để đếm vi phạm, đối chiếu schema, cột thời gian và số dòng; chỉ một hàng số liệu tổng hợp được trả về driver. Kiểm tra điều kiện trên đầu ra không tự chứng minh tương đương từng dòng với raw, nên hai phạm vi kiểm tra được ghi riêng. Các kết quả hiện có là synthetic; dữ liệu thật và chạy lại trên máy thành viên khác vẫn cần được xác nhận.
