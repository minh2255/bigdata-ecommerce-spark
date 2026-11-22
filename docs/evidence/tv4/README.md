# Minh chứng TV4

Toàn bộ số liệu thật nằm ở [`real/`](real/) (Kaggle 2019-Oct, 42.349.872 dòng clean). Không để file kết quả ở thư mục gốc này, tránh hai bản trùng.

- `real/`: lần chạy 22/11/2026 vùng `/data/real_oct_tv4_20261122` (KPI 14/14, KB4 mẫu 1%/5%/10%, biểu đồ, `samples_log.csv`, `source.json`), dùng trong báo cáo.
- `real/brand_revenue.png`, `real/hourly_activity.png`, `real/conversion_rate.json`: biểu đồ và tỷ lệ chuyển đổi bổ sung từ nhánh `tv4/real-data-kpi`.
- `real/run_real_oct_full/`: lần chạy độc lập khác trên vùng `/data/real_oct_full` (`kpi_check.json`, `kb4_benchmark.csv`), dùng để đối chiếu chéo.
- Kết quả cũ trên synthetic (19.627 dòng) đã bỏ khỏi thư mục này, vẫn xem được trong lịch sử Git (commit `da0daef`).
