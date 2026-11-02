# HƯỚNG DẪN TÍCH HỢP & VẬN HÀNH BI DASHBOARD

Tài liệu này bao gồm hướng dẫn cho cả hai phương án triển khai BI Dashboard trong dự án SmartJob:
1. **Frontend Web BI Dashboard** (Checklist 04 - Tích hợp trực tiếp trên giao diện website)
2. **Apache Superset BI Dashboard** (Checklist 03 - Hệ thống phân tích chuyên sâu với views)

---

## PHẦN 1: FRONTEND WEB BI DASHBOARD (CHECKLIST 04)

### 1.1. Phạm vi
Dashboard BI được tích hợp trực tiếp trong frontend tại `frontend/bi-dashboard.html`, sử dụng các API tổng hợp dữ liệu của Django REST Framework. Trang hiển thị dữ liệu thực trong PostgreSQL, không dùng số liệu mẫu cố định.

Các báo cáo gồm:
- Tổng số tin tuyển dụng, tin đang tuyển, ứng viên, doanh nghiệp, đơn ứng tuyển và lượt xem.
- Top kỹ năng được yêu cầu nhiều nhất trong tin tuyển dụng.
- Khoảng lương trung bình theo ngành nghề và cấp bậc.
- Phễu lượt xem → nộp đơn → sơ tuyển → phỏng vấn → trúng tuyển, cùng hai tỷ lệ chuyển đổi.

### 1.2. Chạy dashboard
1. Cài đặt PostgreSQL, tạo database và chạy schema theo [SETUP_DATABASE.md](./SETUP_DATABASE.md).
2. Cấu hình kết nối trong `.env` ở thư mục gốc.
3. Cài thư viện backend và khởi động Django từ thư mục gốc:
   ```powershell
   python -m pip install -r backend/requirements.txt
   python backend/manage.py runserver
   ```
4. Phục vụ thư mục frontend bằng một static web server hoặc mở qua script `start.bat`:
   ```powershell
   python -m http.server 5500 --directory frontend
   ```
5. Mở `http://localhost:5500/bi-dashboard.html` (hoặc mở trực tiếp file `frontend/index.html` -> menu BI Dashboard).

Frontend gọi API tại `http://localhost:8000/api/`. Nếu thay đổi địa chỉ backend, cập nhật `API_BASE` trong `frontend/js/api.js`.

### 1.3. API được sử dụng
| Endpoint | Nội dung |
|---|---|
| `GET /api/bi/overview/` | Các chỉ số tổng quan |
| `GET /api/bi/skills_demand/?limit=8` | Nhu cầu kỹ năng theo số tin tuyển dụng |
| `GET /api/bi/salary_trends/` | Mức lương trung bình theo ngành và cấp bậc |
| `GET /api/bi/conversion_funnel/` | Số lượng theo từng giai đoạn và tỷ lệ chuyển đổi |

Khi một API không phản hồi, trang báo lỗi cho riêng khu vực tương ứng và cho phép tải lại dữ liệu. Trường hợp chưa có dữ liệu phù hợp (ví dụ chưa khai báo lương), dashboard hiển thị trạng thái trống thay vì tạo giá trị giả.

---

## PHẦN 2: HƯỚNG DẪN CÀI ĐẶT & VẬN HÀNH APACHE SUPERSET (CHECKLIST 03)

### 2.1. Mục tiêu
Triển khai Dashboard phân tích thị trường lao động cho SmartJob bằng PostgreSQL + Apache Superset dựa trên các BI views đã được chuẩn hóa trong dự án.

### 2.2. Chuẩn bị backend và database
```bash
python -m pip install -r backend/requirements.txt
python backend/manage.py setup_bi_dashboard
python scripts/validate_bi_dashboard.py
```

### 2.3. Kết nối Apache Superset với PostgreSQL
1. Mở Superset.
2. Vào **Settings → Database Connections → + DATABASE**.
3. Chọn PostgreSQL và nhập SQLAlchemy URI:
   ```text
   postgresql+psycopg2://smartjob_user:<DB_PASSWORD>@localhost:5432/smartjob_db
   ```
4. Bật:
   - `Expose in SQL Lab`
   - `Allow CREATE TABLE AS`
   - `Allow DML` (nếu cần thử nghiệm SQL nâng cao)
5. Nhấn **TEST CONNECTION** → **CONNECT**.

### 2.4. Tạo datasets trong Superset
Tạo lần lượt các dataset từ các views:
1. `bi.vw_job_market_fact` (chọn `created_at` làm temporal column)
2. `bi.vw_job_postings_by_industry`
3. `bi.vw_skill_demand`
4. `bi.vw_avg_salary_by_industry_position`
5. `bi.vw_recruitment_funnel`
6. `bi.vw_dashboard_kpis`

### 2.5. Cấu hình biểu đồ theo Checklist 03
1. **Biểu đồ số lượng tin tuyển dụng theo ngành nghề**:
   - Dataset: `bi.vw_job_postings_by_industry` | Bar Chart | Dimension: `industry` | Metric: `SUM(total_jobs)`
2. **Biểu đồ nhu cầu kỹ năng doanh nghiệp**:
   - Dataset: `bi.vw_skill_demand` | Bar Chart | Dimension: `skill_name` | Metric: `SUM(jobs_requiring_skill)` | Row limit: 15
3. **Biểu đồ mức lương trung bình theo ngành nghề/vị trí**:
   - Dataset: `bi.vw_avg_salary_by_industry_position` | Heatmap/Bar Chart | Group by: `industry`, `position_level` | Metric: `AVG(avg_salary_mid)`
4. **Biểu đồ tỷ lệ ứng tuyển/phỏng vấn/tuyển dụng**:
   - Dataset: `bi.vw_recruitment_funnel` | Funnel Chart | Stages: `total_applications` → `reviewed_or_higher` → `interviewed` → `hired_success`
5. **KPI Cards**:
   - Dataset: `bi.vw_dashboard_kpis` (Total Job Postings, Total Candidates, Total Applications, Hiring Rate %)

### 2.6. Thiết lập bộ lọc dữ liệu (Native Filters)
Tạo filter với datasource `bi.vw_job_market_fact`:
1. **Ngành nghề**: cột `industry`
2. **Vị trí công việc**: cột `position_level`
3. **Khu vực**: cột `region`
4. **Thời gian**: cột `created_at` (time range)
5. **Mức lương**: cột `salary_mid` (range filter)

### 2.7. Tham chiếu kỹ thuật
- SQL BI views: `docs/bi/checklist_03_bi_queries.sql`
- Spec dashboard: `docs/bi/superset_dashboard_spec.yaml`
- Command setup BI: `backend/api/management/commands/setup_bi_dashboard.py`
- Script validate: `scripts/validate_bi_dashboard.py`
- Báo cáo hoàn thành: `docs/CHECKLIST_3_BI_REPORT.md`
