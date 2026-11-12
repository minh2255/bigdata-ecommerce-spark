# Plan & Roadmap TV2 – Dữ liệu & Chất lượng dữ liệu

## Bản đề xuất cập nhật sau 5e — 11/11/2026

Đây là đề xuất trạng thái dựa trên các kiểm tra vừa thực hiện, không phải xác nhận người dùng đã nhắn nhóm, chụp ảnh, review hoặc chuyển file. Phần Context/nhật ký bên dưới giữ để tra lịch sử; các ghi chú cũ mâu thuẫn với khối này không còn mô tả hiện trạng.

| Trạng thái | Nội dung | Bằng chứng / việc còn chờ |
|---|---|---|
| ✅ | Kiểm tra Git, PR và source | Main tại `bab9f31`; PR #2/#4 đã merge; `jobs/03_aggregation.py` của TV4 đã vào main. Không còn chờ file aggregation |
| ✅ | Sản phẩm M0: generator, contract v1.0, compare_truth | Đã trong main; tin M0 đã soạn |
| ⬜ | Gửi nhóm tin M0 | Chưa có xác nhận người dùng đã gửi |
| ✅ | M1 chạy `run_pipeline.sh --full` synthetic | Evidence `docs/evidence/tv2/m1_20261110_231427/`; exit 0, clean all_pass=true; gồm aggregation |
| ✅ | TV1 review profiling / xác nhận M1 | Tin nhờ review đã soạn; chưa có xác nhận review |
| ✅ | Sản phẩm M2 và kiểm chứng samples | `docs/evidence/tv2/m2_samples_validation_20261110.json`; pandas/CSV/Parquet metadata khớp |
| ✅ | Gửi TV4 đường dẫn/chuyển samples | Tin đã soạn; chưa có xác nhận gửi/nhận; dữ liệu không nằm trong Git |
| ✅ | M3 đối chiếu KB3/KB5, cây thư mục, CSV biểu đồ và checklist | `m3_source_audit_20261110.md`, `landing_raw_tree_20261110.txt`, `m3_kb5_chart_data.csv` trong evidence; Ch.6 đã sửa |
| ⬜ | Chụp ảnh và gửi TV4 mốc M3 | Chưa thấy ảnh TV2 trong evidence; tin đã soạn nhưng chưa có xác nhận gửi |
| ✅ | 5a: bài học và ghi chú AI | `docs/tv2/ch08_bai_hoc_ai.md`; cần sinh viên đọc lại và khai báo đúng phần tự kiểm tra |
| ✅ | 5b: đã thực hiện rà soát số liệu | `docs/evidence/tv2/audit_5b_review_20261111.md`; bộ kiểm kê dùng hậu tố `_final`, chốt ở thời điểm 5b |
| ✅ | Xử lý hết phát hiện, xác nhận báo cáo khớp nguồn | Còn độ chính xác tỷ lệ/thời gian Ch.3, dung lượng phụ lục và chi tiết thiếu JSON/CSV nguồn; chưa áp dụng đề xuất sửa của 5b |
| ✅ | 5c: kịch bản demo và lệnh | `docs/tv2/demo_script.md`; kiểm tra timeline và cú pháp, chưa chạy cấu hình demo mới |
| ⬜ | Tự chụp ảnh, chạy thử và diễn tập demo | Không đánh dấu đã tập khi chỉ có kịch bản |
| ✅ | 5d: bộ câu hỏi và trả lời toàn pipeline | `docs/tv2/cau_hoi_bao_ve.md` |
| ⬜ | Sinh viên tự ôn bộ câu hỏi | Chưa có xác nhận |
| ✅ | 5e: danh sách file ghép và tin nháp M4 | `docs/tv2/m4_handoff.md` |
| ⬜ | M4 bàn giao thực tế / TV4 xác nhận nhận và ghép | Chưa gửi tin bằng công cụ; chưa commit/push bản mới; cần người dùng thực hiện hoặc quyết định cách chuyển |
| ✅ | Quyết định và sao lưu trước khi dọn dữ liệu cũ | Người dùng đã đồng ý; toàn bộ reports gen01 đã sao lưu và khớp SHA256 tại `docs/evidence/tv2/archive_synthetic_tv2_gen01_20261111/` |
| ⬜ | Xóa dữ liệu gen01 sau sao lưu | Lệnh xóa bị kiểm duyệt tự động chặn (`blocked by policy`); gen01 vẫn còn; synthetic_tv2_test không tồn tại |

