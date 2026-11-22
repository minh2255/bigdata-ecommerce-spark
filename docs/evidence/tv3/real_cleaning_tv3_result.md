# TV3 tự chạy cleaning trên dữ liệu Kaggle thật (22/11/2026)

- Nguồn: `2019-Oct.csv` (5.668.612.855 byte), header đúng contract TV2. DATA_DIR gốc `/data/real_oct_tv3`, DATA_KIND=real.
- Ingest: exit 0, 3 phút 33 giây. Chia 8 lát theo ngày bằng `jobs/slice_raw_by_day.py` (7 phút 10 giây); tổng raw 42.448.764.
- Cleaning `--clean-only` từng lát (`/data/tv3_real_s1..s8`), tuần tự, cả 8 exit 0, mỗi lát khoảng 100-150 giây.
- Tổng: raw 42.448.764, written 42.349.872. Khớp `docs/evidence/tv2/cleaning_metrics_merged.json`; từng lát cũng khớp số TV2.
- Lưu ý: lát 4-6 chạy khi phiên làm việc bị khởi động lại, vẫn exit 0. Một lệnh chạy lát 5 thứ hai bị cơ chế chống ghi đè chặn (exit 4), không đổi dữ liệu.
- Chưa làm: ảnh Spark UI, xác nhận của TV4, chạy lại trên máy thành viên khác.
