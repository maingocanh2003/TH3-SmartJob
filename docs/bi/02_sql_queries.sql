-- =====================================================
-- SMARTJOB BI SQL QUERIES / VIEWS
-- Mục đích: phục vụ dashboard phân tích tuyển dụng, kỹ năng, lương và tỷ lệ chuyển đổi
-- =====================================================

-- 1) Tạo view tổng hợp dữ liệu tuyển dụng theo job
CREATE OR REPLACE VIEW bi_vw_job_market_overview AS
SELECT
    j.job_id,
    j.job_title,
    j.status,
    j.created_at,
    j.location,
    j.position_level,
    j.employment_type,
    j.num_of_positions,
    COALESCE(c.company_name, 'Unknown') AS company_name,
    COALESCE(c.industry, 'Unknown') AS industry,
    CASE
        WHEN j.salary_min IS NOT NULL AND j.salary_max IS NOT NULL THEN (j.salary_min + j.salary_max) / 2
        WHEN j.salary_min IS NOT NULL THEN j.salary_min
        WHEN j.salary_max IS NOT NULL THEN j.salary_max
        ELSE NULL
    END AS avg_salary,
    j.salary_min,
    j.salary_max,
    COALESCE(j.view_count, 0) AS view_count,
    (
        SELECT COUNT(*)
        FROM Applications a
        WHERE a.job_id = j.job_id
    ) AS application_count
FROM Jobs j
LEFT JOIN Companies c
    ON c.company_id = j.company_id;

-- 2) Job demand by industry
CREATE OR REPLACE VIEW bi_vw_job_demand_by_industry AS
SELECT
    industry,
    COUNT(DISTINCT job_id) AS jobs_count,
    ROUND(
        100.0 * COUNT(DISTINCT job_id) / NULLIF((SELECT COUNT(*) FROM Jobs WHERE status = 'active'), 0),
        2
    ) AS share_of_active_jobs_pct
FROM bi_vw_job_market_overview
WHERE status = 'active'
GROUP BY industry
ORDER BY jobs_count DESC;

-- 3) Top skill demand
CREATE OR REPLACE VIEW bi_vw_skill_demand AS
SELECT
    s.skill_name,
    s.category,
    COUNT(DISTINCT js.job_id) AS jobs_count,
    ROUND(
        100.0 * COUNT(DISTINCT js.job_id) / NULLIF((SELECT COUNT(*) FROM Jobs WHERE status = 'active'), 0),
        2
    ) AS share_of_active_jobs_pct
FROM Job_Skills js
JOIN Skills s ON s.skill_id = js.skill_id
JOIN Jobs j ON j.job_id = js.job_id
WHERE j.status = 'active'
GROUP BY s.skill_name, s.category
ORDER BY jobs_count DESC;

-- 4) Salary trend by month, industry, position
CREATE OR REPLACE VIEW bi_vw_salary_by_industry_and_role AS
WITH salary_base AS (
    SELECT
        DATE_TRUNC('month', created_at)::date AS month_start,
        COALESCE(industry, 'Unknown') AS industry,
        COALESCE(position_level, 'Unknown') AS position_level,
        avg_salary,
        job_id
    FROM bi_vw_job_market_overview
    WHERE status = 'active' AND avg_salary IS NOT NULL
)
SELECT
    month_start,
    industry,
    position_level,
    ROUND(AVG(avg_salary), 0) AS avg_salary_vnd,
    COUNT(DISTINCT job_id) AS jobs_count
FROM salary_base
GROUP BY month_start, industry, position_level
ORDER BY month_start DESC, avg_salary_vnd DESC;