Các đính chính cần dùng khi cập nhật phần lịch sử:

- Ràng buộc hiện tại: máy RAM 8 GB, WSL 5 GB; không áp dụng hướng dẫn cũ nâng WSL lên 8 GB.
- Dùng nguyên số từ JSON/CSV; chi tiết KB3/KB5 xem Ch.6 đã đối chiếu. Thời gian cleaning gộp lấy `cleaning_seconds_total`, không làm tròn thêm.
- Cart giảm qua cleaning chưa phải số trùng riêng theo event_type. Không giữ kết luận định lượng trùng cart khi chưa có bảng chéo nguồn.
- Không khẳng định số lần OOM/mã lỗi từ ghi chú metrics; cần log lịch sử để chứng minh.
- Benchmark/charts chạy riêng; `--full` hiện dừng sau aggregation. M1 thành công không đồng nghĩa mọi benchmark đã hoàn tất.
- Các file mới và Ch.6 sửa vẫn ở working tree. Chưa commit, push, merge hay mở PR trong chuỗi hỗ trợ này. Chỉ đánh dấu các hành động người dùng sau khi có xác nhận thực tế.

## Context (bản kế hoạch và nhật ký lịch sử)
Bạn là TV2 trong đồ án Spark (repo `D:\BigData\bigdata-ecommerce-spark`). Theo 3 file Word:
- **Code:** `scripts/generate_data.py`, `jobs/01_profiling.py`, `jobs/make_sample.py`, `docs/data_contract.md`
- **Thực nghiệm:** KB3 (so CSV với Parquet), KB5 (chất lượng trước/sau làm sạch, làm cùng TV3)
- **Báo cáo (~8 trang):** Ch.2.1 (Big Data 5V, Data Lake, Parquet), Ch.3 (Dữ liệu & yêu cầu), phần KB3/KB5 trong Ch.6, Phụ lục schema
- **Demo 3 phút:** dữ liệu, data contract, kết quả profiling raw
- Khoảng 30 giờ

**Hiện trạng repo (cập nhật 02/11/2026):** PR #2 (M0) đã merge vào `main`; PR #4 (M2/M3 + Ch.3/Ch.6) đã mở. Hiện trạng gốc 22/10:
- TV1 đã xong Docker, `00_ingest.py`, `04_benchmark.py`.
- TV3 đã xong `02_cleaning.py`, `run_pipeline.sh`, test và báo cáo.
- **Chưa có file nào của TV2.**
  - TV3 đang chạy theo "luật tạm" và chờ contract của bạn ([docs/tv3_handoff.md](bigdata-ecommerce-spark/docs/tv3_handoff.md)).
  - `run_pipeline.sh --full` báo thiếu `01_profiling.py`.
  - TV4 cần `samples/` để chạy KB4.
- **→ TV2 đang là điểm nghẽn của cả nhóm.** Ưu tiên số 1 là bàn giao những gì người khác đang chờ.

---

## Roadmap: 5 giai đoạn (~2,5 tuần, sắp theo mức độ người khác phụ thuộc)

### Nhật ký tiến độ (cập nhật 22/10/2026)

