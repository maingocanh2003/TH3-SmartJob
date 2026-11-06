import json
from superset.app import create_app


def main():
    sqlalchemy_uri = "postgresql+psycopg2://smartjob_user:20032005@host.docker.internal:5432/smartjob_db"
    app = create_app()
    with app.app_context():
        from superset.extensions import db, security_manager
        from superset.models.core import Database
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.slice import Slice
        from superset.models.dashboard import Dashboard

        # 1. Ensure Database
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
        else:
            database.sqlalchemy_uri = sqlalchemy_uri
            db.session.commit()

        # 2. Ensure Datasets
        dataset_names = [
            ("bi", "vw_dashboard_kpis"),
            ("bi", "vw_applications_over_time"),
            ("bi", "vw_applications_by_status"),
            ("bi", "vw_skill_demand"),
            ("bi", "vw_job_postings_by_industry"),
            ("bi", "vw_recruitment_funnel"),
            ("bi", "vw_job_market_fact"),
        ]
        datasets = {}
        for schema_name, table_name in dataset_names:
            ds = (
                db.session.query(SqlaTable)
                .filter(SqlaTable.database_id == database.id)
                .filter(SqlaTable.schema == schema_name)
                .filter(SqlaTable.table_name == table_name)
                .one_or_none()
            )
            if ds is None:
                ds = SqlaTable(
                    database_id=database.id,
                    table_name=table_name,
                    schema=schema_name,
                    sql=None,
                    is_sqllab_view=False,
                )
                db.session.add(ds)
                db.session.commit()
            try:
                ds.fetch_metadata()
                if table_name == "vw_applications_over_time":
                    ds.main_dttm_col = "application_date"
                    for col in ds.columns:
                        if col.column_name == "application_date":
                            col.is_dttm = True
                db.session.commit()
            except Exception as e:
                print(f"Metadata warning for {table_name}: {e}")
            datasets[table_name] = ds

        # 3. Ensure Dashboard
        dash = db.session.query(Dashboard).filter(Dashboard.slug == "smartjob-bi").one_or_none()
        if dash is None:
            dash = Dashboard(
                dashboard_title="SmartJob - Dashboard BI Tuyển Dụng",
                slug="smartjob-bi",
                published=True,
            )
            db.session.add(dash)
            db.session.commit()
        else:
            dash.dashboard_title = "SmartJob - Dashboard BI Tuyển Dụng"
            dash.published = True
            db.session.commit()

        # 4. Create / Update Charts
        kpi_ds = datasets["vw_dashboard_kpis"]
        time_ds = datasets["vw_applications_over_time"]
        status_ds = datasets["vw_applications_by_status"]
        skill_ds = datasets["vw_skill_demand"]

        chart_defs = [
            (
                "KPI_ACTIVE_JOBS",
                "Tổng số tin tuyển dụng đang hoạt động",
                kpi_ds,
                "big_number_total",
                {
                    "datasource": f"{kpi_ds.id}__table",
                    "viz_type": "big_number_total",
                    "metric": {"expressionType": "SQL", "sqlExpression": "MAX(active_job_postings)", "label": "Tin đang tuyển"},
                    "subheader": "Tin tuyển dụng đang mở (Active)",
                    "y_axis_format": "SMART_NUMBER",
                    "header_font_size": 0.4,
                    "subheader_font_size": 0.15,
                },
            ),
            (
                "KPI_TOTAL_APPS",
                "Tổng số hồ sơ ứng tuyển",
                kpi_ds,
                "big_number_total",
                {
                    "datasource": f"{kpi_ds.id}__table",
                    "viz_type": "big_number_total",
                    "metric": {"expressionType": "SQL", "sqlExpression": "MAX(total_applications)", "label": "Tổng hồ sơ"},
                    "subheader": "Tổng đơn ứng tuyển đã nhận",
                    "y_axis_format": "SMART_NUMBER",
                    "header_font_size": 0.4,
                    "subheader_font_size": 0.15,
                },
            ),
            (
                "KPI_PENDING_APPS",
                "Số lượng ứng viên đang chờ xử lý",
                kpi_ds,
                "big_number_total",
                {
                    "datasource": f"{kpi_ds.id}__table",
                    "viz_type": "big_number_total",
                    "metric": {"expressionType": "SQL", "sqlExpression": "MAX(pending_applications)", "label": "Chờ xử lý"},
                    "subheader": "Hồ sơ mới tiếp nhận & đang xem xét",
                    "y_axis_format": "SMART_NUMBER",
                    "header_font_size": 0.4,
                    "subheader_font_size": 0.15,
                },
            ),
            (
                "KPI_HIRING_RATE",
                "Tỷ lệ tuyển dụng thành công (%)",
                kpi_ds,
                "big_number_total",
                {
                    "datasource": f"{kpi_ds.id}__table",
                    "viz_type": "big_number_total",
                    "metric": {"expressionType": "SQL", "sqlExpression": "MAX(hiring_rate_pct)", "label": "Tỷ lệ trúng tuyển (%)"},
                    "subheader": "Tỷ lệ ứng viên trúng tuyển / tổng đơn (%)",
                    "y_axis_format": "SMART_NUMBER",
                    "header_font_size": 0.4,
                    "subheader_font_size": 0.15,
                },
            ),
            (
                "CHART_APPS_TIMELINE",
                "Biểu đồ thống kê hồ sơ ứng tuyển theo thời gian",
                time_ds,
                "echarts_timeseries_line",
                {
                    "datasource": f"{time_ds.id}__table",
                    "viz_type": "echarts_timeseries_line",
                    "x_axis": "application_date",
                    "time_grain_sqla": "P1D",
                    "x_axis_sort_asc": True,
                    "metrics": [
                        {"expressionType": "SQL", "sqlExpression": "SUM(total_applications)", "label": "Tổng hồ sơ ứng tuyển", "optionName": "m_total"},
                        {"expressionType": "SQL", "sqlExpression": "SUM(accepted_count)", "label": "Hồ sơ trúng tuyển", "optionName": "m_acc"},
                    ],
                    "groupby": [],
                    "adhoc_filters": [],
                    "row_limit": 1000,
                    "area": True,
                    "opacity": 0.25,
                    "markerEnabled": True,
                    "markerSize": 6,
                    "show_legend": True,
                    "rich_tooltip": True,
                    "color_scheme": "supersetColors",
                    "y_axis_format": "SMART_NUMBER",
                },
            ),
            (
                "CHART_APPS_STATUS",
                "Phân bổ hồ sơ theo trạng thái quy trình tuyển dụng",
                status_ds,
                "pie",
                {
                    "datasource": f"{status_ds.id}__table",
                    "viz_type": "pie",
                    "groupby": ["status_label"],
                    "metric": {"expressionType": "SQL", "sqlExpression": "SUM(application_count)", "label": "Số hồ sơ"},
                    "adhoc_filters": [],
                    "row_limit": 20,
                    "donut": True,
                    "innerRadius": 45,
                    "outerRadius": 70,
                    "show_labels": True,
                    "show_legend": True,
                    "color_scheme": "supersetColors",
                },
            ),
            (
                "CHART_SKILL_DEMAND",
                "Top kỹ năng được tuyển dụng nhiều nhất",
                skill_ds,
                "echarts_timeseries_bar",
                {
                    "datasource": f"{skill_ds.id}__table",
                    "viz_type": "echarts_timeseries_bar",
                    "x_axis": "skill_name",
                    "metrics": [
                        {"expressionType": "SQL", "sqlExpression": "SUM(jobs_requiring_skill)", "label": "Số tin yêu cầu", "optionName": "m_skill"}
                    ],
                    "groupby": [],
                    "adhoc_filters": [],
                    "row_limit": 10,
                    "order_desc": True,
                    "show_legend": False,
                    "rich_tooltip": True,
                    "color_scheme": "supersetColors",
                },
            ),
        ]

        created_slices = {}
        dash_slices = []
        for key, name, ds, viz_type, params in chart_defs:
            slc = (
                db.session.query(Slice)
                .filter(Slice.slice_name == name)
                .filter(Slice.datasource_id == ds.id)
                .one_or_none()
            )
            params_with_dash = dict(params, dashboards=[dash.id])
            if slc is None:
                slc = Slice(
                    slice_name=name,
                    viz_type=viz_type,
                    datasource_id=ds.id,
                    datasource_type="table",
                    params=json.dumps(params_with_dash, ensure_ascii=False),
                )
                db.session.add(slc)
                db.session.commit()
            else:
                slc.viz_type = viz_type
                slc.params = json.dumps(params_with_dash, ensure_ascii=False)
                db.session.commit()
            created_slices[key] = slc
            dash_slices.append(slc)

        dash.slices = dash_slices

        # 5. Build clean Dashboard Grid Layout (position_json)
        k1 = created_slices["KPI_ACTIVE_JOBS"]
        k2 = created_slices["KPI_TOTAL_APPS"]
        k3 = created_slices["KPI_PENDING_APPS"]
        k4 = created_slices["KPI_HIRING_RATE"]
        c_time = created_slices["CHART_APPS_TIMELINE"]
        c_status = created_slices["CHART_APPS_STATUS"]
        c_skill = created_slices["CHART_SKILL_DEMAND"]

        position_json = {
            "DASHBOARD_VERSION_KEY": "v2",
            "ROOT_ID": {"id": "ROOT_ID", "type": "ROOT", "children": ["GRID_ID"]},
            "GRID_ID": {
                "id": "GRID_ID",
                "type": "GRID",
                "children": ["ROW-KPIS", "ROW-TIMELINE", "ROW-BOTTOM"],
                "parents": ["ROOT_ID"],
            },
            "HEADER_ID": {
                "id": "HEADER_ID",
                "type": "HEADER",
                "meta": {"text": "SmartJob - Dashboard BI Tuyển Dụng"},
            },
            "ROW-KPIS": {
                "id": "ROW-KPIS",
                "type": "ROW",
                "children": ["CHART-K1", "CHART-K2", "CHART-K3", "CHART-K4"],
                "parents": ["ROOT_ID", "GRID_ID"],
                "meta": {"background": "BACKGROUND_TRANSPARENT"},
            },
            "CHART-K1": {
                "id": "CHART-K1",
                "type": "CHART",
                "children": [],
                "parents": ["ROOT_ID", "GRID_ID", "ROW-KPIS"],
                "meta": {"chartId": k1.id, "sliceName": k1.slice_name, "width": 3, "height": 28},
            },
            "CHART-K2": {
                "id": "CHART-K2",
                "type": "CHART",
                "children": [],
                "parents": ["ROOT_ID", "GRID_ID", "ROW-KPIS"],
                "meta": {"chartId": k2.id, "sliceName": k2.slice_name, "width": 3, "height": 28},
            },
            "CHART-K3": {
                "id": "CHART-K3",
                "type": "CHART",
                "children": [],
                "parents": ["ROOT_ID", "GRID_ID", "ROW-KPIS"],
                "meta": {"chartId": k3.id, "sliceName": k3.slice_name, "width": 3, "height": 28},
            },
            "CHART-K4": {
                "id": "CHART-K4",
                "type": "CHART",
                "children": [],
                "parents": ["ROOT_ID", "GRID_ID", "ROW-KPIS"],
                "meta": {"chartId": k4.id, "sliceName": k4.slice_name, "width": 3, "height": 28},
            },
            "ROW-TIMELINE": {
                "id": "ROW-TIMELINE",
                "type": "ROW",
                "children": ["CHART-TIME", "CHART-STATUS"],
                "parents": ["ROOT_ID", "GRID_ID"],
                "meta": {"background": "BACKGROUND_TRANSPARENT"},
            },
            "CHART-TIME": {
                "id": "CHART-TIME",
                "type": "CHART",
                "children": [],
                "parents": ["ROOT_ID", "GRID_ID", "ROW-TIMELINE"],
                "meta": {"chartId": c_time.id, "sliceName": c_time.slice_name, "width": 7, "height": 50},
            },
            "CHART-STATUS": {
                "id": "CHART-STATUS",
                "type": "CHART",
                "children": [],
                "parents": ["ROOT_ID", "GRID_ID", "ROW-TIMELINE"],
                "meta": {"chartId": c_status.id, "sliceName": c_status.slice_name, "width": 5, "height": 50},
            },
            "ROW-BOTTOM": {
                "id": "ROW-BOTTOM",
                "type": "ROW",
                "children": ["CHART-SKILL"],
                "parents": ["ROOT_ID", "GRID_ID"],
                "meta": {"background": "BACKGROUND_TRANSPARENT"},
            },
            "CHART-SKILL": {
                "id": "CHART-SKILL",
                "type": "CHART",
                "children": [],
                "parents": ["ROOT_ID", "GRID_ID", "ROW-BOTTOM"],
                "meta": {"chartId": c_skill.id, "sliceName": c_skill.slice_name, "width": 12, "height": 48},
            },
        }
        dash.position_json = json.dumps(position_json, ensure_ascii=False)
        db.session.commit()

        # 6. Grant all_datasource_access & all_database_access to Gamma and Public roles for seamless iframe embedding
        for role_name in ["Gamma", "Public"]:
            role = security_manager.find_role(role_name)
            if role:
                for perm_name, vm_name in [
                    ("all_datasource_access", "all_datasource_access"),
                    ("all_database_access", "all_database_access"),
                    ("can_read", "Dashboard"),
                    ("can_read", "Chart"),
                    ("can_read", "Dataset"),
                    ("can_read", "Database"),
                ]:
                    pvm = security_manager.find_permission_view_menu(perm_name, vm_name)
                    if pvm and pvm not in role.permissions:
                        role.permissions.append(pvm)
                db.session.commit()

        print(f"SUCCESS: Provisioned Superset Dashboard ID={dash.id}, slug={dash.slug}")
        print(f"URL: http://localhost:8088/superset/dashboard/{dash.slug}/?standalone=true")


if __name__ == "__main__":
    main()
