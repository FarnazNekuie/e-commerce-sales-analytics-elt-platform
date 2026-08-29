import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

from airflow.exceptions import AirflowException
from airflow.sdk import PokeReturnValue, dag, task
from cosmos import DbtTaskGroup, ExecutionConfig, ProfileConfig, ProjectConfig


DBT_PROJECT_PATH = Path("/opt/airflow/dbt/olist_analytics")
DBT_EXECUTABLE_PATH = Path("/opt/airflow/dbt_venv/bin/dbt")
DBT_PROFILES_PATH = DBT_PROJECT_PATH / "profiles.yml"

FIVETRAN_BASE_URL = "https://api.fivetran.com/v1"


def get_fivetran_auth() -> HTTPBasicAuth:
    return HTTPBasicAuth(
        os.environ["FIVETRAN_API_KEY"],
        os.environ["FIVETRAN_API_SECRET"],
    )


def get_connection_details() -> dict:
    connection_id = os.environ["FIVETRAN_CONNECTION_ID"]

    response = requests.get(
        f"{FIVETRAN_BASE_URL}/connections/{connection_id}",
        auth=get_fivetran_auth(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["data"]


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
        connection_id = os.environ["FIVETRAN_CONNECTION_ID"]
        previous_details = get_connection_details()

        previous_state = {
            "succeeded_at": previous_details.get("succeeded_at"),
            "failed_at": previous_details.get("failed_at"),
        }

        response = requests.post(
            f"{FIVETRAN_BASE_URL}/connections/{connection_id}/sync",
            auth=get_fivetran_auth(),
            headers={"Content-Type": "application/json"},
            json={"force": False},
            timeout=30,
        )

        if response.status_code == 409:
            code = response.json().get("code")
            if code != "AlreadyInSync":
                response.raise_for_status()
        else:
            response.raise_for_status()

        return previous_state

    @task.sensor(
        poke_interval=15,
        timeout=1800,
        mode="reschedule",
    )
    def wait_for_fivetran_sync(previous_state: dict) -> PokeReturnValue:
        details = get_connection_details()

        sync_state = details["status"]["sync_state"]
        succeeded_at = details.get("succeeded_at")
        failed_at = details.get("failed_at")

        if sync_state == "paused":
            raise AirflowException("Fivetran connection is paused.")

        new_failure = (
            failed_at
            and failed_at != previous_state.get("failed_at")
        )

        if new_failure and sync_state not in {"syncing", "rescheduled"}:
            raise AirflowException(
                f"Fivetran sync failed at {failed_at}."
            )

        sync_succeeded = (
            succeeded_at
            and succeeded_at != previous_state.get("succeeded_at")
            and sync_state not in {"syncing", "rescheduled"}
        )

        return PokeReturnValue(
            is_done=bool(sync_succeeded),
            xcom_value={
                "sync_state": sync_state,
                "succeeded_at": succeeded_at,
            } if sync_succeeded else None,
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

