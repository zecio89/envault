"""Tests for envault.checksum."""

from __future__ import annotations

import json
import pytest

from envault.backends.local import LocalBackend
from envault.checksum import (
    delete_checksum,
    get_checksum,
    record_checksum,
    verify_checksum,
)


@pytest.fixture()
def backend(tmp_path):
    return LocalBackend(str(tmp_path))


@pytest.fixture()
def populated_backend(backend):
    backend.upload("prod", b"encrypted-blob-content")
    return backend


# ---------------------------------------------------------------------------
# record_checksum
# ---------------------------------------------------------------------------

def test_record_checksum_returns_dict(populated_backend):
    result = record_checksum(populated_backend, "prod")
    assert result["env_key"] == "prod"
    assert result["algorithm"] == "sha256"
    assert len(result["checksum"]) == 64  # hex SHA-256


def test_record_checksum_stored_in_backend(populated_backend):
    record_checksum(populated_backend, "prod")
    ck_key = "__checksums__/prod.json"
    assert populated_backend.exists(ck_key)
    stored = json.loads(populated_backend.download(ck_key).decode())
    assert stored["env_key"] == "prod"


def test_record_checksum_missing_key_raises(backend):
    with pytest.raises(KeyError, match="prod"):
        record_checksum(backend, "prod")


def test_record_checksum_overwrites_previous(populated_backend):
    """Re-recording after a blob update should reflect the new checksum."""
    first = record_checksum(populated_backend, "prod")
    populated_backend.upload("prod", b"new-encrypted-blob-content")
    second = record_checksum(populated_backend, "prod")
    assert first["checksum"] != second["checksum"]


# ---------------------------------------------------------------------------
# get_checksum
# ---------------------------------------------------------------------------

def test_get_checksum_returns_none_when_unrecorded(populated_backend):
    assert get_checksum(populated_backend, "prod") is None


def test_get_checksum_returns_record(populated_backend):
    record_checksum(populated_backend, "prod")
    result = get_checksum(populated_backend, "prod")
    assert result is not None
    assert result["algorithm"] == "sha256"


# ---------------------------------------------------------------------------
# verify_checksum
# ---------------------------------------------------------------------------

def test_verify_checksum_true_when_intact(populated_backend):
    record_checksum(populated_backend, "prod")
    assert verify_checksum(populated_backend, "prod") is True


def test_verify_checksum_false_when_no_record(populated_backend):
    assert verify_checksum(populated_backend, "prod") is False


def test_verify_checksum_false_after_blob_tampered(populated_backend):
    record_checksum(populated_backend, "prod")
    # Overwrite blob with different content
    populated_backend.upload("prod", b"tampered-content")
    assert verify_checksum(populated_backend, "prod") is False


# ---------------------------------------------------------------------------
# delete_checksum
# ---------------------------------------------------------------------------

def test_delete_checksum_removes_record(populated_backend):
    record_checksum(populated_backend, "prod")
    delete_checksum(populated_backend, "prod")
    assert get_checksum(populated_backend, "prod") is None


def test_delete_checksum_idempotent(populated_backend):
    """Deleting a checksum that does not exist should not raise."""
    delete_checksum(populated_backend, "prod")  # no record yet
    assert get_checksum(populated_backend, "prod") is None
