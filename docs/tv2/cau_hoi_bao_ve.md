# Câu hỏi bảo vệ đồ án Spark — phần ôn tập của TV2

Bản soạn ngày 11/11/2026, đối chiếu source trên `main` commit `bab9f31` và bằng chứng TV2. Câu trả lời ngắn để luyện nói; chưa xác nhận sinh viên đã ôn hoặc thuộc bài. Các giới hạn của source dưới đây là nhận xét từ đọc code, chưa được sửa trong bước này.

## Giải thích toàn bộ pipeline

**Hỏi: Em trình bày toàn bộ pipeline, không chỉ phần TV2?**

“Landing giữ CSV nguồn. Ingest đọc schema cố định và ghi raw Parquet. Profiling raw đo chất lượng đầu vào. Cleaning dedup, lọc lỗi theo contract, chuẩn hóa và ghi clean theo ngày. Profiling clean kiểm tra bất biến. Aggregation tạo KPI. Các job benchmark đo truy vấn theo cấu hình; job charts đọc bảng tổng hợp và báo cáo để vẽ biểu đồ.”

| Khâu | File thực tế | Đầu vào → đầu ra | Trách nhiệm chính |
|---|---|---|---|
| Chuẩn bị và môi trường | Dockerfile, docker-compose; scripts/generate_data.py | Nguồn thật hoặc synthetic có truth → landing và metadata | TV1 môi trường; TV2 dữ liệu |
| Ingest | jobs/00_ingest.py | landing/*.csv → raw/events, reports/ingest_log.csv | TV1 |
| Profiling trước/sau | jobs/01_profiling.py raw hoặc clean | Parquet từng tầng → reports/profiling_{layer}.json | TV2 |
| Cleaning | jobs/02_cleaning.py | raw/events → clean/events, metrics và schema | TV3 |
| Aggregation | jobs/03_aggregation.py | clean/events → agg/daily_kpi, category_kpi, brand_kpi, funnel, hourly | TV4 |
| Benchmark truy vấn | jobs/04_benchmark.py | clean/events → reports/benchmark.csv và benchmark_runs.jsonl | TV1 |
| Samples/KB3 | jobs/make_sample.py; jobs/kb3_csv_vs_parquet.py | clean → samples; CSV/raw → báo cáo KB3 | TV2 |
| Pandas và biểu đồ | jobs/pandas_baseline.py; jobs/05_charts.py | samples hoặc agg/reports → báo cáo và PNG | TV4 |

**Hỏi: `run_pipeline.sh --full` đã chạy tất cả các hàng trong bảng chưa?**

Chưa. Source chạy theo thứ tự ingest → profiling raw → cleaning → profiling clean → aggregation. Benchmark, make_sample, KB3 và charts được gọi riêng. Log M1 chỉ chứng minh chuỗi `--full` đó hoàn tất, không chứng minh mọi thực nghiệm đã chạy trong cùng lệnh.

## Parquet, partition và cách Spark thực thi

**Hỏi: Vì sao chọn Parquet?**

Parquet lưu theo cột, có schema và hỗ trợ đọc cột cần thiết. Trong KB3, CSV/raw Parquet lần lượt là 5.668.612.855/1.465.175.946 byte; tỷ số nguồn là 3,87×. Đây là kết quả trên dữ liệu và môi trường đã ghi, không phải tỷ lệ cố định cho mọi dataset. [Tài liệu Parquet của Spark](https://spark.apache.org/docs/3.5.9/sql-data-sources-parquet.html).

**Hỏi: Partition là gì? Có phải một thư mục ngày luôn là một task?**

Partition xử lý là phần dữ liệu Spark phân công cho task. Partition thư mục theo ngày là cách bố trí lưu trữ. Số file và cách chia khi đọc có thể khiến chúng không tương ứng một-một. [Partition discovery](https://spark.apache.org/docs/3.5.9/sql-data-sources-parquet.html#partition-discovery).

**Hỏi: Vì sao clean dùng `partitionBy("event_date")`?**

Code cleaning ghi theo ngày để truy vấn có điều kiện ngày có thể bỏ qua thư mục không cần đọc. Phải đọc từ gốc `clean/events` để nhận diện cột partition. Trong mẫu do make_sample tạo, event_date là cột thường; mẫu không partitionBy ngày. Xem `02_cleaning.py` và `make_sample.py`.

**Hỏi: Transformation và action khác nhau thế nào?**

Transformation xây kế hoạch; action yêu cầu kết quả và kích hoạt tính toán. Trong repo, filter/withColumn tạo kế hoạch; count/collect/write yêu cầu thực thi. Không đo thời gian chỉ quanh việc khai báo truy vấn. [Spark: operations](https://spark.apache.org/docs/3.5.9/rdd-programming-guide.html#rdd-operations).

**Hỏi: Ví dụ narrow và wide trong đồ án?**

Filter thường xử lý trong partition hiện có. GroupBy, dedup hoặc repartition thường cần gom lại dữ liệu theo khóa. Cần xem physical plan thực tế để xác nhận trao đổi dữ liệu. [Spark: shuffle](https://spark.apache.org/docs/3.5.9/rdd-programming-guide.html#shuffle-operations).

**Hỏi: Shuffle là gì, vì sao tốn tài nguyên?**

Shuffle phân phối lại dữ liệu giữa partition; phát sinh trao đổi, serialize và có thể ghi đĩa. Trong code, dedup và tổng hợp theo khóa là các vị trí cần chú ý. [Spark: shuffle](https://spark.apache.org/docs/3.5.9/rdd-programming-guide.html#shuffle-operations).

**Hỏi: Tăng shuffle partitions có luôn nhanh hơn không?**

Không. Task nhỏ hơn có thể giảm áp lực bộ nhớ nhưng tăng chi phí lập lịch. AQE còn có thể gộp partition sau shuffle; phải xem cấu hình và metrics thực tế. [Spark: performance tuning](https://spark.apache.org/docs/3.5.9/sql-performance-tuning.html).

**Hỏi: `repartition` khác `coalesce` thế nào trong repo?**

Cleaning dùng repartition theo event_date trước khi ghi; make_sample dùng coalesce(1) để gom mỗi mẫu vào một file. Cách gom mẫu tiện cho Pandas nhưng đưa khâu ghi về ít task, nên không áp dụng tùy tiện cho dữ liệu lớn. [Spark: coalesce/repartition](https://spark.apache.org/docs/3.5.9/rdd-programming-guide.html#transformations).

**Hỏi: Vì sao cleaning dùng persist rồi unpersist?**

Code đếm sau mỗi bước và còn dùng dữ liệu cho bước tiếp. Persist MEMORY_AND_DISK hỗ trợ tái sử dụng; sau khi bước mới được materialize bằng count, code unpersist bước trước. Đổi lại có chi phí lưu trữ. [Spark: caching](https://spark.apache.org/docs/3.5.9/sql-performance-tuning.html#caching-data-in-memory).

**Hỏi: Driver, master, worker và executor làm gì?**

Driver điều phối ứng dụng; master standalone cấp tài nguyên; worker chạy executor; executor thực hiện task và lưu dữ liệu của ứng dụng. Hai worker Docker cùng máy vẫn dùng chung phần cứng. [Spark programming guide](https://spark.apache.org/docs/3.5.9/rdd-programming-guide.html).

## Dữ liệu, contract và chất lượng

**Hỏi: Vì sao phải có raw nếu đã có landing?**

Landing giữ CSV nguồn; raw là bản đã parse bằng schema cố định và lưu Parquet để phân tích, làm sạch lại. “Không cleaning ở raw” không có nghĩa mọi chuỗi CSV được giữ nguyên: chuỗi lỗi có thể thành null khi parse. Xem `00_ingest.py` và JSON synthetic M1.

**Hỏi: Vì sao dedup trước chuẩn hóa?**

Contract xét dòng raw giống hoàn toàn. Hai dòng chỉ khác chữ hoa/thường có thể giống nhau sau chuẩn hóa; không tự dedup lại clean vì sẽ đổi luật đã thống nhất. Xem `docs/data_contract.md`.

**Hỏi: Sao không xóa hết dòng thiếu brand hoặc category?**

Thông tin mô tả thiếu chưa làm sự kiện vô nghĩa. Code giữ dòng, chuẩn hóa brand và cat_l1/cat_l2 thành unknown; category_code gốc có thể vẫn null. Cần tách unknown khi giải thích KPI theo danh mục/thương hiệu.

**Hỏi: Vì sao loại giá bằng 0, âm, NaN hoặc vô hạn?**

Đó là quy ước hợp lệ của contract cho bài toán này. Cleaning chỉ giữ giá hữu hạn dương; profiling kiểm tra lại. Không coi quy ước đó là luật bắt buộc của mọi hệ thống thương mại điện tử.

**Hỏi: NaN, null và chuỗi trắng khác nhau ra sao?**

Chúng cần bộ đếm riêng. M1 truth chèn `218` giá nan; raw ghi `220` price null và `0` price_nan. Raw cũng có `198` session null và `212` session trắng. Parser và bản trùng làm số quan sát khác số chèn. Nguồn: các JSON trong `docs/evidence/tv2/m1_20261110_231427/`.

**Hỏi: Có bắt ID dương hoặc session là UUID không?**

Không loại theo hai điều kiện này. Contract chỉ theo dõi chúng trong profiling; user_id null và session thiếu/trắng vẫn bị loại. Session là khóa nhóm nhiều sự kiện, không phải khóa duy nhất của từng dòng.

**Hỏi: Vì sao tổng lỗi raw không bằng tổng dòng bị loại?**

Lỗi có thể giao nhau và chỉ bị loại ở bước đầu gặp. Raw có 68.673 giá không dương; sau dedup, bước giá loại 68.670. Chênh `3` thuộc phần đã bị dedup. Nguồn: profiling_raw.json và cleaning_metrics_merged.json.

**Hỏi: Vì sao chia lát ngày? Có đổi kết quả không?**

Note metrics ghi cleaning toàn tháng hết bộ nhớ. Chia lát giảm lượng dữ liệu mỗi lần xử lý. Dedup toàn dòng được bảo toàn nếu lát bao phủ nguồn, không chồng lấn và dòng trùng luôn cùng lát do có cùng event_time. Không suy rộng cho khóa dedup nghiệp vụ có thể lặp ở nhiều ngày.

**Hỏi: Chứng minh chia lát không mất dòng thế nào?**

Đối chiếu tổng counts các lát với raw và tổng clean. JSON gộp ghi 42.448.764 raw → 42.418.544 sau dedup → 42.349.872 clean. Kiểm tra invariants từng lát và toàn tháng; không chỉ dựa vào exit code.

**Hỏi: Có chắc dòng trùng tập trung ở cart không?**

Chưa có bảng chéo trực tiếp để khẳng định. Cart giảm 28.224 dòng qua toàn cleaning; đây không phải số trùng riêng. Muốn kết luận cần đếm theo event_type trước và ngay sau dedup. Xem audit M3 và bước 5b.

**Hỏi: Tập clean rỗng có phải job lỗi?**

Không nhất thiết. Cleaning có nhánh SUCCESS_EMPTY, ghi Parquet rỗng mang schema; profiling xử lý tập rỗng. Các job sau phải có chính sách riêng, không giả định luôn có dữ liệu. Không khẳng định mọi downstream đã test tập rỗng chỉ vì cleaning đã hỗ trợ.

**Hỏi: Tại sao phải thống nhất UTC?**

Ngày, giờ và KPI phụ thuộc múi giờ. Cleaning/profiling và make_sample đặt UTC tường minh. Aggregation hiện chưa đặt timezone tường minh trong builder; không nói mọi job đều đã làm vậy. Cần thống nhất cấu hình submit hoặc source khi dùng các phép thời gian.

## Aggregation và ý nghĩa KPI của TV4

**Hỏi: TV4 tính những bảng nào?**

Daily KPI đếm view/cart/purchase, cộng giá purchase và đếm user distinct; category/brand KPI tính trên purchase; funnel đếm session distinct theo event_type; hourly đếm sự kiện theo giờ và loại. Tất cả đọc clean, ghi vào agg. Xem `03_aggregation.py`.

**Hỏi: Trường orders có phải số đơn hàng thật?**

Code dùng count(*) của sự kiện purchase. Dataset không có order_id để chứng minh mỗi dòng là một đơn hàng độc lập; nên giải thích là số sự kiện purchase theo quy ước đồ án.

**Hỏi: Funnel hiện tại có chứng minh người dùng đi đủ view → cart → purchase theo thứ tự không?**

Không. Code chỉ đếm session distinct trong từng loại sự kiện. Muốn xác định chuyển đổi tuần tự phải xét cùng session và thứ tự thời gian; bảng hiện tại chưa làm việc đó.

**Hỏi: Doanh thu trong KPI khác tổng giá benchmark không?**

Có. Aggregation chỉ cộng price của purchase. `04_benchmark.py` cộng price theo ngày/event_type cho mọi loại sự kiện. Tên revenue trong truy vấn benchmark không làm tổng giá view/cart trở thành doanh thu kinh doanh.

**Hỏi: Làm sạch có làm doanh thu thay đổi không?**

Loại purchase trùng có thể giảm phần bị đếm lặp. Nguồn TV2 chưa có tổng doanh thu trước/sau để định lượng; không trả lời “không ảnh hưởng” khi chưa có phép đối chiếu đó.

## Benchmark, kiểm chứng và giới hạn kết quả

**Hỏi: `04_benchmark.py` đo gì, action ở đâu?**

GroupBy event_date/event_type, tính count và sum(price), rồi collect kết quả nhóm nhỏ. Timer bắt đầu sau tạo DataFrame; action còn thực hiện đọc dữ liệu và truy vấn theo kế hoạch lazy. Thời gian không gồm khởi động Spark và khám phá schema. `benchmark_runs.jsonl` ghi rõ timing_scope.

**Hỏi: Vì sao không thay collect bằng count cho benchmark này?**

Source có chú thích: count số nhóm có thể khiến optimizer bỏ các phép tổng hợp không cần dùng. Collect lấy các cột kết quả nên buộc tính cả n và tổng giá. Không collect toàn bộ events lên driver.

**Hỏi: KB1/KB2/KB6 thay đổi gì?**

`run_benchmarks.sh` lần lượt thay fraction, tổng core và shuffle partitions, lặp đo theo cấu hình script. Đọc cả AQE, cores và số dòng thực dùng trong JSONL; không coi nhãn cấu hình là bằng chứng tài nguyên đã thực dùng. Trong phần này không tuyên bố kết quả của các KB nếu chưa có CSV/JSON tương ứng.

**Hỏi: Spark chắc chắn nhanh hơn Pandas không?**

Không. Dữ liệu nhỏ có thể chịu overhead Spark; kết luận phải dựa trên cùng dữ liệu, truy vấn, môi trường và phạm vi đo. Các samples đọc được mới chứng minh khả năng đọc, chưa chứng minh bên nào nhanh hơn.

**Hỏi: So sánh Pandas–Spark trong source đã công bằng chưa?**

Cần kiểm tra thêm: Spark sample từ clean trong action, còn Pandas đọc samples đã lưu; cùng fraction hoặc seed chưa chứng minh cùng tập dòng. Cần cho hai bên đọc cùng mẫu cố định và đối chiếu output trước khi so thời gian.

**Hỏi: Có rủi ro khi ghép báo cáo benchmark không?**

Có. Spark ghi benchmark.csv với label/fraction/cores/seconds; Pandas ghi cùng tên với engine/fraction/run/seconds; charts lại cần engine. Không trộn hai schema vào cùng file. Cần tách nguồn hoặc chuẩn hóa trước khi ghép, không tự suy ra biểu đồ hợp lệ chỉ từ tên file.

**Hỏi: KB3 cho phép kết luận gì?**

CSV/Parquet mean count là 39,7/2,2 giây, mean sum(price) là 56,3/3,2 giây theo kb3.csv. Chỉ kết luận trong môi trường đã đo; cache và metadata có thể ảnh hưởng. Không dùng tỷ lệ count để đại diện cho mọi truy vấn.

**Hỏi: Chạy xong pipeline có chứng minh dữ liệu và KPI đều đúng không?**

Exit code và marker chứng minh thực thi/ghi thành công. Chất lượng còn cần truth, counts và invariants; công thức KPI cần đối chiếu nghiệp vụ. M1 full thành công chưa thay thế review TV1 hoặc kiểm toán aggregation TV4.

**Hỏi: Làm sao tái lập mà không mất bằng chứng?**

Chọn DATA_DIR mới, lưu nguồn/seed/commit/cấu hình cùng JSON, CSV và log. Pipeline có preflight; ingest và aggregation trực tiếp vẫn dùng overwrite nên không gọi lại vào output cũ. Không commit data hoặc token, không push/merge khi chưa được người dùng đồng ý.

## Nguồn mở khi giảng viên hỏi sâu

- Mã nguồn: `jobs/00_ingest.py` đến `04_benchmark.py`, `pandas_baseline.py`, `make_sample.py`, `kb3_csv_vs_parquet.py`, `05_charts.py`; scripts/run_pipeline.sh và run_benchmarks.sh.
- Luật nghiệp vụ: `docs/data_contract.md`.
- Số liệu: `docs/evidence/tv2/` với profiling, cleaning metrics, kb3.csv, m1_20261110_231427, m2_samples_validation_20261110.json.
- Các phát hiện còn mở: `docs/evidence/tv2/audit_5b_review_20261111.md`.
- Khái niệm Spark được đối chiếu tài liệu chính thức 3.5.9 theo các liên kết trong câu trả lời; không lấy tài liệu lý thuyết thay cho số đo của đồ án.

## Phần người dùng tự luyện

- [ ] Giải thích pipeline bằng lời của mình, chỉ đúng file và output.
- [ ] Phân biệt partition lưu trữ với partition xử lý, transformation với action.
- [ ] Giải thích giới hạn RAM, điều kiện chia lát và lỗi giao nhau bằng nguồn thật.
- [ ] Trả lời đúng giới hạn của orders, funnel và so sánh benchmark.

Tin copy nếu cần báo tình trạng:

> TV2 đã có `docs/tv2/cau_hoi_bao_ve.md` bao phủ toàn pipeline và các câu hỏi Spark, dữ liệu, KPI, benchmark. Có ghi rõ những giới hạn đọc được từ source; chưa sửa code và chưa xác nhận đã ôn xong.
