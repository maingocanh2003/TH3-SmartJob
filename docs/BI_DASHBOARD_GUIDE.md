# HƯỚNG DẪN CÀI ĐẶT & VẬN HÀNH BI DASHBOARD (CHECKLIST 03)

## 1. Mục tiêu

Tài liệu này hướng dẫn triển khai Dashboard phân tích thị trường lao động cho SmartJob bằng PostgreSQL + Apache Superset dựa trên các BI views đã được chuẩn hóa trong dự án.

---

## 2. Chuẩn bị backend và database

### 2.1. Cài dependencies backend

```bash
python -m pip install -r backend/requirements.txt
```

### 2.2. Apply BI views vào PostgreSQL

```bash
python backend/manage.py setup_bi_dashboard
```

### 2.3. Kiểm tra tính đúng đắn dữ liệu BI

```bash
python scripts/validate_bi_dashboard.py
```

---

## 3. Kết nối Apache Superset với PostgreSQL

1. Mở Superset.
2. Vào **Settings → Database Connections → + DATABASE**.
3. Chọn PostgreSQL và nhập SQLAlchemy URI:

```text
postgresql+psycopg2://smartjob_user:<DB_PASSWORD>@localhost:5433/smartjob_db
```

4. Bật:
   - `Expose in SQL Lab`
   - `Allow CREATE TABLE AS`
   - `Allow DML` (nếu cần thử nghiệm SQL nâng cao)
5. Nhấn **TEST CONNECTION** → **CONNECT**.

---

## 4. Tạo datasets trong Superset

Tạo lần lượt các dataset từ các views:

1. `bi.vw_job_market_fact`
2. `bi.vw_job_postings_by_industry`
3. `bi.vw_skill_demand`
4. `bi.vw_avg_salary_by_industry_position`
5. `bi.vw_recruitment_funnel`
6. `bi.vw_dashboard_kpis`

**Khuyến nghị cột thời gian mặc định:**

- Với dataset `bi.vw_job_market_fact`: chọn `created_at` làm temporal column.

---

## 5. Cấu hình biểu đồ theo Checklist 03

## 5.1. Biểu đồ số lượng tin tuyển dụng theo ngành nghề

- Dataset: `bi.vw_job_postings_by_industry`
- Chart type: `Bar Chart`
- Dimension: `industry`
- Metric: `SUM(total_jobs)`
- Sort: giảm dần

## 5.2. Biểu đồ nhu cầu kỹ năng doanh nghiệp

- Dataset: `bi.vw_skill_demand`
- Chart type: `Bar Chart`
- Dimension: `skill_name`
- Metric: `SUM(jobs_requiring_skill)`
- Row limit: 15

## 5.3. Biểu đồ mức lương trung bình theo ngành nghề/vị trí

- Dataset: `bi.vw_avg_salary_by_industry_position`
- Chart type: `Heatmap` (hoặc `Bar Chart` nếu muốn đơn giản)
- Group by: `industry`, `position_level`
- Metric: `AVG(avg_salary_mid)` hoặc `SUM(avg_salary_mid)` tùy thiết kế

## 5.4. Biểu đồ tỷ lệ ứng tuyển/phỏng vấn/tuyển dụng

- Dataset: `bi.vw_recruitment_funnel`
- Chart type: `Funnel Chart`
- Stages:
  1. `total_applications`
  2. `reviewed_or_higher`
  3. `interviewed`
  4. `hired_success`

## 5.5. KPI Cards

- Dataset: `bi.vw_dashboard_kpis`
- `Total Job Postings` → `total_job_postings`
- `Total Candidates` → `total_candidates`
- `Total Applications` → `total_applications`
- `Hiring Rate (%)` → `hiring_rate_pct`

---

## 6. Thiết lập bộ lọc dữ liệu (Native Filters)

Tạo filter với datasource `bi.vw_job_market_fact`:

1. **Ngành nghề**: cột `industry`
2. **Vị trí công việc**: cột `position_level`
3. **Khu vực**: cột `region`
4. **Thời gian**: cột `created_at` (time range)
5. **Mức lương**: cột `salary_mid` (range filter)

Apply filters đến các chart liên quan trong dashboard.

---

## 7. Kiểm thử bàn giao

## 7.1. Kiểm tra tính đúng số liệu

- So sánh chart/kpi với truy vấn trực tiếp ở SQL Lab từ các view `bi.*`.
- Chạy `python scripts/validate_bi_dashboard.py` để đối soát tự động.

## 7.2. Kiểm tra bộ lọc

- Chọn từng giá trị filter (industry, position, region, time, salary).
- Xác nhận các chart liên quan cập nhật đồng bộ.

## 7.3. Kiểm tra dữ liệu thiếu/null

- Đảm bảo giá trị thiếu hiển thị nhóm `Unknown` (không làm vỡ chart).
- Kiểm tra các tỷ lệ không bị lỗi chia 0 khi chưa có ứng tuyển.

---

## 8. Tham chiếu kỹ thuật

- SQL BI views: `docs/bi/checklist_03_bi_queries.sql`
- Spec dashboard: `docs/bi/superset_dashboard_spec.yaml`
- Command setup BI: `backend/api/management/commands/setup_bi_dashboard.py`
- Script validate: `scripts/validate_bi_dashboard.py`
- Báo cáo hoàn thành: `docs/CHECKLIST_3_BI_REPORT.md`
