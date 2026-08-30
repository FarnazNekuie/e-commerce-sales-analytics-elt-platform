import os

import requests
from requests.auth import HTTPBasicAuth

FIVETRAN_BASE_URL = "https://api.fivetran.com/v1"
ACTIVE_SYNC_STATES = {"syncing", "rescheduled"}


class FivetranSyncError(RuntimeError):
    """Raised when Fivetran reports an invalid connector or sync state."""


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


def trigger_sync() -> dict:
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
        if response.json().get("code") != "AlreadyInSync":
            response.raise_for_status()
    else:
        response.raise_for_status()

    return previous_state


def evaluate_sync(
    previous_state: dict,
    details: dict,
) -> tuple[bool, dict | None]:
    sync_state = details["status"]["sync_state"]
    succeeded_at = details.get("succeeded_at")
    failed_at = details.get("failed_at")

    if sync_state == "paused":
        raise FivetranSyncError("Fivetran connection is paused.")

    new_failure = failed_at and failed_at != previous_state.get("failed_at")
    if new_failure and sync_state not in ACTIVE_SYNC_STATES:
        raise FivetranSyncError(f"Fivetran sync failed at {failed_at}.")

    sync_succeeded = (
        succeeded_at
        and succeeded_at != previous_state.get("succeeded_at")
        and sync_state not in ACTIVE_SYNC_STATES
    )

    result = None
    if sync_succeeded:
        result = {
            "sync_state": sync_state,
            "succeeded_at": succeeded_at,
        }

    return bool(sync_succeeded), result