-- 5) Recruitment funnel: application -> reviewed -> shortlisted -> interviewed -> offered
CREATE OR REPLACE VIEW bi_vw_recruitment_funnel AS
WITH funnel AS (
    SELECT
        COUNT(DISTINCT application_id) AS total_applications,
        COUNT(DISTINCT CASE WHEN status IN ('reviewing', 'shortlisted', 'interviewed', 'offered', 'rejected') THEN application_id END) AS reviewed,
        COUNT(DISTINCT CASE WHEN status IN ('shortlisted', 'interviewed', 'offered') THEN application_id END) AS shortlisted,
        COUNT(DISTINCT CASE WHEN status IN ('interviewed', 'offered') THEN application_id END) AS interviewed,
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

-- 6) View chuẩn hóa cho funnel dạng stage (Superset chart Funnel/Bar dễ dùng hơn)
CREATE OR REPLACE VIEW bi_vw_funnel_by_stage AS
SELECT 'Applications' AS stage_name, COUNT(*)::INT AS stage_count FROM Applications
UNION ALL
SELECT 'Reviewed', COUNT(*)::INT FROM Applications WHERE status IN ('reviewing', 'shortlisted', 'interviewed', 'offered', 'rejected')
UNION ALL
SELECT 'Shortlisted', COUNT(*)::INT FROM Applications WHERE status IN ('shortlisted', 'interviewed', 'offered')
UNION ALL
SELECT 'Interviewed', COUNT(*)::INT FROM Applications WHERE status IN ('interviewed', 'offered')
UNION ALL
SELECT 'Offered', COUNT(*)::INT FROM Applications WHERE status = 'offered';

-- 7) Top employer / company overview
CREATE OR REPLACE VIEW bi_vw_company_market_share AS
SELECT
    company_name,
    industry,
    COUNT(DISTINCT job_id) AS jobs_count,
    ROUND(AVG(avg_salary), 0) AS avg_salary_vnd,
    SUM(application_count) AS total_applications
FROM bi_vw_job_market_overview
WHERE status = 'active'
GROUP BY company_name, industry
ORDER BY jobs_count DESC, total_applications DESC;

-- 8) Top job title by volume
CREATE OR REPLACE VIEW bi_vw_top_job_titles AS
SELECT
    job_title,
    COUNT(*) AS jobs_count,
    ROUND(AVG(COALESCE(avg_salary, 0)), 0) AS avg_salary_vnd
FROM bi_vw_job_market_overview
WHERE status = 'active'
GROUP BY job_title
ORDER BY jobs_count DESC;

-- =====================================================
-- 9) CÂU LỆNH CHECK / VALIDATE DỮ LIỆU CHO DASHBOARD
-- =====================================================

-- Tổng số job đang active
SELECT COUNT(*) AS total_active_jobs
FROM Jobs
WHERE status = 'active';

-- Tổng số ứng tuyển
SELECT COUNT(*) AS total_applications
FROM Applications;

-- Phân bổ theo trạng thái ứng tuyển
SELECT status, COUNT(*) AS application_count
FROM Applications
GROUP BY status
ORDER BY application_count DESC;

-- Kiểm tra dữ liệu lương null
SELECT COUNT(*) AS jobs_missing_salary
FROM Jobs
WHERE status = 'active' AND salary_min IS NULL AND salary_max IS NULL;

-- Kiểm tra industry null / thiếu phân loại
SELECT COUNT(*) AS jobs_with_unknown_industry
FROM bi_vw_job_market_overview
WHERE status = 'active' AND industry = 'Unknown';

-- Kiểm tra duplicate / vi phạm khóa / ràng buộc
SELECT COUNT(*) AS duplicate_applications
FROM (
    SELECT job_id, candidate_id, COUNT(*) AS cnt
    FROM Applications
    GROUP BY job_id, candidate_id
    HAVING COUNT(*) > 1
) d;

-- Kiểm tra skill demand có null / missing name
SELECT COUNT(*) AS invalid_skill_rows
FROM Job_Skills js
LEFT JOIN Skills s ON s.skill_id = js.skill_id
WHERE s.skill_id IS NULL;

-- =====================================================
-- 10) GHI CHÚ DÙNG CHO APACHE SUPERSET
-- =====================================================
-- Dùng các view trên làm dataset trong Superset:
--   - bi_vw_job_demand_by_industry
--   - bi_vw_skill_demand
--   - bi_vw_salary_by_industry_and_role
--   - bi_vw_recruitment_funnel
--   - bi_vw_funnel_by_stage
--   - bi_vw_company_market_share
--   - bi_vw_top_job_titles
--
-- Khuyến nghị filter trong Superset:
--   - created_at / date range (từ Jobs hoặc Applications)
--   - industry
--   - location
--   - position_level
--   - employment_type
--   - company_name
--
-- Lưu ý: Vì dữ liệu thật từ PostgreSQL phải được kiểm tra trực tiếp trên DB. Nếu schema khác hoặc
-- database chưa tạo, tất cả view này sẽ báo lỗi ngay ở thời điểm chạy SQL.