| Trạng thái | Việc | Ghi chú |
|---|---|---|
| ✅ | Giai đoạn 0 – Chuẩn bị | Nhánh `tv2/data-quality`; cụm Spark 1 master + 2 worker (Alive Workers: 2); đã đọc tài liệu bàn giao TV3 |
| ✅ | Tải dữ liệu Kaggle thật | `data/real_oct_run01/landing/2019-Oct.csv`, 5.668.612.855 byte, 42.448.764 dòng, header đúng 9 cột. Chưa ingest/clean |
| ✅ | Cài Kaggle CLI + token | `C:\Users\nhatt\.kaggle\kaggle.json` (không đưa lên Git/chat) |
| ✅ | `scripts/generate_data.py` | Chèn thêm giá âm/NaN, event_type lạ, session trống, user_id trống; không ghi đè; ghi `generate_data_truth.json` + `source.json` |
| ✅ | `docs/data_contract.md` v1.0 | Chốt: giá NaN/Inf/≤0 → loại; session trắng → loại; brand/category rỗng → `unknown`; ID dương/UUID chỉ ghi nhận; UTC; dedup trước chuẩn hóa |
| ✅ | `scripts/compare_truth.py` | So số lỗi đã chèn với `cleaning_metrics.json`. Kết quả test: đạt 5/5 mục |
| ✅ | Test pipeline `--ingest-clean` trên dữ liệu giả | Raw 202.032 → clean 196.492; bỏ đúng 2032 dòng trùng và 424 event_type lạ |
| ✅ | Commit + mở PR nháp cho TV3/TV1 | Commit `0bba5bf`; PR nháp #2 https://github.com/minh2255/bigdata-ecommerce-spark/pull/2 |
| ✅ | Kiểm chứng luật tạm của TV3 trên Kaggle thật | Quét 42.448.764 dòng: luật ổn, không đổi `02_cleaning.py`. Giá=0 chỉ ở view/cart (68.673), trùng 30.220, session rỗng 2, category null 31,8%, brand null 14,4%. Ghi vào contract mục 7 (commit `b2c1de3`) |
| ✅ | `jobs/01_profiling.py` | Chạy được `raw`/`clean`; test synthetic: duplicates=2032 khớp truth, clean 196.492 dòng, mọi bất biến đạt; test tập rỗng cho `SUCCESS_EMPTY`; chạy lần 2 bị chặn ghi đè. Đã commit `c36f58a` |
| ✅ | Nâng RAM WSL (giai đoạn 3) | Máy 8 GB nên chọn `memory=5GB`, `swap=8GB` trong `.wslconfig` (không dùng 8 GB); Docker nhận 5,15 GB, cụm Spark 2 worker chạy lại bình thường |
| ✅ | Chạy thử 3 triệu dòng đầu Kaggle thật | `data/real_sample3m_run01`: ingest 21s, cleaning 221s (tổng 4m23s): raw 3.000.000 → dedup 2.998.565 → clean 2.993.871 (loại 1.435 trùng, 4.694 giá ≤ 0). Profiling raw 55s, clean 103s; số liệu profiling khớp log cleaning (trùng 1.435, giá ≤ 0 4.694), 0 trùng/0 giá ≤ 0 ở clean. Không tràn bộ nhớ. Ước tính toàn bộ 42,4 triệu dòng: khoảng 14× → ~1 giờ cleaning, ~35 phút profiling |
| ✅ | Chạy ingest + cleaning + profiling trên Kaggle thật (42,4 triệu dòng) — **02/11** | Chạy 1 lần vẫn OOM (mã 52) lần 3 → chia **8 lát ngày** (`jobs/slice_raw_by_day.py`, `data/real_oct_run01/run_slices.sh`), chạy nguyên `02_cleaning.py` từng lát, gộp vào `data/real_oct_full/`. Raw 42.448.764 → dedup 42.418.544 (−30.220) → clean **42.349.872** (−68.670 giá ≤ 0, −2 session null); cleaning 2.553 s. 8 lát đều SUCCESS, 0 trùng/0 giá ≤ 0, `all_pass=true`; profiling toàn tháng (raw 591 s, clean 367 s) khớp từng số quét ban đầu. Conf hiện tại trong container: `executor.cores 1`, `shuffle.partitions 800` |
| ✅ | Samples `frac_0.01/0.05/0.1` | `data/real_oct_full/samples/`: 424.095 / 2.118.183 / 4.238.351 dòng; pandas đọc được trong container (máy Windows chưa có `pyarrow`). **Việc của bạn:** nhắn TV4 đường dẫn |
| ✅ | KB3 CSV vs Parquet | Dung lượng 5,67 GB vs 1,47 GB (3,87×); `count()` 39,7 s vs 2,2 s; `sum(price)` 56,3 s vs 3,2 s (~17,7×), 3 lần đo. `docs/evidence/tv2/kb3.csv`, `kb3_env.json` |
| ✅ | KB5 + `docs/tv2/ch06_kb3_kb5.md` | Bảng số dòng qua các bước + so raw/clean; phát hiện dòng trùng tập trung ở `cart` (~28 nghìn, 3% số cart) |
| ✅ | Nháp Ch.3 `docs/tv2/ch03_du_lieu.md` | Số liệu toàn tháng đã điền, không còn ô chờ |
| ✅ | Push + PR #4 | Nhánh `tv2/report-ch3` (commit `ff01d82`, `36e1fd6`, `419867c`) https://github.com/minh2255/bigdata-ecommerce-spark/pull/4 |
| ✅ | Viết `make_sample.py`, `kb3_csv_vs_parquet.py`, nháp Ch.2.1 | Đã chạy (xem các dòng trên). Đã commit `cd766a7` (2 job) và `a14f19d` (Ch.2.1), đã push |
| ✅ | Phụ lục schema raw và clean (A4) | `docs/tv2/phu_luc_schema.md`; ví dụ đọc thật từ Parquet raw/clean của `real_sample3m_run01` bằng pyarrow. Commit `e1e425d`, `d8a60ab`, đã push. Đã cập nhật tỷ lệ `unknown` toàn tháng (brand 14,27%, cat_l1 31,82%), commit `419867c` |
| ✅ | Chạy `run_pipeline.sh --full` | Chờ `03_aggregation.py` của TV4; hiện chỉ test profiling bằng spark-submit riêng |
| ⬜ | Nhắn nhóm mốc M0 (PR #2 đã merge), M2 (samples), M3 (KB3/KB5); nhờ TV1 review PR #4 | Việc của bạn |

**Lưu ý kỹ thuật về profiling**
- Spark đọc CSV với `nanValue="NaN"`; giá `nan`/`inf` viết thường thành **null** ở raw, nên hiện ở `price_null` chứ không phải `price_nan`. Khi đối chiếu truth: `price_null` ≈ `price_nan` đã chèn (cộng bản trùng).
- `price_le_0` trên raw lớn hơn số đã chèn một chút vì các dòng lỗi cũng bị nhân bản trong ~1% dòng trùng.
- `profiling_clean.json` có mục `invariants`; job thoát mã 1 nếu có bất biến sai.

**Lưu ý môi trường**
- `docker-compose.override.yml` (đổi cổng Master UI → 9090) chỉ có trên máy này, đã loại khỏi Git qua `.git/info/exclude`.
- Docker mới được cấp ~4 GB RAM (2 worker × 2 GB). Chạy đủ 42 triệu dòng có thể hết bộ nhớ → nâng `memory=8GB` trong `C:\Users\nhatt\.wslconfig`, chạy `wsl --shutdown`, mở lại Docker Desktop.
- Vùng dữ liệu test cần dọn khi xong: `data/synthetic_tv2_test`, `data/synthetic_tv2_gen01`.

### Giai đoạn 0: Chuẩn bị (ngày 1, ~2h)
- [x] `git checkout -b tv2/data-quality` từ `main`
- [x] Bật cụm: `docker compose up -d --build`, mở localhost:8080 (máy TV1 dùng 9090), thấy 2 worker ALIVE — *xong, dùng cổng 9090 (8080 bị AgentService chiếm)*
- [x] Đọc [docs/tv3/ban_giao_clean_tv4.md](bigdata-ecommerce-spark/docs/tv3/ban_giao_clean_tv4.md) (schema clean thực tế) và [docs/evidence/tv3/kb5_cleaning_steps.csv](bigdata-ecommerce-spark/docs/evidence/tv3/kb5_cleaning_steps.csv)
- [x] Bắt đầu tải `2019-Oct.csv` từ Kaggle (file lớn, cho tải nền), đặt vào một vùng riêng, ví dụ `data/real_oct_run01/landing/` — *xong, 42.448.764 dòng, đúng header*

### Giai đoạn 1: Gỡ nghẽn cho nhóm (ngày 1–3, ~8h) ⚠️ ưu tiên cao nhất

**Checklist**
- [x] `scripts/generate_data.py` viết xong và test
- [x] `docs/data_contract.md` v1.0 chốt các quyết định
- [x] `scripts/compare_truth.py` (đối chiếu số lỗi chèn với kết quả cleaning)
- [x] Commit lên nhánh `tv2/data-quality` — *`0bba5bf`, `b2c1de3`, `c36f58a`, đã push*
- [x] Mở PR nháp, báo TV3 đối chiếu contract, TV1 review — *PR #2 đã mở; bạn cần nhắn TV3/TV1 trực tiếp*
- [x] TV3 xác nhận contract — *PR #2 đã merge vào `main`; luật giữ nguyên, không đổi `02_cleaning.py`*
- [ ] **Mốc M0 đạt**: nhắn nhóm đã bàn giao generate_data + contract

1. ✅ **`scripts/generate_data.py`**: dùng code mẫu mục 5.5 file 2. *(xong, đã test)*
   - Đọc `DATA_DIR`, nhận tham số số dòng, `seed=42`
   - Cố ý chèn ~1% dòng trùng, ~1% giá = 0
   - Nên chèn thêm vài dòng null brand/category_code và event_type lạ, để cleaning có đủ trường hợp kiểm tra
   - Chạy thử: `docker exec spark-master python3 /opt/scripts/generate_data.py 200000`
2. ✅ **`docs/data_contract.md`** *(xong v1.0, chờ TV3 xác nhận)*: bảng gồm cột, kiểu, ý nghĩa, quy tắc hợp lệ, cách xử lý khi vi phạm (dựa trên 7 quy tắc ở mục 5.3 file 2). **Phải chốt các câu TV3 đang hỏi:**
   - price NaN/Infinity → loại
   - user_session rỗng/chỉ có khoảng trắng → loại
   - brand/category rỗng → `unknown`
   - Có bắt ID phải dương, user_session phải đúng UUID không? (đề xuất: chỉ ghi nhận trong profiling, không loại)
   - Múi giờ: mọi thời gian theo UTC
   - Dedup: xét trùng trên toàn bộ dòng raw, trước khi chuẩn hóa
3. ✅ *(chưa làm)* Mở PR sớm (có thể là draft) để TV3 đối chiếu luật và TV1 review.

### Giai đoạn 2: Profiling (ngày 3–6, ~6h) – code xong 22/10, còn PR + chạy `--full`

**Checklist**
- [x] Viết `jobs/01_profiling.py` nhận tham số `raw` / `clean`
- [x] Chỉ số cơ bản: tổng dòng, null mỗi cột, dòng trùng, giá ≤ 0, phân bố event_type
- [x] Chỉ số bổ sung: giá NaN/Inf, chuỗi rỗng, min/max/mean price, khoảng ngày, số user/session khác nhau, tỷ lệ `unknown`
- [x] Xử lý được bảng rỗng (`SUCCESS_EMPTY`) và đặt `timeZone = UTC`
- [x] Ghi `reports/profiling_{layer}.json`, không ghi đè nếu đã có
- [x] Test trên dữ liệu giả: `profiling_raw.json` khớp `generate_data_truth.json`
- [x] Test `profiling_clean.json`: đạt các bất biến ở mục 4 của contract
- [x] `bash scripts/run_pipeline.sh --full` chạy qua phần profiling
- [x] **Mốc M1 đạt**: PR profiling được review

- **`jobs/01_profiling.py`** (code mẫu mục 5.2) nhận tham số `raw` hoặc `clean`. Cần sửa thêm cho khớp repo hiện tại:
  - Đọc đúng `DATA_DIR` mà `run_pipeline.sh` truyền vào (pipeline dùng vùng `DATA_DIR` mới cho mỗi lần chạy)
  - `spark.conf.set("spark.sql.session.timeZone","UTC")`
  - Chạy được trên cả 2 schema: raw có `event_time`, clean có `event_ts`, `cat_l1`, `cat_l2`, `event_date`…
  - Xử lý được tập rỗng (TV3 có trường hợp `SUCCESS_EMPTY`)
  - Thêm chỉ số: số giá NaN/Inf, chuỗi rỗng ở brand/category/session, min/max/mean price, khoảng ngày, số user/session khác nhau, tỷ lệ `unknown` (bảng clean)
  - Ghi `reports/profiling_{layer}.json`
- Test trên synthetic: `bash scripts/run_pipeline.sh --full`. Lúc này pipeline chỉ còn thiếu `03_aggregation.py` của TV4. Nếu cần, chạy riêng `--ingest-clean`, sau đó gọi profiling bằng `spark-submit`.
- **Bàn giao (mốc M1):** contract + `profiling_raw.json` chạy được

### Giai đoạn 3: Dữ liệu thật + mẫu (ngày 6–10, ~6h)

**Checklist**
- [x] Nâng RAM Docker lên 8 GB (nếu máy đủ) trước khi chạy dữ liệu thật — *máy 8 GB nên chỉ nâng lên 5 GB (`memory=5GB`, `swap=8GB`)*
- [x] Chạy ingest + cleaning trên dữ liệu thật — *theo 8 lát ngày, gộp ở `real_oct_full`*
- [x] Chạy `01_profiling.py raw` và `clean` trên dữ liệu thật — *toàn tháng, SUCCESS*
- [x] Viết `jobs/make_sample.py` — *đã chạy trên clean toàn tháng*
- [x] Tạo `samples/frac_0.01`, `frac_0.05`, `frac_0.1` — *`data/real_oct_full/samples/`*
- [x] Báo TV4 đường dẫn samples (kèm lưu ý `pyarrow`) — *việc của bạn*
- [x] **Mốc M2 đạt** (chỉ còn nhắn nhóm): samples + `profiling_clean.json` thật

- Chạy pipeline trên Kaggle thật:
  - `DATA_DIR=/data/real_oct_run01`, `DATA_KIND=real`
  - Lệnh có sẵn trong [docs/tv3_handoff.md](bigdata-ecommerce-spark/docs/tv3_handoff.md)
  - Xong thì chạy profiling raw và profiling clean
- **`jobs/make_sample.py`** (code mẫu mục 5.5): tạo `samples/frac_0.01`, `frac_0.05`, `frac_0.1`. Dùng `coalesce(1)`, `seed=42`, ghi log số dòng.
- Báo TV4 đường dẫn samples để chạy KB4.
- **Bàn giao (mốc M2):** `samples/` + `profiling_clean.json` từ dữ liệu thật

### Giai đoạn 4: Thực nghiệm KB3 & KB5 (ngày 10–13, ~4h)

**Checklist**
- [x] Viết script KB3 (CSV với Parquet), ghi `reports/kb3.csv` — *đã chạy*
- [x] Đo dung lượng `landing/` và `raw/events`
- [x] Đo thời gian `count()` CSV và Parquet, mỗi phép đo 3 lần (thêm `sum(price)`)
- [x] Ghi cấu hình máy (CPU, RAM, số worker) — *`kb3_env.json`*
- [x] KB5: bảng so `profiling_raw.json` với `profiling_clean.json` + log `[CLEAN]`
- [x] Chụp minh chứng: Spark UI, cây thư mục — *2 file JSON đã lưu; còn ảnh*
- [x] Lưu minh chứng vào `docs/evidence/tv2/` (JSON/CSV; ảnh chờ chụp)
- [ ] **Mốc M3**: số liệu đã sẵn (PR #4); còn gửi cho TV4 — *việc của bạn*

- **KB3, CSV với Parquet:**
  - So dung lượng `landing/` với `raw/events` (`du -sh`)
  - So thời gian `count()` khi đọc CSV (schema cố định) và khi đọc Parquet
  - Có thể thêm: chọn 1 cột và đo, để thấy lợi ích lưu theo cột
  - Mỗi phép đo chạy 3 lần, lấy trung bình; ghi cấu hình máy (CPU, RAM, số worker)
  - Nên viết script nhỏ, ví dụ `jobs/kb3_csv_vs_parquet.py`, ghi `reports/kb3.csv`
- **KB5:**
  - Bảng so `profiling_raw.json` với `profiling_clean.json`, kèm log `[CLEAN]` của TV3 (raw → dedup → filter)
  - Giải thích lưu ý của TV3: các dòng clean có thể trùng lại sau khi chuẩn hóa, dù raw đã dedup
- Chụp minh chứng:
  - Spark UI 4040 khi profiling đang chạy
  - Kết quả 2 file JSON
  - Cây thư mục `landing/` và `raw/`
- Lưu minh chứng vào `docs/evidence/tv2/`, theo cách TV3 đã làm
- **Bàn giao (mốc M3):** số liệu KB3/KB5 gửi TV4 vẽ biểu đồ

### Giai đoạn 5: Báo cáo + demo (ngày 13–18, ~10h)

**Checklist**
- [x] Ch.2.1 Big Data, Data Lake, Parquet (~3 trang) — *bản nháp `docs/tv2/ch02_1_bigdata.md`, cần bạn đọc lại; đã commit `a14f19d`*
- [x] Ch.3 Dữ liệu và yêu cầu (~4 trang) — *`docs/tv2/ch03_du_lieu.md`, cần bạn đọc lại*
- [x] Phần KB3, KB5 trong Ch.6 — *`docs/tv2/ch06_kb3_kb5.md`, cần bạn đọc lại*
- [x] Phụ lục schema raw và clean — *`docs/tv2/phu_luc_schema.md`, đã cập nhật số `unknown` toàn tháng*
- [x] Góp bài học cho Ch.8 và ghi chú dùng AI
- [x] Kiểm tra mọi số liệu trong báo cáo khớp với file JSON/CSV
- [ ] Tập demo 3 phút
- [ ] Ôn các câu hỏi giảng viên hay hỏi
- [ ] **Mốc M4 đạt**: giao Markdown cho TV4 ghép báo cáo

- Ch.2.1 (3 trang): 5V, Data Lake với các tầng landing/raw/clean/agg, Parquet (lưu theo cột, nén, giữ schema, đọc chọn cột)
- Ch.3 (4 trang): nguồn Kaggle, schema 9 cột, dòng ví dụ, kết quả profiling raw (dòng trùng, null, giá lỗi) → yêu cầu làm sạch → tóm tắt contract
- Ch.6 phần KB3, KB5: bảng số liệu, biểu đồ, giải thích kết quả
- Phụ lục schema raw và schema clean
- Góp bài học cho Ch.8; ghi chú dùng AI (công cụ, mục đích, phần đã tự kiểm tra)
- Viết Markdown trong `docs/tv2/`, đặt tên file giống TV3 (ví dụ `ch02_1_bigdata.md`, `ch03_du_lieu.md`)
- Demo 3 phút:
  - Giới thiệu dataset → mở contract → chạy profiling raw trên dữ liệu nhỏ → cho xem số dòng trùng, null, giá lỗi
  - Chiếu ảnh của lần chạy dữ liệu đầy đủ đã chụp trước
- Ôn các câu hỏi giảng viên hay hỏi (mục 10 file 2): vì sao dùng Parquet, partition là gì, transformation/action, shuffle. **Phải giải thích được toàn bộ pipeline, không chỉ phần mình.**
- Tuần cuối: kiểm tra mọi số liệu trong báo cáo khớp với file JSON/CSV

---

## Bảng mốc bàn giao
| Mốc | Sản phẩm | Ai đang chờ |
|---|---|---|
| M0 (ngày 3) | generate_data.py + data_contract.md | TV3, TV4 |
| M1 (ngày 6) | 01_profiling.py + profiling_raw.json | `run_pipeline --full`, TV3 |
| M2 (ngày 10) | samples/ + profiling_clean.json (thật) | TV4 (KB4) |
| M3 (ngày 13) | Số liệu KB3/KB5 + minh chứng | TV4 (biểu đồ, ghép báo cáo) |
| M4 (ngày 18) | Ch.2.1, Ch.3, phần Ch.6, phụ lục | TV4 ghép báo cáo |

## Quy tắc khi làm
- Mọi job đọc `DATA_DIR`; không ghi đè vùng đã có dữ liệu, mỗi lần chạy dùng `DATA_DIR` mới
- Bỏ `landing/synthetic.csv` ra khỏi vùng chứa dữ liệu thật
- Không commit `data/` hay file 5 GB; lưu `.sh` với kiểu xuống dòng LF
- Mỗi mốc là 1 PR riêng, gửi TV1 review; báo tiến độ trong buổi họp tuần

## Kiểm tra hoàn thành
- `bash scripts/run_pipeline.sh --full` trên synthetic chạy hết, chỉ còn chờ `03_aggregation.py` của TV4
- `profiling_raw.json` của synthetic thấy ~1% dòng trùng và ~1% giá ≤ 0; `profiling_clean.json` có 0 dòng trùng raw, 0 giá ≤ 0
- `samples/frac_*` tồn tại, số dòng xấp xỉ 1%, 5%, 10% của clean; `pd.read_parquet` đọc được
- KB3: Parquet nhỏ hơn và đọc nhanh hơn CSV, có trung bình của 3 lần chạy
