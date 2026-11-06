-- =====================================================
-- CHECKLIST 03 - BI / DASHBOARD (PostgreSQL)
-- SmartJob - Labor Market Analytics
-- =====================================================

CREATE SCHEMA IF NOT EXISTS bi;

-- 1) Base dataset for dashboard filters (industry, position, region, time, salary)
CREATE OR REPLACE VIEW bi.vw_job_market_fact AS
SELECT
    j.job_id,
    j.job_title,
    COALESCE(NULLIF(c.industry, ''), 'Unknown') AS industry,
    COALESCE(NULLIF(j.position_level, ''), 'Unknown') AS position_level,
    COALESCE(NULLIF(j.location, ''), 'Unknown') AS region,
    j.employment_type,
    j.status AS job_status,
    j.created_at,
    j.application_deadline,
    j.salary_min,
    j.salary_max,
    CASE
        WHEN j.salary_min IS NOT NULL AND j.salary_max IS NOT NULL THEN (j.salary_min + j.salary_max) / 2.0
        ELSE NULL
    END AS salary_mid,
    COUNT(DISTINCT a.application_id) AS application_count,
    COUNT(DISTINCT CASE WHEN LOWER(COALESCE(a.status, '')) IN ('interviewed') THEN a.application_id END) AS interviewed_count,
    COUNT(DISTINCT CASE WHEN LOWER(COALESCE(a.status, '')) IN ('offered', 'hired', 'accepted') THEN a.application_id END) AS hired_count,
    COUNT(DISTINCT js.job_skill_id) AS skill_requirement_count,
    COALESCE(j.view_count, 0) AS view_count
FROM jobs j
JOIN companies c ON c.company_id = j.company_id
LEFT JOIN applications a ON a.job_id = j.job_id
LEFT JOIN job_skills js ON js.job_id = j.job_id
GROUP BY
    j.job_id,
    j.job_title,
    c.industry,
    j.position_level,
    j.location,
    j.employment_type,
    j.status,
    j.created_at,
    j.application_deadline,
    j.salary_min,
    j.salary_max,
    j.view_count;

-- 2) Number of job postings by industry
CREATE OR REPLACE VIEW bi.vw_job_postings_by_industry AS
SELECT
    COALESCE(NULLIF(c.industry, ''), 'Unknown') AS industry,
    COUNT(DISTINCT j.job_id) AS total_jobs,
    COUNT(DISTINCT CASE WHEN LOWER(COALESCE(j.status, '')) = 'active' THEN j.job_id END) AS active_jobs,
    MIN(j.created_at) AS first_posted_at,
    MAX(j.created_at) AS latest_posted_at
FROM jobs j
JOIN companies c ON c.company_id = j.company_id
GROUP BY COALESCE(NULLIF(c.industry, ''), 'Unknown')
ORDER BY total_jobs DESC, industry;

-- 3) Skill demand from employers
CREATE OR REPLACE VIEW bi.vw_skill_demand AS
SELECT
    s.skill_id,
    s.skill_name,
    COALESCE(NULLIF(s.category, ''), 'Unknown') AS skill_category,
    COUNT(DISTINCT js.job_id) AS jobs_requiring_skill,
    COUNT(DISTINCT CASE WHEN js.is_required IS TRUE THEN js.job_id END) AS jobs_mandatory_skill,
    ROUND(AVG(COALESCE(js.weight, 1.0))::numeric, 2) AS avg_skill_weight
FROM job_skills js
JOIN skills s ON s.skill_id = js.skill_id
GROUP BY s.skill_id, s.skill_name, COALESCE(NULLIF(s.category, ''), 'Unknown')
ORDER BY jobs_requiring_skill DESC, jobs_mandatory_skill DESC, s.skill_name;

-- 4) Average salary by industry and position
CREATE OR REPLACE VIEW bi.vw_avg_salary_by_industry_position AS
SELECT
    COALESCE(NULLIF(c.industry, ''), 'Unknown') AS industry,
    COALESCE(NULLIF(j.position_level, ''), 'Unknown') AS position_level,
    COUNT(DISTINCT j.job_id) AS total_jobs,
    ROUND(AVG(j.salary_min)::numeric, 2) AS avg_salary_min,
    ROUND(AVG(j.salary_max)::numeric, 2) AS avg_salary_max,
    ROUND(
        AVG(
            CASE
                WHEN j.salary_min IS NOT NULL AND j.salary_max IS NOT NULL THEN (j.salary_min + j.salary_max) / 2.0
                ELSE NULL
            END
        )::numeric,
        2
    ) AS avg_salary_mid,
    MIN(j.salary_min) AS min_salary_observed,
    MAX(j.salary_max) AS max_salary_observed
FROM jobs j
JOIN companies c ON c.company_id = j.company_id
WHERE j.salary_min IS NOT NULL OR j.salary_max IS NOT NULL
GROUP BY COALESCE(NULLIF(c.industry, ''), 'Unknown'), COALESCE(NULLIF(j.position_level, ''), 'Unknown')
ORDER BY industry, position_level;

