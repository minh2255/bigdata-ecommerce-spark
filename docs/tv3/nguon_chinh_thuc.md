# Tài liệu tham khảo chính thức và phạm vi sử dụng

Các trang dưới đây được kiểm tra ngày 18 tháng 10 năm 2026, dùng phiên bản Spark 3.5.9 tương ứng image đang chạy. Nội dung trong báo cáo được diễn giải và liên hệ với code; không trích nguyên đoạn tài liệu. Số liệu thực nghiệm lấy từ log/JSON của repo, không lấy từ trang tài liệu kỹ thuật.

1. [Cluster Mode Overview](https://spark.apache.org/docs/3.5.9/cluster-overview.html): driver, executor, cluster manager, worker, job/stage/task và UI.
2. [Submitting Applications](https://spark.apache.org/docs/3.5.9/submitting-applications.html): spark-submit, client mode và giới hạn Standalone Python cluster deploy mode.
3. [Spark SQL Guide](https://spark.apache.org/docs/3.5.9/sql-programming-guide.html): xử lý dữ liệu có cấu trúc, DataFrame và engine SQL.
4. [RDD Programming Guide](https://spark.apache.org/docs/3.5.9/rdd-programming-guide.html): lazy evaluation, transformation/action, shuffle và lưu trữ trung gian.
5. [Parquet Files](https://spark.apache.org/docs/3.5.9/sql-data-sources-parquet.html): nhận diện cột phân vùng, kiểu cột phân vùng và basePath.
6. [Generic Load Save Functions](https://spark.apache.org/docs/3.5.9/sql-data-sources-load-save-functions.html): chế độ ghi và xử lý đường dẫn đã tồn tại.
7. [Datetime Patterns](https://spark.apache.org/docs/3.5.9/sql-ref-datetime-pattern.html): mẫu ngày/giờ và ký hiệu E cho tên thứ.
8. [try_to_timestamp](https://spark.apache.org/docs/3.5.9/api/python/reference/pyspark.sql/api/pyspark.sql.functions.try_to_timestamp.html): parse timestamp an toàn với dữ liệu không hợp lệ.
9. [dropDuplicates](https://spark.apache.org/docs/3.5.9/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.dropDuplicates.html): loại trùng DataFrame batch theo toàn bộ cột hoặc subset.
10. [persist](https://spark.apache.org/docs/3.5.9/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.persist.html): materialize/persist và mức lưu trữ.
11. [repartition](https://spark.apache.org/docs/3.5.9/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.repartition.html): phân phối lại DataFrame theo biểu thức cột.
12. [Performance Tuning](https://spark.apache.org/docs/3.5.9/sql-performance-tuning.html): partition, cấu hình và AQE.
13. [Data Types](https://spark.apache.org/docs/3.5.9/sql-ref-datatypes.html): kiểu dữ liệu Spark SQL, date và timestamp.

Tài liệu nhóm đã đọc lại: D:/Desktop/BD_PhanCong.docx, BD_Project.docx và BD_CaiDat.docx. Phân công xác định TV3 chịu trách nhiệm cleaning, run_pipeline, Chương 2.2, Chương 5, phụ lục và hỗ trợ KB5. Các hướng dẫn nhóm về merge/commit hoặc xóa dữ liệu không được thực hiện tự động; phiên làm việc này giữ nguyên thay đổi, không commit/push/merge và không ghi đè dữ liệu cũ.
