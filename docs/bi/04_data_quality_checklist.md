# Data Quality Checklist

## 1. Kiểm tra schema và dữ liệu

- [ ] Bảng `Jobs` có `status`, `created_at`, `company_id`, `salary_min`, `salary_max`
- [ ] Bảng `Companies` có `industry`, `company_name`
- [ ] Bảng `Applications` có `status`, `applied_at`, `job_id`, `candidate_id`
- [ ] Bảng `Job_Skills` có `job_id`, `skill_id`
- [ ] Bảng `Skills` có `skill_name`

## 2. Kiểm tra null/invalid value

- [ ] `industry` null được fill bằng `Unknown`
- [ ] `salary_min` / `salary_max` null được xử lý trong công thức lương
- [ ] `location` rỗng được xử lý với `COALESCE`
- [ ] `status` phải nằm trong tập hợp xác định

## 3. Kiểm tra logic KPI

- [ ] Số lượng job active = `COUNT(*) WHERE status = 'active'`
- [ ] Job demand by industry = `COUNT(DISTINCT job_id)` theo ngành
- [ ] Skill demand = `COUNT(DISTINCT job_id)` theo kỹ năng
- [ ] Salary average = tính đúng từ min/max hoặc fallback
- [ ] Recruitment funnel = các stage không trùng nhau và tính trên cùng tập dữ liệu

## 4. Kiểm tra dashboard

- [ ] Có filter đúng cho `industry`, `location`, `position_level`, `date range`
- [ ] Tên chart rõ ràng và phù hợp với KPI
- [ ] Có label, unit, và color coding rõ
- [ ] Không có chart sai đơn vị hoặc sai metric
- [ ] Dashboard lưu đúng sau khi chỉnh config

## 5. Đánh giá chất lượng dữ liệu cuối cùng

- [ ] Dữ liệu khớp với thực tế business
- [ ] KPI có thể giải thích được cho stakeholder
- [ ] Dashboard có thể dùng để ra quyết định tuyển dụng / nhân sự
- [ ] Có phiên bản screenshot hoặc bản backup giao nhận

## 6. Kết luận QA

Nếu tất cả checklist trên đạt, dashboard có thể được bàn giao cho PM / BI / Stakeholder để sử dụng trong phân tích thực tế.