-- 5) Recruitment funnel (application -> interview -> hired)
CREATE OR REPLACE VIEW bi.vw_recruitment_funnel AS
WITH status_norm AS (
    SELECT
        a.application_id,
        a.job_id,
        LOWER(COALESCE(a.status, 'pending')) AS status_norm,
        a.applied_at
    FROM applications a
),
funnel AS (
    SELECT
        COUNT(DISTINCT application_id) AS total_applications,
        COUNT(DISTINCT CASE
            WHEN status_norm IN ('reviewing', 'shortlisted', 'interviewed', 'offered', 'hired', 'accepted')
            THEN application_id
        END) AS reviewed_or_higher,
        COUNT(DISTINCT CASE WHEN status_norm IN ('interviewed', 'offered', 'hired', 'accepted') THEN application_id END) AS interviewed,
        COUNT(DISTINCT CASE WHEN status_norm IN ('offered', 'hired', 'accepted') THEN application_id END) AS hired_success
    FROM status_norm
)
SELECT
    total_applications,
    reviewed_or_higher,
    interviewed,
    hired_success,
    ROUND((reviewed_or_higher::numeric / NULLIF(total_applications, 0)) * 100.0, 2) AS reviewed_rate_pct,
    ROUND((interviewed::numeric / NULLIF(total_applications, 0)) * 100.0, 2) AS interview_rate_pct,
    ROUND((hired_success::numeric / NULLIF(total_applications, 0)) * 100.0, 2) AS hiring_success_rate_pct
FROM funnel;

-- 6) KPI cards for dashboard header
CREATE OR REPLACE VIEW bi.vw_dashboard_kpis AS
WITH app_base AS (
    SELECT
        COUNT(*) AS total_applications,
        COUNT(DISTINCT candidate_id) AS total_applied_candidates,
        COUNT(*) FILTER (
            WHERE LOWER(COALESCE(status, 'pending')) IN ('pending', 'reviewing', 'shortlisted')
        ) AS pending_applications,
        COUNT(*) FILTER (
            WHERE LOWER(COALESCE(status, '')) IN ('offered', 'hired', 'accepted')
        ) AS successful_applications
    FROM applications
)
SELECT
    (SELECT COUNT(*) FROM jobs) AS total_job_postings,
    (SELECT COUNT(*) FROM jobs WHERE LOWER(COALESCE(status, '')) = 'active') AS active_job_postings,
    (SELECT COUNT(*) FROM candidates) AS total_candidates,
    app_base.total_applications,
    app_base.pending_applications,
    app_base.total_applied_candidates,
    app_base.successful_applications,
    ROUND((app_base.successful_applications::numeric / NULLIF(app_base.total_applications, 0)) * 100.0, 2) AS hiring_rate_pct
FROM app_base;

-- 7) Applications over time (for time-series chart in Superset & BI Dashboard)
CREATE OR REPLACE VIEW bi.vw_applications_over_time AS
SELECT
    DATE_TRUNC('day', COALESCE(a.applied_at, a.created_at, CURRENT_TIMESTAMP))::date AS application_date,
    COUNT(a.application_id) AS total_applications,
    COUNT(a.application_id) FILTER (WHERE LOWER(COALESCE(a.status, 'pending')) = 'pending') AS pending_count,
    COUNT(a.application_id) FILTER (WHERE LOWER(COALESCE(a.status, '')) IN ('reviewing', 'shortlisted')) AS reviewing_count,
    COUNT(a.application_id) FILTER (WHERE LOWER(COALESCE(a.status, '')) = 'interviewed') AS interviewed_count,
    COUNT(a.application_id) FILTER (WHERE LOWER(COALESCE(a.status, '')) IN ('offered', 'accepted', 'hired')) AS accepted_count,
    COUNT(a.application_id) FILTER (WHERE LOWER(COALESCE(a.status, '')) = 'rejected') AS rejected_count
FROM applications a
GROUP BY DATE_TRUNC('day', COALESCE(a.applied_at, a.created_at, CURRENT_TIMESTAMP))::date
ORDER BY application_date ASC;

-- 8) Applications by status breakdown
CREATE OR REPLACE VIEW bi.vw_applications_by_status AS
SELECT
    CASE LOWER(COALESCE(a.status, 'pending'))
        WHEN 'pending' THEN '1. Đã tiếp nhận'
        WHEN 'reviewing' THEN '2. Đang xem xét'
        WHEN 'shortlisted' THEN '2. Đang xem xét'
        WHEN 'interviewed' THEN '3. Mời phỏng vấn'
        WHEN 'offered' THEN '4. Trúng tuyển'
        WHEN 'rejected' THEN '5. Từ chối'
        ELSE 'Khác'
    END AS status_label,
    LOWER(COALESCE(a.status, 'pending')) AS status_code,
    COUNT(a.application_id) AS application_count
FROM applications a
GROUP BY status_label, LOWER(COALESCE(a.status, 'pending'))
ORDER BY status_label;
