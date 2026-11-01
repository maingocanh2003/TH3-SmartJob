# SmartJob Market Intelligence Dashboard

## 1. Mục tiêu

Dashboard này hỗ trợ phân tích thị trường lao động cho dự án SmartJob, tập trung vào:

- số lượng tin tuyển dụng theo ngành nghề
- nhu cầu kỹ năng của doanh nghiệp
- xu hướng mức lương theo ngành/vị trí
- tỷ lệ ứng tuyển, phỏng vấn và tuyển dụng thành công
- phân tích doanh nghiệp và vị trí hot trên thị trường

## 2. Nguồn dữ liệu

- PostgreSQL
- Schema dự án SmartJob
- Bảng chính: `Jobs`, `Companies`, `Applications`, `Skills`, `Job_Skills`, `AI_Match_Results`

## 3. KPI chính

1. Tổng số tin tuyển dụng đang hoạt động
2. Số lượng ứng tuyển theo thời gian
3. Tỷ lệ review / shortlist / interview / offer
4. Top kỹ năng hot nhất
5. Mức lương trung bình theo ngành / vị trí
6. Số lượng job theo công ty, ngành, vị trí

## 4. Dashboard Superset

Tên dashboard đề xuất:

- `SmartJob Market Overview`

Các chart chính đề xuất:

- KPI cards
- Bar chart: Job demand by industry
- Horizontal bar: Top skills demanded
- Line chart: Salary trend by industry
- Funnel chart: Recruitment conversion funnel
- Bar chart: Top employers
- Treemap/Bar: Top positions

## 5. Bộ lọc đề xuất

- industry
- location
- position_level
- employment_type
- job_title
- created_at / date range
- status

## 6. Hướng dẫn sử dụng

- Kết nối PostgreSQL đến Superset
- Tạo dataset từ SQL view / table gốc
- Thêm chart theo từng KPI
- Gắn filter vào toàn dashboard
- Save dashboard và export screenshot khi bàn giao

## 7. Người nhận sản phẩm

- Product Owner / PM
- Data Analyst / BI
- Nhà tuyển dụng / Hiring manager
- Team phát triển SmartJob

## 8. Tài liệu đi kèm

- `01_kpi_definition.md`
- `02_sql_queries.sql`
- `03_superset_dashboard_spec.md`
- `04_data_quality_checklist.md`
