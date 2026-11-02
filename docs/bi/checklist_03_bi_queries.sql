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
            WHERE LOWER(COALESCE(status, '')) IN ('offered', 'hired', 'accepted')
        ) AS successful_applications
    FROM applications
)
SELECT
    (SELECT COUNT(*) FROM jobs) AS total_job_postings,
    (SELECT COUNT(*) FROM candidates) AS total_candidates,
    app_base.total_applications,
    app_base.total_applied_candidates,
    app_base.successful_applications,
    ROUND((app_base.successful_applications::numeric / NULLIF(app_base.total_applications, 0)) * 100.0, 2) AS hiring_rate_pct
FROM app_base;

-- =====================================================
-- Canonical SQL snippets for Superset charts
-- =====================================================

-- A. Job postings by industry
-- SELECT industry, total_jobs FROM bi.vw_job_postings_by_industry ORDER BY total_jobs DESC;

-- B. Top demanded skills
-- SELECT skill_name, jobs_requiring_skill, jobs_mandatory_skill FROM bi.vw_skill_demand ORDER BY jobs_requiring_skill DESC LIMIT 20;

-- C. Salary trend by industry / position
-- SELECT industry, position_level, avg_salary_mid FROM bi.vw_avg_salary_by_industry_position ORDER BY avg_salary_mid DESC NULLS LAST;

-- D. Recruitment funnel rates
-- SELECT reviewed_rate_pct, interview_rate_pct, hiring_success_rate_pct FROM bi.vw_recruitment_funnel;

-- E. KPI cards
-- SELECT * FROM bi.vw_dashboard_kpis;
