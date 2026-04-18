import pytest
from envault.backends.local import LocalBackend
from envault.lock import lock_env, unlock_env, is_locked, list_locked


@pytest.fixture
def backend(tmp_path):
    return LocalBackend(str(tmp_path))


@pytest.fixture
def populated_backend(backend):
    backend.upload("prod", b"encrypted-data")
    backend.upload("staging", b"encrypted-data-2")
    return backend


def test_lock_creates_marker(populated_backend):
    lock_env(populated_backend, "prod")
    assert populated_backend.exists("prod.lock")


def test_is_locked_true(populated_backend):
    lock_env(populated_backend, "prod")
    assert is_locked(populated_backend, "prod") is True


def test_is_locked_false(populated_backend):
    assert is_locked(populated_backend, "prod") is False


def test_unlock_removes_marker(populated_backend):
    lock_env(populated_backend, "prod")
    unlock_env(populated_backend, "prod")
    assert not populated_backend.exists("prod.lock")


def test_lock_missing_key_raises(backend):
    with pytest.raises(KeyError, match="No such env"):
        lock_env(backend, "nonexistent")


def test_unlock_not_locked_raises(populated_backend):
    with pytest.raises(KeyError, match="not locked"):
        unlock_env(populated_backend, "prod")


def test_list_locked(populated_backend):
    lock_env(populated_backend, "prod")
    lock_env(populated_backend, "staging")
    locked = list_locked(populated_backend)
    assert sorted(locked) == ["prod", "staging"]


def test_list_locked_empty(populated_backend):
    assert list_locked(populated_backend) == []
