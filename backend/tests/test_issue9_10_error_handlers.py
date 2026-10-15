import logging
from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest

from app.repositories.recommendation_repository import recommendation_repository
from app.utils.error_handler import EmailLogHandler, logger as eh_logger


def test_issue9_recommendation_parse_created_at_handles_corrupt_date_without_name_error():
    """Verify that _parse_created_at does not crash with NameError when parsing corrupt dates."""
    # 1. Corrupt string that raises in fromisoformat
    mock_record_corrupt = MagicMock()
    mock_record_corrupt.created_at = "INVALID_CORRUPT_TIMESTAMP"

    with patch.object(logging, "warning") as mock_warning:
        dt = recommendation_repository._parse_created_at(mock_record_corrupt)
        assert dt is None
        mock_warning.assert_called_once()
        log_args = mock_warning.call_args[0]
        # Ensure the log template received raw value without raising NameError
        assert "could not parse date value" in log_args[0]
        assert log_args[1] == "INVALID_CORRUPT_TIMESTAMP"

    # 2. None value
    mock_record_none = MagicMock()
    mock_record_none.created_at = None
    assert recommendation_repository._parse_created_at(mock_record_none) is None

    # 3. Valid ISO format
    mock_record_valid = MagicMock()
    mock_record_valid.created_at = "2026-10-15T12:00:00Z"
    valid_dt = recommendation_repository._parse_created_at(mock_record_valid)
    assert isinstance(valid_dt, datetime)
    assert valid_dt.year == 2026
    assert valid_dt.tzinfo is not None


def test_issue10_email_log_handler_emit_handles_malformed_user_without_name_error():
    """Verify that EmailLogHandler.emit does not crash with NameError: name 'logger' is not defined."""
    handler = EmailLogHandler()

    class FailingPart:
        def split(self, *args, **kwargs):
            raise ValueError("Simulated malformed user line error")

    class FailingMessage(str):
        def split(self, sep=None, maxsplit=-1):
            if sep == "user ":
                return ["Error message for ", FailingPart()]
            return super().split(sep, maxsplit)

    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="Critical failure encountered for user ",
        args=(),
        exc_info=None,
    )

    with patch.object(handler, "format", return_value=FailingMessage("Critical failure encountered for user ")):
        with patch.object(eh_logger, "debug") as mock_debug:
            handler.emit(record)
            mock_debug.assert_called_once()
            assert "Could not extract user from error message" in mock_debug.call_args[0][0]
