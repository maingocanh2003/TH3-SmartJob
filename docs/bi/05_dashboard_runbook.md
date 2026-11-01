# Hướng dẫn chạy dashboard BI SmartJob

## 1. Tình trạng thực tế trong môi trường hiện tại

Tôi đã kiểm tra project và cấu hình hiện tại theo đúng quy tắc: không tự đoán tên bảng, không sửa code của người khác, và ưu tiên sử dụng dữ liệu từ PostgreSQL hiện có.

Kết quả kiểm tra thực tế:

- File `.env` của dự án xác định database `smartjob_db` trên host `localhost`, port `5433`.
- PostgreSQL CLI/Server không có sẵn trong môi trường này (không có `psql`, không có PostgreSQL service đang chạy).
- Apache Superset chưa được cài đặt hoặc chưa chạy trong environment hiện tại.
- Vì vậy, không thể kết nối thật tới PostgreSQL, chạy SQL trên DB hoặc render dashboard trong máy làm việc hiện tại.

Đây là tình trạng cần được xử lý bằng cách:

1. Cài đặt/khởi động PostgreSQL trên máy hoặc server.
2. Tạo/khôi phục database `smartjob_db`.
3. Chạy schema và dữ liệu thực tế vào DB.
4. Cài đặt Apache Superset hoặc sử dụng container Docker.
5. Kết nối Superset tới PostgreSQL và import dataset từ các VIEW đã tạo.

## 2. Nguồn dữ liệu chính đã xác thực từ project

Các bảng thực tế đã được xác thực từ `docs/database-schema.sql` và `backend/api/models.py`:

- `Users`
- `Candidates`
- `Companies`
- `Skills`
- `Candidate_Skills`
- `Education`
- `Experience`
- `Jobs`
- `Job_Skills`
- `Applications`
- `AI_Match_Results`
- `Job_Views`
- `Saved_Jobs`

Các bảng quan trọng cho dashboard BI:

- `Jobs` -> tin tuyển dụng
- `Companies` -> ngành nghề, doanh nghiệp
- `Job_Skills` + `Skills` -> nhu cầu kỹ năng
- `Applications` -> quy trình ứng tuyển
- `AI_Match_Results` -> điểm match AI (nếu cần phân tích)
- `Job_Views` -> lượt xem job để đo mức quan tâm

## 3. Cấu hình kết nối PostgreSQL với Superset

### Connection string mẫu

```text
postgresql+psycopg2://smartjob_user:matkhau_moi@host.docker.internal:5433/smartjob_db
```

Nếu chạy local:

```text
postgresql+psycopg2://smartjob_user:matkhau_moi@localhost:5433/smartjob_db
```

Trong Superset:

1. Vào Data > Databases.
2. Chọn PostgreSQL.
3. Nhập:
   - Host: `localhost` hoặc hostname thật
   - Port: `5433`
   - Database: `smartjob_db`
   - Username: `smartjob_user`
   - Password: theo `.env`
4. Test connection.
5. Nếu OK, lưu database.

## 4. SQL thực hiện để tạo data mart cho dashboard

File sử dụng: `docs/bi/02_sql_queries.sql`

Các VIEW đã tạo:

- `bi_vw_job_market_overview`
- `bi_vw_job_demand_by_industry`
- `bi_vw_skill_demand`
- `bi_vw_salary_by_industry_and_role`
- `bi_vw_recruitment_funnel`
- `bi_vw_funnel_by_stage`
- `bi_vw_company_market_share`
- `bi_vw_top_job_titles`

Các view này dùng tên cột thực sự có trong schema, không suy đoán, và bao gồm kiểm tra `NULL` bằng `COALESCE()`.

## 5. Dashboard yêu cầu cần có

### A. Số lượng tin tuyển dụng theo ngành nghề

- Dataset: `bi_vw_job_demand_by_industry`
- Chart: Bar Chart / Column Chart
- X-axis: `industry`
- Y-axis: `jobs_count`
- Filter: `industry`, `date range` if needed

### B. Nhu cầu kỹ năng của doanh nghiệp

- Dataset: `bi_vw_skill_demand`
- Chart: Horizontal Bar Chart
- X-axis: `jobs_count`
- Y-axis: `skill_name`
- Sort: DESC

### C. Mức lương theo ngành nghề hoặc vị trí

- Dataset: `bi_vw_salary_by_industry_and_role`
- Chart: Line / Bar
- X-axis: `month_start`
- Series: `industry` hoặc `position_level`
- Metric: `avg_salary_vnd`

### D. Tỷ lệ ứng tuyển, phỏng vấn và tuyển dụng thành công

- Dataset: `bi_vw_recruitment_funnel` hoặc `bi_vw_funnel_by_stage`
- Chart: Funnel / Bar Chart
- Stages: `Applications`, `Reviewed`, `Shortlisted`, `Interviewed`, `Offered`
- Metric: `stage_count`

## 6. Bộ lọc đề xuất cho dashboard

- time range: `created_at` hoặc `applied_at`
- `industry`
- `location`
- `position_level`
- `employment_type`
- `company_name`
- `status`

## 7. Kiểm tra tính chính xác của số liệu

Tôi đã cung cấp các câu lệnh kiểm tra trong `docs/bi/02_sql_queries.sql`:

- tổng số job active
- tổng số ứng tuyển
- số lượng theo trạng thái ứng tuyển
- jobs missing salary
- industry thiếu dữ liệu
- duplicate application
- skill rows không có mapping

Các kiểm tra này cần được chạy sau khi DB đã được tạo thật.

## 8. Các bước thực hiện khi database đã sẵn sàng

1. Đăng nhập PostgreSQL bằng user `smartjob_user`.
2. Chạy schema nếu chưa tạo: `docs/database-schema.sql`.
3. Chạy seed data nếu cần: `docs/seed-data.sql` hoặc dữ liệu chính thức từ project.
4. Chạy SQL trong `docs/bi/02_sql_queries.sql` để tạo VIEW.
5. Vào Apache Superset, tạo database connection.
6. Dùng các view như dataset.
7. Thiết kế dashboard theo 4 nội dung yêu cầu.
8. Kiểm tra số liệu bằng các câu lệnh validate.
9. Lưu dashboard và export screenshot.

## 9. Kết luận

Trong môi trường hiện tại, tôi không thể hoàn tất trực tiếp giao diện dashboard trên Superset vì PostgreSQL và Superset chưa được cài/khởi động. Tuy nhiên, toàn bộ cấu trúc SQL, dataset, KPI và thiết kế dashboard đã được triển khai trong project theo đúng dữ liệu thật của schema hiện có, sẵn sàng cho các bước chạy tiếp khi môi trường DB được kích hoạt.

Nếu team bật PostgreSQL và Superset lên, tôi có thể tiếp tục triển khai trực tiếp trên máy đó ngay sau khi database thật sẵn sàng.
