from datetime import datetime, timezone
from pathlib import Path

from airflow.exceptions import AirflowException
from airflow.sdk import PokeReturnValue, dag, task
from cosmos import DbtTaskGroup, ExecutionConfig, ProfileConfig, ProjectConfig
from fivetran_client import (
    FivetranSyncError,
    evaluate_sync,
    get_connection_details,
    trigger_sync,
)

DBT_PROJECT_PATH = Path("/opt/airflow/dbt/olist_analytics")
DBT_EXECUTABLE_PATH = Path("/opt/airflow/dbt_venv/bin/dbt")
DBT_PROFILES_PATH = DBT_PROJECT_PATH / "profiles.yml"


@dag(
    dag_id="olist_elt_pipeline",
    schedule=None,
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_tasks=4,
    default_args={
        "owner": "data-engineering",
        "retries": 2,
    },
    tags=["olist", "fivetran", "dbt", "snowflake"],
)
def build_olist_elt_pipeline():

    @task
    def trigger_fivetran_sync() -> dict:
        return trigger_sync()

    @task.sensor(
        poke_interval=15,
        timeout=1800,
        mode="reschedule",
    )
    def wait_for_fivetran_sync(previous_state: dict) -> PokeReturnValue:
        details = get_connection_details()

        try:
            is_done, result = evaluate_sync(previous_state, details)
        except FivetranSyncError as error:
            raise AirflowException(str(error)) from error

        return PokeReturnValue(
            is_done=is_done,
            xcom_value=result,
        )

    previous_state = trigger_fivetran_sync()
    sync_complete = wait_for_fivetran_sync(previous_state)

    dbt_transformations = DbtTaskGroup(
        group_id="dbt_transformations",
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
    )

    sync_complete >> dbt_transformations


olist_elt_pipeline = build_olist_elt_pipeline()
