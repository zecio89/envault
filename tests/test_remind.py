"""Tests for envault.remind."""

import pytest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
from envault.backends.local import LocalBackend
from envault.remind import (
    record_rotation,
    get_rotation_info,
    check_overdue,
    list_overdue,
    delete_reminder,
)


@pytest.fixture
def backend(tmp_path):
    b = LocalBackend(str(tmp_path))
    b.upload("prod", b"encrypted-blob")
    b.upload("staging", b"encrypted-blob-2")
    return b


def test_record_rotation_returns_entry(backend):
    entry = record_rotation(backend, "prod")
    assert entry["env_key"] == "prod"
    assert "last_rotated" in entry


def test_record_rotation_missing_key_raises(backend):
    with pytest.raises(KeyError):
        record_rotation(backend, "nonexistent")


def test_get_rotation_info_none_when_unrecorded(backend):
    assert get_rotation_info(backend, "prod") is None


def test_get_rotation_info_returns_entry(backend):
    record_rotation(backend, "prod")
    info = get_rotation_info(backend, "prod")
    assert info is not None
    assert info["env_key"] == "prod"


def test_check_overdue_true_when_no_record(backend):
    assert check_overdue(backend, "prod", max_days=30) is True


def test_check_overdue_false_when_just_rotated(backend):
    record_rotation(backend, "prod")
    assert check_overdue(backend, "prod", max_days=30) is False


def test_check_overdue_true_when_old(backend):
    record_rotation(backend, "prod")
    future = datetime.now(timezone.utc) + timedelta(days=31)
    with patch("envault.remind.datetime") as mock_dt:
        mock_dt.now.return_value = future
        mock_dt.fromisoformat = datetime.fromisoformat
        assert check_overdue(backend, "prod", max_days=30) is True


def test_list_overdue_returns_all_when_none_recorded(backend):
    overdue = list_overdue(backend, max_days=30)
    assert set(overdue) == {"prod", "staging"}


def test_list_overdue_excludes_rotated(backend):
    record_rotation(backend, "prod")
    overdue = list_overdue(backend, max_days=30)
    assert "prod" not in overdue
    assert "staging" in overdue


def test_delete_reminder_removes_record(backend):
    record_rotation(backend, "prod")
    delete_reminder(backend, "prod")
    assert get_rotation_info(backend, "prod") is None


def test_delete_reminder_noop_when_missing(backend):
    delete_reminder(backend, "prod")  # should not raise
