# KPI Definition

## 1. Job Demand by Industry

### Mục tiêu

Đo lường số lượng tin tuyển dụng đang có trên thị trường theo ngành nghề.

### Công thức

```sql
COUNT(DISTINCT job_id)
```

### Mô tả

- Đếm số tin tuyển dụng active theo ngành của công ty
- Giúp đánh giá ngành nào đang nóng và có nhu cầu tuyển dụng cao

### SQL mẫu

```sql
SELECT
    COALESCE(c.industry, 'Unknown') AS industry,
    COUNT(DISTINCT j.job_id) AS jobs_count
FROM Jobs j
LEFT JOIN Companies c ON c.company_id = j.company_id
WHERE j.status = 'active'
GROUP BY COALESCE(c.industry, 'Unknown')
ORDER BY jobs_count DESC;
```

## 2. Skill Demand

### Mục tiêu

Xác định kỹ năng nào doanh nghiệp đang ưu tiên tuyển dụng.

### Công thức

```sql
COUNT(DISTINCT job_id)
```

### Mô tả

- Đếm số lượng job yêu cầu mỗi kỹ năng
- Hỗ trợ định hướng đào tạo nhân lực và tối ưu CV/AI matching

### SQL mẫu

```sql
SELECT
    s.skill_name,
    COUNT(DISTINCT js.job_id) AS jobs_count
FROM Job_Skills js
JOIN Skills s ON s.skill_id = js.skill_id
JOIN Jobs j ON j.job_id = js.job_id
WHERE j.status = 'active'
GROUP BY s.skill_name
ORDER BY jobs_count DESC;
```

## 3. Salary Trend by Industry / Position

### Mục tiêu

Phân tích xu hướng mức lương theo ngành và vị trí.

### Công thức

```sql
AVG((salary_min + salary_max) / 2)
```

### Mô tả

- Tính mức lương trung bình cho từng ngành / vị trí / tháng
- Hỗ trợ đánh giá thị trường và chuẩn bị mức lương cạnh tranh

### SQL mẫu

```sql
SELECT
    DATE_TRUNC('month', j.created_at)::date AS month_start,
    COALESCE(c.industry, 'Unknown') AS industry,
    j.position_level,
    ROUND(AVG(CASE
        WHEN j.salary_min IS NOT NULL AND j.salary_max IS NOT NULL THEN (j.salary_min + j.salary_max) / 2
        WHEN j.salary_min IS NOT NULL THEN j.salary_min
        WHEN j.salary_max IS NOT NULL THEN j.salary_max
        ELSE NULL
    END), 0) AS avg_salary
FROM Jobs j
LEFT JOIN Companies c ON c.company_id = j.company_id
WHERE j.status = 'active'
GROUP BY DATE_TRUNC('month', j.created_at)::date, COALESCE(c.industry, 'Unknown'), j.position_level
ORDER BY month_start DESC;
```

## 4. Recruitment Conversion Funnel

### Mục tiêu

Đo tỷ lệ chuyển đổi từ ứng tuyển đến phỏng vấn đến offer.

### Công thức

- review_rate = reviewed / total_applications
- shortlist_rate = shortlisted / reviewed
- interview_rate = interviewed / shortlisted
- offer_rate = offered / interviewed
- overall_hire_rate = offered / total_applications

### Mô tả

- Hiểu hiệu suất tuyển dụng và điểm nghẽn của quy trình

### SQL mẫu

```sql
WITH funnel AS (
    SELECT
        COUNT(DISTINCT application_id) AS total_applications,
        COUNT(DISTINCT CASE WHEN status IN ('reviewing','shortlisted','interviewed','offered','rejected') THEN application_id END) AS reviewed,
        COUNT(DISTINCT CASE WHEN status IN ('shortlisted','interviewed','offered') THEN application_id END) AS shortlisted,
        COUNT(DISTINCT CASE WHEN status IN ('interviewed','offered') THEN application_id END) AS interviewed,
        COUNT(DISTINCT CASE WHEN status = 'offered' THEN application_id END) AS offered
    FROM Applications
)
SELECT
    total_applications,
    reviewed,
    shortlisted,
    interviewed,
    offered,
    ROUND(100.0 * reviewed / NULLIF(total_applications, 0), 2) AS review_rate_pct,
    ROUND(100.0 * shortlisted / NULLIF(reviewed, 0), 2) AS shortlist_rate_pct,
    ROUND(100.0 * interviewed / NULLIF(shortlisted, 0), 2) AS interview_rate_pct,
    ROUND(100.0 * offered / NULLIF(interviewed, 0), 2) AS offer_rate_pct,
    ROUND(100.0 * offered / NULLIF(total_applications, 0), 2) AS overall_hire_rate_pct
FROM funnel;
```

## 5. Top Employers / Top Positions

### Mục tiêu

Xác định công ty và vị trí đang chiếm ưu thế trên thị trường.

### SQL mẫu

```sql
SELECT
    c.company_name,
    COUNT(DISTINCT j.job_id) AS jobs_count
FROM Jobs j
JOIN Companies c ON c.company_id = j.company_id
WHERE j.status = 'active'
GROUP BY c.company_name
ORDER BY jobs_count DESC
LIMIT 10;
```

## 6. Ý nghĩa kinh doanh

- Các ngành có job demand cao cho biết thị trường đang ưu tiên lĩnh vực nào
- Top kỹ năng phản ánh nhu cầu nhân lực và định hướng đào tạo
- Xu hướng mức lương giúp quản lý có định giá nhân sự phù hợp
- Funnel conversion cho biết hiệu suất tuyển dụng và các bước cần cải thiện
