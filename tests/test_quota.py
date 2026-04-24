"""Tests for envault.quota."""

from __future__ import annotations

import pytest

from envault.backends.local import LocalBackend
from envault.quota import (
    set_quota,
    get_quota,
    delete_quota,
    check_quota,
    enforce_quota,
    QuotaConfig,
    QuotaStatus,
)


@pytest.fixture()
def backend(tmp_path):
    return LocalBackend(root=str(tmp_path))


def test_set_quota_returns_config(backend):
    config = set_quota(backend, max_keys=10)
    assert isinstance(config, QuotaConfig)
    assert config.max_keys == 10
    assert config.warn_threshold == 0.8


def test_set_quota_custom_warn_threshold(backend):
    config = set_quota(backend, max_keys=20, warn_threshold=0.5)
    assert config.warn_threshold == 0.5


def test_set_quota_invalid_max_keys_raises(backend):
    with pytest.raises(ValueError, match="max_keys"):
        set_quota(backend, max_keys=0)


def test_set_quota_invalid_warn_threshold_raises(backend):
    with pytest.raises(ValueError, match="warn_threshold"):
        set_quota(backend, max_keys=5, warn_threshold=0.0)


def test_get_quota_none_when_unset(backend):
    assert get_quota(backend) is None


def test_get_quota_returns_config(backend):
    set_quota(backend, max_keys=5, warn_threshold=0.6)
    config = get_quota(backend)
    assert config is not None
    assert config.max_keys == 5
    assert config.warn_threshold == 0.6


def test_delete_quota_removes_config(backend):
    set_quota(backend, max_keys=5)
    delete_quota(backend)
    assert get_quota(backend) is None


def test_delete_quota_noop_when_unset(backend):
    delete_quota(backend)  # should not raise


def test_check_quota_none_when_no_config(backend):
    backend.upload("prod", b"data")
    assert check_quota(backend) is None


def test_check_quota_returns_status(backend):
    backend.upload("prod", b"data")
    backend.upload("staging", b"data")
    set_quota(backend, max_keys=10)
    status = check_quota(backend)
    assert isinstance(status, QuotaStatus)
    assert status.current == 2
    assert status.max_keys == 10
    assert not status.exceeded
    assert not status.warning


def test_check_quota_warning(backend):
    for i in range(8):
        backend.upload(f"key{i}", b"data")
    set_quota(backend, max_keys=10, warn_threshold=0.7)
    status = check_quota(backend)
    assert status.warning
    assert not status.exceeded


def test_check_quota_exceeded(backend):
    for i in range(5):
        backend.upload(f"key{i}", b"data")
    set_quota(backend, max_keys=5)
    status = check_quota(backend)
    assert status.exceeded


def test_enforce_quota_raises_when_exceeded(backend):
    for i in range(3):
        backend.upload(f"key{i}", b"data")
    set_quota(backend, max_keys=3)
    with pytest.raises(RuntimeError, match="Quota exceeded"):
        enforce_quota(backend)


def test_enforce_quota_passes_when_under_limit(backend):
    backend.upload("only_one", b"data")
    set_quota(backend, max_keys=10)
    enforce_quota(backend)  # should not raise


def test_internal_quota_key_excluded_from_count(backend):
    set_quota(backend, max_keys=5)
    # Only the quota marker itself is in the backend; count should be 0
    status = check_quota(backend)
    assert status.current == 0
