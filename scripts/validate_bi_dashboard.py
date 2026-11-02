import os
from pathlib import Path

import psycopg2


def load_env(env_file: Path) -> None:
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip().strip("'\"")


def scalar(cursor, sql: str):
    cursor.execute(sql)
    row = cursor.fetchone()
    return row[0] if row else None


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    env_file = root / ".env"
    if not env_file.exists():
        raise FileNotFoundError(f"Missing .env file: {env_file}")

    load_env(env_file)

    conn = psycopg2.connect(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
    )

    with conn:
        with conn.cursor() as cur:
            total_jobs = scalar(cur, "SELECT COUNT(*) FROM jobs;")
            jobs_in_industry_view = scalar(cur, "SELECT COALESCE(SUM(total_jobs), 0) FROM bi.vw_job_postings_by_industry;")
            total_apps = scalar(cur, "SELECT COUNT(*) FROM applications;")
            funnel_apps = scalar(cur, "SELECT total_applications FROM bi.vw_recruitment_funnel;")

            null_industry_jobs = scalar(
                cur,
                """
                SELECT COUNT(*)
                FROM jobs j
                JOIN companies c ON c.company_id = j.company_id
                WHERE c.industry IS NULL OR TRIM(c.industry) = '';
                """,
            )
            duplicated_app_pairs = scalar(
                cur,
                """
                SELECT COUNT(*)
                FROM (
                    SELECT job_id, candidate_id, COUNT(*) AS c
                    FROM applications
                    GROUP BY job_id, candidate_id
                    HAVING COUNT(*) > 1
                ) d;
                """,
            )

            print("=== BI VALIDATION SUMMARY ===")
            print(f"jobs table count                         : {total_jobs}")
            print(f"sum(total_jobs) in vw_job_postings       : {jobs_in_industry_view}")
            print(f"applications table count                 : {total_apps}")
            print(f"total_applications in vw_recruitment     : {funnel_apps}")
            print(f"jobs with null/empty industry            : {null_industry_jobs}")
            print(f"duplicate (job_id, candidate_id) records : {duplicated_app_pairs}")

            if total_jobs != jobs_in_industry_view:
                raise RuntimeError("Mismatch: jobs count differs from vw_job_postings_by_industry.")
            if total_apps != funnel_apps:
                raise RuntimeError("Mismatch: applications count differs from vw_recruitment_funnel.")

            print("Validation passed: core BI metrics are consistent.")


if __name__ == "__main__":
    main()
