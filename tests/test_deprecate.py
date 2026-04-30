"""Tests for envault.deprecate."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from envault.backends.local import LocalBackend
from envault.deprecate import (
    clear_deprecation,
    get_deprecation,
    is_sunset,
    list_deprecated,
    mark_deprecated,
)


@pytest.fixture()
def backend(tmp_path):
    b = LocalBackend(root=str(tmp_path))
    # Seed a couple of real env keys so mark_deprecated doesn't raise
    b.upload("production", b"encrypted-blob")
    b.upload("staging", b"encrypted-blob-2")
    return b


def test_mark_deprecated_returns_record(backend):
    record = mark_deprecated(backend, "production", reason="Use new key")
    assert record["key"] == "production"
    assert record["reason"] == "Use new key"
    assert record["replacement"] is None
    assert record["sunset"] is None
    assert "deprecated_at" in record


def test_mark_deprecated_with_replacement_and_sunset(backend):
    record = mark_deprecated(
        backend, "staging", reason="Migrating", replacement="prod", sunset="2099-01-01"
    )
    assert record["replacement"] == "prod"
    assert record["sunset"] == "2099-01-01"


def test_mark_deprecated_missing_key_raises(backend):
    with pytest.raises(KeyError, match="nonexistent"):
        mark_deprecated(backend, "nonexistent", reason="gone")


def test_get_deprecation_returns_record(backend):
    mark_deprecated(backend, "production", reason="Old")
    record = get_deprecation(backend, "production")
    assert record is not None
    assert record["key"] == "production"


def test_get_deprecation_returns_none_when_not_marked(backend):
    assert get_deprecation(backend, "production") is None


def test_clear_deprecation_returns_true_when_exists(backend):
    mark_deprecated(backend, "production", reason="Old")
    assert clear_deprecation(backend, "production") is True
    assert get_deprecation(backend, "production") is None


def test_clear_deprecation_returns_false_when_not_marked(backend):
    assert clear_deprecation(backend, "production") is False


def test_list_deprecated_returns_all(backend):
    mark_deprecated(backend, "production", reason="Old")
    mark_deprecated(backend, "staging", reason="Migrating")
    records = list_deprecated(backend)
    keys = {r["key"] for r in records}
    assert keys == {"production", "staging"}


def test_list_deprecated_empty_when_none(backend):
    assert list_deprecated(backend) == []


def test_is_sunset_false_for_future_date():
    future = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()
    record = {"sunset": future}
    assert is_sunset(record) is False


def test_is_sunset_true_for_past_date():
    past = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
    record = {"sunset": past}
    assert is_sunset(record) is True


def test_is_sunset_false_when_no_sunset():
    assert is_sunset({"sunset": None}) is False
    assert is_sunset({}) is False
