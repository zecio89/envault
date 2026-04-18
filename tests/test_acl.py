import pytest
from envault.backends.local import LocalBackend
from envault.acl import set_acl, get_acl, delete_acl, is_allowed, list_acls


@pytest.fixture
def backend(tmp_path):
    b = LocalBackend(str(tmp_path))
    # Seed a couple of env keys
    b.upload("production", b"encrypted-blob-1")
    b.upload("staging", b"encrypted-blob-2")
    return b


def test_set_and_get_acl(backend):
    acl = set_acl(backend, "production", ["alice", "bob"])
    assert acl["key"] == "production"
    assert "alice" in acl["allowed_users"]
    assert "bob" in acl["allowed_users"]

    fetched = get_acl(backend, "production")
    assert fetched == acl


def test_get_acl_returns_empty_when_none(backend):
    acl = get_acl(backend, "staging")
    assert acl["key"] == "staging"
    assert acl["allowed_users"] == []


def test_set_acl_raises_for_missing_key(backend):
    with pytest.raises(KeyError, match="nonexistent"):
        set_acl(backend, "nonexistent", ["alice"])


def test_set_acl_deduplicates_users(backend):
    acl = set_acl(backend, "production", ["alice", "alice", "bob"])
    assert acl["allowed_users"].count("alice") == 1


def test_delete_acl(backend):
    set_acl(backend, "production", ["alice"])
    delete_acl(backend, "production")
    acl = get_acl(backend, "production")
    assert acl["allowed_users"] == []


def test_delete_acl_noop_when_missing(backend):
    # Should not raise
    delete_acl(backend, "staging")


def test_is_allowed_when_no_acl_set(backend):
    assert is_allowed(backend, "staging", "anyone") is True


def test_is_allowed_true(backend):
    set_acl(backend, "production", ["alice"])
    assert is_allowed(backend, "production", "alice") is True


def test_is_allowed_false(backend):
    set_acl(backend, "production", ["alice"])
    assert is_allowed(backend, "production", "eve") is False


def test_list_acls(backend):
    set_acl(backend, "production", ["alice"])
    set_acl(backend, "staging", ["bob"])
    acls = list_acls(backend)
    keys = {a["key"] for a in acls}
    assert keys == {"production", "staging"}
