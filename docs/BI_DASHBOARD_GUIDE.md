# Hướng dẫn Dashboard BI SmartJob

## Phạm vi

Dashboard BI được tích hợp trực tiếp trong frontend tại `frontend/bi-dashboard.html`, sử dụng các API tổng hợp dữ liệu của Django REST Framework. Trang hiển thị dữ liệu thực trong PostgreSQL, không dùng số liệu mẫu cố định.

Các báo cáo gồm:

- Tổng số tin tuyển dụng, tin đang tuyển, ứng viên, doanh nghiệp, đơn ứng tuyển và lượt xem.
- Top kỹ năng được yêu cầu nhiều nhất trong tin tuyển dụng.
- Khoảng lương trung bình theo ngành nghề và cấp bậc.
- Phễu lượt xem → nộp đơn → sơ tuyển → phỏng vấn → trúng tuyển, cùng hai tỷ lệ chuyển đổi.

## Chạy dashboard

1. Cài đặt PostgreSQL, tạo database và chạy schema theo [SETUP_DATABASE.md](./SETUP_DATABASE.md).
2. Cấu hình kết nối trong `.env` ở thư mục gốc.
3. Cài thư viện backend và khởi động Django từ thư mục gốc:

   ```powershell
   python -m pip install -r backend/requirements.txt
   python backend/manage.py runserver
   ```

4. Phục vụ thư mục frontend bằng một static web server; không mở HTML bằng `file://`. Ví dụ:

   ```powershell
   python -m http.server 5500 --directory frontend
   ```

5. Mở `http://localhost:5500/bi-dashboard.html`.

Frontend gọi API tại `http://localhost:8000/api/`. Nếu thay đổi địa chỉ backend, cập nhật `API_BASE` trong `frontend/js/api.js`.

## API được sử dụng

| Endpoint | Nội dung |
|---|---|
| `GET /api/bi/overview/` | Các chỉ số tổng quan |
| `GET /api/bi/skills_demand/?limit=8` | Nhu cầu kỹ năng theo số tin tuyển dụng |
| `GET /api/bi/salary_trends/` | Mức lương trung bình theo ngành và cấp bậc |
| `GET /api/bi/conversion_funnel/` | Số lượng theo từng giai đoạn và tỷ lệ chuyển đổi |

Khi một API không phản hồi, trang báo lỗi cho riêng khu vực tương ứng và cho phép tải lại dữ liệu. Trường hợp chưa có dữ liệu phù hợp (ví dụ chưa khai báo lương), dashboard hiển thị trạng thái trống thay vì tạo giá trị giả.

## Giới hạn dữ liệu

- Mức lương được tổng hợp từ các tin có khai báo `salary_max`; đơn vị lưu trong database là VND.
- Nhu cầu kỹ năng được tính từ các quan hệ `Job_Skills`.
- Phễu dùng tổng lượt xem và trạng thái đơn ứng tuyển hiện có; đây là số liệu tích lũy, chưa lọc theo khoảng thời gian.
- Dashboard là bản BI nhẹ phục vụ chạy và trình diễn cục bộ. Có thể kết nối Apache Superset sau này nếu cần phân tích nâng cao hoặc chia sẻ dashboard cho nhiều người dùng.
