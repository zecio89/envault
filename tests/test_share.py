import pytest
from envault.backends.local import LocalBackend
from envault.crypto import encrypt
from envault.acl import set_acl
from envault.share import share_env, retrieve_share, list_shares, delete_share


@pytest.fixture
def backend(tmp_path):
    return LocalBackend(str(tmp_path))


@pytest.fixture
def populated_backend(backend):
    content = "DB_HOST=localhost\nDB_PASS=secret\n"
    blob = encrypt(content, "old-pass")
    backend.upload("production", blob.encode())
    return backend


def test_share_env_returns_share_key(populated_backend):
    share_key = share_env(
        populated_backend, "production", "old-pass", "recv-pass", ["alice", "bob"]
    )
    assert share_key == "__shares__/production/alice+bob"


def test_share_stored_in_backend(populated_backend):
    share_env(populated_backend, "production", "old-pass", "recv-pass", ["alice"])
    assert populated_backend.exists("__shares__/production/alice")


def test_retrieve_share_roundtrip(populated_backend):
    content = "DB_HOST=localhost\nDB_PASS=secret\n"
    share_env(populated_backend, "production", "old-pass", "recv-pass", ["alice"])
    result = retrieve_share(populated_backend, "production", ["alice"], "recv-pass")
    assert result == content


def test_retrieve_share_wrong_passphrase_raises(populated_backend):
    share_env(populated_backend, "production", "old-pass", "recv-pass", ["alice"])
    with pytest.raises(Exception):
        retrieve_share(populated_backend, "production", ["alice"], "wrong-pass")


def test_share_missing_key_raises(backend):
    with pytest.raises(KeyError, match="not found"):
        share_env(backend, "nonexistent", "old-pass", "recv-pass", ["alice"])


def test_share_acl_blocks_unauthorized(populated_backend):
    set_acl(populated_backend, "production", ["carol"])
    with pytest.raises(PermissionError):
        share_env(
            populated_backend, "production", "old-pass", "recv-pass",
            ["alice"], actor="eve"
        )


def test_list_shares(populated_backend):
    share_env(populated_backend, "production", "old-pass", "recv-pass", ["alice"])
    share_env(populated_backend, "production", "old-pass", "recv-pass", ["bob"])
    shares = list_shares(populated_backend, "production")
    assert len(shares) == 2


def test_delete_share(populated_backend):
    share_env(populated_backend, "production", "old-pass", "recv-pass", ["alice"])
    delete_share(populated_backend, "production", ["alice"])
    assert not populated_backend.exists("__shares__/production/alice")


def test_delete_share_missing_raises(backend):
    with pytest.raises(KeyError):
        delete_share(backend, "production", ["alice"])
