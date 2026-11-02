import json
import os
from pathlib import Path

import requests


SUPERSET_URL = "http://127.0.0.1:8088"
SUPERSET_USER = "admin"
SUPERSET_PASSWORD = "admin123"
DATABASE_NAME = "SmartJob PostgreSQL"
DASHBOARD_TITLE = "SmartJob - Labor Market BI Dashboard"


DATASETS = [
	("bi", "vw_job_market_fact"),
	("bi", "vw_job_postings_by_industry"),
	("bi", "vw_skill_demand"),
	("bi", "vw_avg_salary_by_industry_position"),
	("bi", "vw_recruitment_funnel"),
	("bi", "vw_dashboard_kpis"),
]


def load_env() -> None:
	env_file = Path(__file__).resolve().parents[1] / ".env"
	for line in env_file.read_text(encoding="utf-8").splitlines():
		line = line.strip()
		if line and not line.startswith("#") and "=" in line:
			key, value = line.split("=", 1)
			os.environ[key.strip()] = value.strip().strip("'\"")


def build_sqlalchemy_uri() -> str:
	db_name = os.environ["DB_NAME"]
	db_user = os.environ["DB_USER"]
	db_password = os.environ["DB_PASSWORD"]
	db_host = os.environ["DB_HOST"]
	db_port = os.environ["DB_PORT"]
	return f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def login(session: requests.Session) -> tuple[str, str]:
	login_resp = session.post(
		f"{SUPERSET_URL}/api/v1/security/login",
		json={
			"username": SUPERSET_USER,
			"password": SUPERSET_PASSWORD,
			"provider": "db",
			"refresh": True,
		},
		timeout=30,
	)
	login_resp.raise_for_status()
	access_token = login_resp.json()["access_token"]

	csrf_resp = session.get(
		f"{SUPERSET_URL}/api/v1/security/csrf_token/",
		headers={"Authorization": f"Bearer {access_token}"},
		timeout=30,
	)
	csrf_resp.raise_for_status()
	csrf_token = csrf_resp.json()["result"]
	return access_token, csrf_token


def api_get(session: requests.Session, token: str, path: str, params: dict | None = None) -> dict:
	resp = session.get(
		f"{SUPERSET_URL}{path}",
		headers={"Authorization": f"Bearer {token}"},
		params=params,
		timeout=30,
	)
	resp.raise_for_status()
	return resp.json()


def api_post(session: requests.Session, token: str, csrf: str, path: str, payload: dict) -> dict:
	resp = session.post(
		f"{SUPERSET_URL}{path}",
		headers={
			"Authorization": f"Bearer {token}",
			"X-CSRFToken": csrf,
			"Referer": SUPERSET_URL,
		},
		json=payload,
		timeout=30,
	)
	if resp.status_code >= 400:
		raise RuntimeError(f"POST {path} failed ({resp.status_code}): {resp.text}")
	return resp.json()


def ensure_database(session: requests.Session, token: str, csrf: str, sqlalchemy_uri: str) -> int:
	dbs = api_get(session, token, "/api/v1/database/", params={"page_size": 1000}).get("result", [])
	for db in dbs:
		if db.get("database_name") == DATABASE_NAME:
			return db["id"]

	created = api_post(
		session,
		token,
		csrf,
		"/api/v1/database/",
		{
			"database_name": DATABASE_NAME,
			"sqlalchemy_uri": sqlalchemy_uri,
			"expose_in_sqllab": True,
			"allow_ctas": True,
			"allow_cvas": True,
			"allow_dml": True,
		},
	)
	return created["id"]


def ensure_datasets(session: requests.Session, token: str, csrf: str, database_id: int) -> dict[str, int]:
	existing = api_get(session, token, "/api/v1/dataset/", params={"page_size": 1000}).get("result", [])
	existing_map = {
		(row.get("schema"), row.get("table_name"), row.get("database", {}).get("id")): row["id"]
		for row in existing
	}

	dataset_ids: dict[str, int] = {}
	for schema, table_name in DATASETS:
		key = (schema, table_name, database_id)
		if key in existing_map:
			dataset_ids[table_name] = existing_map[key]
			continue

		created = api_post(
			session,
			token,
			csrf,
			"/api/v1/dataset/",
			{
				"database": database_id,
				"schema": schema,
				"table_name": table_name,
			},
		)
		dataset_ids[table_name] = created["id"]

	return dataset_ids


