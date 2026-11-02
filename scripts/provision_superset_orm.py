import os

from superset.app import create_app
from superset.extensions import db
from superset.models.core import Database
from superset.connectors.sqla.models import SqlaTable


def load_env(path: str = "d:/TH3-SmartJob/.env"):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip("'\"")


def main():
    load_env()
    sqlalchemy_uri = (
        f"postgresql+psycopg2://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
    )

    app = create_app()
    with app.app_context():
        database = db.session.query(Database).filter(Database.database_name == "SmartJob PostgreSQL").one_or_none()
        if database is None:
            database = Database(
                database_name="SmartJob PostgreSQL",
                sqlalchemy_uri=sqlalchemy_uri,
                expose_in_sqllab=True,
                allow_ctas=True,
                allow_cvas=True,
                allow_dml=True,
            )
            db.session.add(database)
            db.session.commit()

        datasets = [
            ("bi", "vw_job_market_fact"),
            ("bi", "vw_job_postings_by_industry"),
            ("bi", "vw_skill_demand"),
            ("bi", "vw_avg_salary_by_industry_position"),
            ("bi", "vw_recruitment_funnel"),
            ("bi", "vw_dashboard_kpis"),
        ]

        for schema_name, table_name in datasets:
            existing = (
                db.session.query(SqlaTable)
                .filter(SqlaTable.database_id == database.id)
                .filter(SqlaTable.schema == schema_name)
                .filter(SqlaTable.table_name == table_name)
                .one_or_none()
            )
            if existing is not None:
                continue

            ds = SqlaTable(
                database_id=database.id,
                table_name=table_name,
                schema=schema_name,
                sql=None,
                is_sqllab_view=False,
            )
            db.session.add(ds)
            db.session.commit()

            ds.fetch_metadata()
            db.session.commit()

        print("Superset ORM provisioning finished.")
        print(f"Database ID: {database.id}")


if __name__ == "__main__":
    main()
