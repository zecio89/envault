import pytest
from envault.backends.local import LocalBackend
from envault.crypto import encrypt
from envault.snapshot import create_snapshot, list_snapshots, restore_snapshot, delete_snapshot


@pytest.fixture
def backend(tmp_path):
    return LocalBackend(str(tmp_path))


@pytest.fixture
def populated_backend(backend):
    pp = "pass123"
    backend.upload("prod", encrypt("KEY=val1", pp).encode())
    backend.upload("staging", encrypt("KEY=val2", pp).encode())
    return backend, pp


def test_create_snapshot_returns_metadata(populated_backend):
    backend, pp = populated_backend
    result = create_snapshot(backend, pp, name="snap1")
    assert result["name"] == "snap1"
    assert result["key_count"] == 2


def test_create_snapshot_stores_in_backend(populated_backend):
    backend, pp = populated_backend
    create_snapshot(backend, pp, name="snap1")
    assert "snap1" in list_snapshots(backend)


def test_create_snapshot_auto_name(populated_backend):
    backend, pp = populated_backend
    result = create_snapshot(backend, pp)
    assert result["name"] in list_snapshots(backend)


def test_create_snapshot_empty_raises(backend):
    with pytest.raises(ValueError, match="No environment keys"):
        create_snapshot(backend, "pass")


def test_list_snapshots_empty(backend):
    assert list_snapshots(backend) == []


def test_restore_snapshot_overwrites_keys(populated_backend):
    backend, pp = populated_backend
    create_snapshot(backend, pp, name="snap1")
    backend.upload("prod", encrypt("KEY=changed", pp).encode())
    restored = restore_snapshot(backend, "snap1", pp)
    assert "prod" in restored and "staging" in restored


def test_restore_snapshot_wrong_passphrase_raises(populated_backend):
    backend, pp = populated_backend
    create_snapshot(backend, pp, name="snap1")
    with pytest.raises(Exception):
        restore_snapshot(backend, "snap1", "wrongpass")


def test_delete_snapshot(populated_backend):
    backend, pp = populated_backend
    create_snapshot(backend, pp, name="snap1")
    delete_snapshot(backend, "snap1")
    assert "snap1" not in list_snapshots(backend)


def test_delete_snapshot_missing_raises(backend):
    with pytest.raises(KeyError, match="snap1"):
        delete_snapshot(backend, "snap1")