def ensure_dashboard(session: requests.Session, token: str, csrf: str) -> int:
	dashboards = api_get(session, token, "/api/v1/dashboard/", params={"page_size": 1000}).get("result", [])
	for dashboard in dashboards:
		if dashboard.get("dashboard_title") == DASHBOARD_TITLE:
			return dashboard["id"]

	created = api_post(
		session,
		token,
		csrf,
		"/api/v1/dashboard/",
		{"dashboard_title": DASHBOARD_TITLE, "published": True},
	)
	return created["id"]


def ensure_chart(
	session: requests.Session,
	token: str,
	csrf: str,
	existing_charts: list[dict],
	chart_name: str,
	dataset_id: int,
	viz_type: str,
	form_data: dict,
	dashboard_id: int,
) -> None:
	for chart in existing_charts:
		if chart.get("slice_name") == chart_name:
			return

	payload = {
		"slice_name": chart_name,
		"viz_type": viz_type,
		"datasource_id": dataset_id,
		"datasource_type": "table",
		"params": json.dumps(form_data),
		"dashboards": [dashboard_id],
	}
	api_post(session, token, csrf, "/api/v1/chart/", payload)


def main() -> None:
	load_env()
	sqlalchemy_uri = build_sqlalchemy_uri()

	session = requests.Session()
	token, csrf = login(session)

	database_id = ensure_database(session, token, csrf, sqlalchemy_uri)
	dataset_ids = ensure_datasets(session, token, csrf, database_id)
	dashboard_id = ensure_dashboard(session, token, csrf)

	charts = api_get(session, token, "/api/v1/chart/", params={"page_size": 1000}).get("result", [])

	ensure_chart(
		session,
		token,
		csrf,
		charts,
		"Số lượng tin tuyển dụng theo ngành nghề",
		dataset_ids["vw_job_postings_by_industry"],
		"dist_bar",
		{
			"datasource": f"{dataset_ids['vw_job_postings_by_industry']}__table",
			"viz_type": "dist_bar",
			"groupby": ["industry"],
			"metrics": ["sum__total_jobs"],
			"row_limit": 1000,
			"adhoc_filters": [],
		},
		dashboard_id,
	)

	ensure_chart(
		session,
		token,
		csrf,
		charts,
		"Nhu cầu kỹ năng của doanh nghiệp",
		dataset_ids["vw_skill_demand"],
		"dist_bar",
		{
			"datasource": f"{dataset_ids['vw_skill_demand']}__table",
			"viz_type": "dist_bar",
			"groupby": ["skill_name"],
			"metrics": ["sum__jobs_requiring_skill"],
			"row_limit": 15,
			"adhoc_filters": [],
		},
		dashboard_id,
	)

	ensure_chart(
		session,
		token,
		csrf,
		charts,
		"Mức lương trung bình theo ngành nghề và vị trí",
		dataset_ids["vw_avg_salary_by_industry_position"],
		"heatmap",
		{
			"datasource": f"{dataset_ids['vw_avg_salary_by_industry_position']}__table",
			"viz_type": "heatmap",
			"all_columns_x": "industry",
			"all_columns_y": "position_level",
			"metric": "avg__avg_salary_mid",
			"adhoc_filters": [],
		},
		dashboard_id,
	)

	ensure_chart(
		session,
		token,
		csrf,
		charts,
		"Tỷ lệ ứng tuyển - phỏng vấn - tuyển dụng thành công",
		dataset_ids["vw_recruitment_funnel"],
		"table",
		{
			"datasource": f"{dataset_ids['vw_recruitment_funnel']}__table",
			"viz_type": "table",
			"all_columns": [
				"total_applications",
				"reviewed_or_higher",
				"interviewed",
				"hired_success",
				"reviewed_rate_pct",
				"interview_rate_pct",
				"hiring_success_rate_pct",
			],
			"row_limit": 100,
			"adhoc_filters": [],
		},
		dashboard_id,
	)

	print("Superset provisioning completed.")
	print(f"Database ID: {database_id}")
	print(f"Dashboard ID: {dashboard_id}")
	print(f"Datasets: {dataset_ids}")


if __name__ == "__main__":
	main()
