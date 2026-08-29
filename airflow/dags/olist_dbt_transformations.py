from datetime import datetime, timezone
from pathlib import Path

from cosmos import DbtDag, ExecutionConfig, ProfileConfig, ProjectConfig


DBT_PROJECT_PATH = Path("/opt/airflow/dbt/olist_analytics")
DBT_EXECUTABLE_PATH = Path("/opt/airflow/dbt_venv/bin/dbt")
DBT_PROFILES_PATH = DBT_PROJECT_PATH / "profiles.yml"


olist_dbt_transformations = DbtDag(
    dag_id="olist_dbt_transformations",
    schedule=None,
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_tasks=4,
    default_args={
        "owner": "data-engineering",
        "retries": 2,
    },
    project_config=ProjectConfig(
        dbt_project_path=DBT_PROJECT_PATH,
    ),
    profile_config=ProfileConfig(
        profile_name="olist_analytics",
        target_name="dev",
        profiles_yml_filepath=DBT_PROFILES_PATH,
    ),
    execution_config=ExecutionConfig(
        dbt_executable_path=str(DBT_EXECUTABLE_PATH),
    ),
    operator_args={
        "install_deps": False,
    },
    tags=["olist", "dbt", "snowflake"],
)

