# Nội dung đóng góp của TV3 cho Chương 8

## Bài học từ triển khai

Việc tách raw và clean thành các tầng Parquet giúp TV3 kiểm tra quy tắc từ fixture trước khi có aggregation. Tính độc lập này đòi hỏi thống nhất schema, nguồn và thời gian. Một thư mục tồn tại hoặc exit 0 chưa đủ chứng minh dữ liệu sẵn sàng; cần đọc lại, kiểm tra kiểu và đối chiếu counts.

Sự cố file nhỏ trên Windows cho thấy I/O và commit có thể lấn át phép xử lý. Bản đầu tạo khoảng 6200 file và bị dừng; bản sau dùng cùng CSV, ghi 31 file và hoàn tất. Không suy ra càng ít file càng tốt: cần đo kích thước file, tải theo ngày và tài nguyên. Quyết định hiện tại mới được kiểm chứng trên synthetic.

Kiểm thử biên phát hiện lỗi khó thấy ở mẫu thông thường. Raw rỗng và toàn bộ bị loại đều cần đầu ra có schema. Nhiều sự kiện chung session phải được giữ nếu không trùng hàng; công cụ dùng session làm khóa duy nhất có thể báo sai. Bản kiểm tra hiện tại so cả giá trị và số lần xuất hiện của hàng trong fixture nhỏ.

## Hạn chế và hướng hoàn thiện

Data contract TV2 chưa được bàn giao. Các mở rộng về giá hữu hạn, session trắng và giá trị chuỗi rỗng của brand/category cần được nhóm xác nhận bằng dữ liệu thật và mục tiêu nghiệp vụ. Chưa áp ràng buộc ID dương hoặc session UUID. Quy tắc dedup là theo raw trước chuẩn hóa, nên không khẳng định mọi hàng clean đều khác nhau nếu các raw khác nhau trở nên giống sau chuẩn hóa.

Môi trường hiện tại là ba container trên một máy, dùng cùng ổ gắn /data. Nó cho phép quan sát task phân phối trên hai worker, nhưng không thay cho thực nghiệm nhiều máy hay lưu trữ phân tán có dự phòng. Test mới được chạy trên máy hiện tại. TV3 chưa nhận file Kaggle, chưa chạy cleaning tháng thật, chưa có profiling chính thức hay đối chiếu KPI với TV4. Đây là các việc phụ thuộc bên ngoài, không thể suy ra từ fixture đã PASS.

Khi tích hợp, cần chốt contract trước, giữ nguồn dữ liệu tách biệt, chọn DATA_DIR mới và lưu mã phiên bản mã nguồn cùng metrics. Sau đó đánh giá file-size/skew trên Kaggle, chạy profiling trước/sau, bàn giao schema/UTC và nhờ thành viên khác thực hiện checklist tái lập. Chỉ đánh dấu hoàn thành những bước có log hoặc xác nhận thật; không chuyển các mục chờ thành kết quả giả định.

# Ghi chú sử dụng AI và xác nhận của người thực hiện

Codex hỗ trợ đọc ba tài liệu nhóm, rà soát code/bằng chứng, cleaning/pipeline/kiểm thử, Markdown/Word, demo và minh chứng. Sửa benchmark TV1 cùng số đo phiên trước được giữ nguyên; phiên cá nhân không chạy tiếp benchmark hoặc làm sản phẩm TV4. Thành viên nhóm vẫn chịu trách nhiệm tác giả và kiểm tra chuyên môn.

Những việc được kiểm tra tự động gồm cú pháp Python/Bash, guard thiếu job/input/config, log/exit code, fixture lỗi/rỗng/toàn bộ bị loại, nhiều sự kiện chung session, schema/UTC/cột dẫn xuất, số dòng đọc lại và bảo vệ hash đầu ra khi chạy lại. Đối chiếu giá trị toàn bộ chỉ áp dụng fixture nhỏ có giới hạn; validator Spark cho tập lớn kiểm tra tập điều kiện và số liệu tổng hợp, không thay cho chứng minh tương đương từng hàng.

Người trình bày cần tự đọc và giải thích từng phép biến đổi, tập demo thực tế, xác nhận các quy tắc mở rộng với TV2, xác minh nguồn Kaggle và đối chiếu dữ liệu thật sau khi có. TV4 cần xác nhận đọc được clean và hiểu quy ước ngày/thứ; thành viên khác cần thực sự chạy checklist trên máy của họ. Các chỗ điền họ tên/MSSV/tỷ lệ đóng góp và việc nhóm chấp nhận nội dung báo cáo vẫn do người dùng thực hiện, không được AI tự xác nhận thay.
