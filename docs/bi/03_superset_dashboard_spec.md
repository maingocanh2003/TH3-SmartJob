# Superset Dashboard Specification

## 1. Dataset

Kết nối Superset tới PostgreSQL bằng connection string.

Dataset gốc có thể dùng:

- `Jobs`
- `Companies`
- `Applications`
- `Skills`
- `Job_Skills`
- `AI_Match_Results`

Nếu cần chuẩn hóa dễ hơn, đề xuất tạo SQL View:

- `vw_job_market_overview`
- `vw_skill_demand`
- `vw_salary_trend`
- `vw_application_funnel`
- `vw_company_market_share`

## 2. Chart layout đề xuất

### Row 1: KPI overview

1. Total Active Jobs
2. Total Applications
3. Interview Rate
4. Offer Rate
5. Average Salary

### Row 2: Demand analytics

6. Job Demand by Industry (Bar chart)
7. Skill Demand (Horizontal Bar)
8. Salary Trend by Month (Line chart)

### Row 3: Recruitment funnel

9. Recruitment Funnel (Funnel chart)
10. Top Employers (Bar chart)
11. Top Positions (Bar chart)

## 3. Chi tiết chart

### Chart 1: Total Active Jobs

- Type: Big number / KPI
- Dataset: `Jobs`
- Metric: `COUNT(*)`
- Filter: `status = active`

### Chart 2: Job Demand by Industry

- Type: Bar chart
- X-axis: `industry`
- Metric: `COUNT(DISTINCT job_id)`

### Chart 3: Top Skills Demand

- Type: Horizontal bar chart
- X-axis: `skill_name`
- Metric: `COUNT(DISTINCT job_id)`

### Chart 4: Salary Trend by Industry

- Type: Line chart
- X-axis: `month_start`
- Series: `industry`
- Metric: `AVG(avg_salary)`

### Chart 5: Recruitment Funnel

- Type: Funnel chart
- Stages: `Application`, `Reviewed`, `Shortlisted`, `Interviewed`, `Offered`
- Metric: `COUNT(DISTINCT application_id)`

### Chart 6: Top Employers

- Type: Bar chart
- X-axis: `company_name`
- Metric: `COUNT(DISTINCT job_id)`

### Chart 7: Top Positions

- Type: Bar chart
- X-axis: `job_title`
- Metric: `COUNT(*)`

## 4. Bộ filter đề xuất

- `industry`
- `location`
- `position_level`
- `employment_type`
- `job_title`
- `status`
- `created_at` (date range)

## 5. Gợi ý cách cấu hình trong Superset

- Chọn dataset tương ứng
- Chọn metric và group by phù hợp
- Vào `Customize` để bật sorting + legend + labels
- Thêm time range filter nếu cần
- Dùng `Queries` để kiểm tra dữ liệu trước khi lưu dashboard

## 6. Lưu ý kỹ thuật

- Đảm bảo các field `date` được map đúng kiểu `TIMESTAMP`
- Kiểm tra null value trên `industry`, `location`, `salary_min`, `salary_max`
- Dùng `coalesce()` để tránh `NULL` làm rỗng hoặc gây lỗi
- Khi dashboard dùng filter đa giá trị, nên set `free form` hoặc `dropdown` tùy trường hợp
