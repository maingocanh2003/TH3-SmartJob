from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Create/refresh BI schema and dashboard views for Superset (Checklist 03)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sql-file",
            dest="sql_file",
            default="docs/bi/checklist_03_bi_queries.sql",
            help="Relative path from project root to SQL file.",
        )

    def handle(self, *args, **options):
        project_root = Path(__file__).resolve().parents[4]
        sql_path = project_root / options["sql_file"]

        if not sql_path.exists():
            raise CommandError(f"SQL file not found: {sql_path}")

        sql_content = sql_path.read_text(encoding="utf-8")
        if not sql_content.strip():
            raise CommandError(f"SQL file is empty: {sql_path}")

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql_content)
        except Exception as exc:
            raise CommandError(f"Failed to apply BI SQL: {exc}") from exc

        self.stdout.write(self.style.SUCCESS("BI schema/views have been applied successfully."))
        self.stdout.write(self.style.NOTICE(f"Source SQL: {sql_path}"))
