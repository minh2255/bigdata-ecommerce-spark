# TV3 tự chạy cleaning trên dữ liệu Kaggle thật (22/11/2026)

- Nguồn: `2019-Oct.csv` (5.668.612.855 byte), header đúng contract TV2. DATA_DIR gốc `/data/real_oct_tv3`, DATA_KIND=real.
- Ingest: exit 0, 3 phút 33 giây. Chia 8 lát theo ngày bằng `jobs/slice_raw_by_day.py` (7 phút 10 giây); tổng raw 42.448.764.
- Cleaning `--clean-only` từng lát (`/data/tv3_real_s1..s8`), tuần tự, cả 8 exit 0, mỗi lát khoảng 100-150 giây.
- Tổng: raw 42.448.764, written 42.349.872. Khớp `docs/evidence/tv2/cleaning_metrics_merged.json`; từng lát cũng khớp số TV2.
- Lưu ý: lát 4-6 chạy khi phiên làm việc bị khởi động lại, vẫn exit 0. Một lệnh chạy lát 5 thứ hai bị cơ chế chống ghi đè chặn (exit 4), không đổi dữ liệu.
- Chưa làm: ảnh Spark UI, xác nhận của TV4, chạy lại trên máy thành viên khác.

## Ảnh Spark UI lúc cleaning dữ liệu thật

Chụp ngày 22/11/2026 trong lượt chạy riêng `--clean-only` trên `/data/tv3_real_shot` (raw copy từ lát 4 của dữ liệu Kaggle thật, exit 0, ứng dụng `02_cleaning`). Đây là lượt chạy lại chỉ để chụp ảnh, không tính vào tổng 8 lát ở trên.

- `spark_ui_master_real.png`: Spark Master, 2 worker ALIVE, `02_cleaning` RUNNING.
- `spark_ui_jobs_real.png`: tab Jobs của ứng dụng `02_cleaning`.
- `spark_ui_executors_real.png`: 2 executor Active, 4 core, 2.225 task hoàn thành, 0 lỗi.
- `spark_ui_stages_real.png`: 22 stage hoàn thành, stage ghi Parquet có output 304,8 MiB.

Tab SQL/DataFrame không mở được (ERR_EMPTY_RESPONSE), không có ảnh.
