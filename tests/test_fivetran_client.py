from unittest.mock import Mock, patch

import pytest
import requests
from fivetran_client import (
    FivetranSyncError,
    evaluate_sync,
    trigger_sync,
)


def connection_details(
    sync_state: str,
    succeeded_at: str | None = None,
    failed_at: str | None = None,
) -> dict:
    return {
        "status": {"sync_state": sync_state},
        "succeeded_at": succeeded_at,
        "failed_at": failed_at,
    }


def test_evaluate_sync_returns_done_for_new_success():
    previous_state = {
        "succeeded_at": "2026-08-29T10:00:00Z",
        "failed_at": None,
    }
    details = connection_details(
        sync_state="scheduled",
        succeeded_at="2026-08-30T10:00:00Z",
    )

    is_done, result = evaluate_sync(previous_state, details)

    assert is_done is True
    assert result == {
        "sync_state": "scheduled",
        "succeeded_at": "2026-08-30T10:00:00Z",
    }


def test_evaluate_sync_waits_while_sync_is_active():
    previous_state = {
        "succeeded_at": "2026-08-29T10:00:00Z",
        "failed_at": None,
    }
    details = connection_details(
        sync_state="syncing",
        succeeded_at="2026-08-30T10:00:00Z",
    )

    is_done, result = evaluate_sync(previous_state, details)

    assert is_done is False
    assert result is None


def test_evaluate_sync_waits_when_timestamp_has_not_changed():
    previous_state = {
        "succeeded_at": "2026-08-30T10:00:00Z",
        "failed_at": None,
    }
    details = connection_details(
        sync_state="scheduled",
        succeeded_at="2026-08-30T10:00:00Z",
    )

    is_done, result = evaluate_sync(previous_state, details)

    assert is_done is False
    assert result is None


def test_evaluate_sync_rejects_paused_connection():
    previous_state = {
        "succeeded_at": None,
        "failed_at": None,
    }
    details = connection_details(sync_state="paused")

    with pytest.raises(
        FivetranSyncError,
        match="Fivetran connection is paused",
    ):
        evaluate_sync(previous_state, details)


def test_evaluate_sync_rejects_new_failure():
    previous_state = {
        "succeeded_at": None,
        "failed_at": "2026-08-29T10:00:00Z",
    }
    details = connection_details(
        sync_state="scheduled",
        failed_at="2026-08-30T10:00:00Z",
    )

    with pytest.raises(
        FivetranSyncError,
        match="Fivetran sync failed",
    ):
        evaluate_sync(previous_state, details)


@patch.dict(
    "os.environ",
    {
        "FIVETRAN_API_KEY": "test-key",
        "FIVETRAN_API_SECRET": "test-secret",
        "FIVETRAN_CONNECTION_ID": "test-connection",
    },
)
@patch("fivetran_client.requests.post")
@patch("fivetran_client.get_connection_details")
def test_trigger_sync_accepts_already_in_sync(
    mock_get_details,
    mock_post,
):
    mock_get_details.return_value = {
        "succeeded_at": "2026-08-29T10:00:00Z",
        "failed_at": None,
    }
    mock_response = Mock()
    mock_response.status_code = 409
    mock_response.json.return_value = {"code": "AlreadyInSync"}
    mock_post.return_value = mock_response

    previous_state = trigger_sync()

    assert previous_state == {
        "succeeded_at": "2026-08-29T10:00:00Z",
        "failed_at": None,
    }
    mock_response.raise_for_status.assert_not_called()
    mock_post.assert_called_once()


@patch.dict(
    "os.environ",
    {
        "FIVETRAN_API_KEY": "test-key",
        "FIVETRAN_API_SECRET": "test-secret",
        "FIVETRAN_CONNECTION_ID": "test-connection",
    },
)
@patch("fivetran_client.requests.post")
@patch("fivetran_client.get_connection_details")
def test_trigger_sync_rejects_other_conflict(
    mock_get_details,
    mock_post,
):
    mock_get_details.return_value = {
        "succeeded_at": None,
        "failed_at": None,
    }
    mock_response = Mock()
    mock_response.status_code = 409
    mock_response.json.return_value = {"code": "UnexpectedConflict"}
    mock_response.raise_for_status.side_effect = requests.HTTPError("409 Client Error")
    mock_post.return_value = mock_response

    with pytest.raises(requests.HTTPError, match="409 Client Error"):
        trigger_sync()

    mock_response.raise_for_status.assert_called_once()
