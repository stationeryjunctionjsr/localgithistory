import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.jobs.valet_timeout_job import _cascade_or_revert_return
from app.models.schemas import PushNotificationPayload, PushNotificationMetadata


@pytest.mark.asyncio
async def test_cascade_or_revert_return_with_next_valet():
    mock_return = MagicMock()
    mock_return.id = 501
    mock_return.return_id = "RET-501"
    mock_return.valet_decline_history = []
    mock_return.valet_cascade_count = 0

    mock_valet = MagicMock()
    mock_valet.id = 999

    with patch("app.jobs.valet_timeout_job._find_next_available_valet_for_return", new=AsyncMock(return_value=mock_valet)), \
         patch("app.jobs.valet_timeout_job.return_request_repository.update", new=AsyncMock(return_value=True)), \
         patch("app.services.push_notification_service.push_notification_service.send_to_user", new=AsyncMock(return_value={"deliveredCount": 1})) as mock_send:

        await _cascade_or_revert_return(mock_return)

        # Ensure send_to_user was called with PushNotificationPayload
        assert mock_send.called
        call_args = mock_send.call_args[0]
        assert call_args[0] == "999"
        payload = call_args[1]
        assert isinstance(payload, PushNotificationPayload)
        assert payload.title == "New Return Pickup Request"
        assert isinstance(payload.data, PushNotificationMetadata)
        assert payload.data.return_id == 501
        assert payload.data.type == "valet_return_assignment"


@pytest.mark.asyncio
async def test_cascade_or_revert_return_revert_to_admin():
    mock_return = MagicMock()
    mock_return.id = 502
    mock_return.return_id = "RET-502"
    mock_return.valet_decline_history = []
    mock_return.valet_cascade_count = 1

    mock_admin = MagicMock()
    mock_admin.id = 1

    with patch("app.jobs.valet_timeout_job._find_next_available_valet_for_return", new=AsyncMock(return_value=None)), \
         patch("app.jobs.valet_timeout_job.return_request_repository.update", new=AsyncMock(return_value=True)), \
         patch("app.jobs.valet_timeout_job.user_repository.findSuperAdmin", new=AsyncMock(return_value=mock_admin)), \
         patch("app.services.push_notification_service.push_notification_service.send_to_user", new=AsyncMock(return_value={"deliveredCount": 1})) as mock_send:

        await _cascade_or_revert_return(mock_return)

        assert mock_send.called
        call_args = mock_send.call_args[0]
        assert call_args[0] == "1"
        payload = call_args[1]
        assert isinstance(payload, PushNotificationPayload)
        assert payload.title == "Return Valet Unavailable — Reassign Required"
        assert isinstance(payload.data, PushNotificationMetadata)
        assert payload.data.return_id == 502
        assert payload.data.type == "valet_return_all_declined"
