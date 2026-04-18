"""Tests for envault.history module."""
import pytest
from pathlib import Path
from envault.backends.local import LocalBackend
from envault.history import record_version, get_history, restore_version, clear_history


@pytest.fixture
def backend(tmp_path: Path) -> LocalBackend:
    return LocalBackend(str(tmp_path))


def test_get_history_empty_when_no_log(backend):
    assert get_history(backend, "prod") == []


def test_record_version_returns_entry(backend):
    entry = record_version(backend, "prod", "enc_blob_1", actor="alice")
    assert entry["version"] == 1
    assert entry["actor"] == "alice"
    assert entry["blob"] == "enc_blob_1"
    assert "timestamp" in entry


def test_record_multiple_versions(backend):
    record_version(backend, "prod", "blob_v1")
    record_version(backend, "prod", "blob_v2", note="hotfix")
    history = get_history(backend, "prod")
    assert len(history) == 2
    assert history[0]["version"] == 1
    assert history[1]["version"] == 2
    assert history[1]["note"] == "hotfix"


def test_restore_version_returns_correct_blob(backend):
    record_version(backend, "staging", "blob_v1")
    record_version(backend, "staging", "blob_v2")
    assert restore_version(backend, "staging", 1) == "blob_v1"
    assert restore_version(backend, "staging", 2) == "blob_v2"


def test_restore_version_missing_raises(backend):
    record_version(backend, "dev", "blob_v1")
    with pytest.raises(KeyError, match="Version 99"):
        restore_version(backend, "dev", 99)


def test_clear_history(backend):
    record_version(backend, "prod", "blob_v1")
    clear_history(backend, "prod")
    assert get_history(backend, "prod") == []


def test_clear_history_noop_when_missing(backend):
    # Should not raise
    clear_history(backend, "nonexistent")


def test_histories_are_independent(backend):
    record_version(backend, "prod", "p_blob")
    record_version(backend, "dev", "d_blob1")
    record_version(backend, "dev", "d_blob2")
    assert len(get_history(backend, "prod")) == 1
    assert len(get_history(backend, "dev")) == 2
