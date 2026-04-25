"""Tests for envault.namespace."""

from __future__ import annotations

import pytest

from envault.backends.local import LocalBackend
from envault.namespace import (
    assign_namespace,
    delete_namespace,
    get_namespace_keys,
    list_namespaces,
    remove_from_namespace,
)


@pytest.fixture()
def backend(tmp_path):
    b = LocalBackend(root=str(tmp_path))
    # Pre-populate some env keys so assign_namespace can find them
    for key in ("prod/db", "prod/app", "staging/db"):
        b.upload(key, b"encrypted-blob")
    return b


def test_assign_creates_namespace(backend):
    result = assign_namespace(backend, "prod/db", "production")
    assert result["namespace"] == "production"
    assert result["env_key"] == "prod/db"
    assert "prod/db" in get_namespace_keys(backend, "production")


def test_assign_multiple_keys_to_namespace(backend):
    assign_namespace(backend, "prod/db", "production")
    assign_namespace(backend, "prod/app", "production")
    keys = get_namespace_keys(backend, "production")
    assert "prod/db" in keys
    assert "prod/app" in keys


def test_assign_idempotent(backend):
    assign_namespace(backend, "prod/db", "production")
    assign_namespace(backend, "prod/db", "production")
    keys = get_namespace_keys(backend, "production")
    assert keys.count("prod/db") == 1


def test_assign_moves_between_namespaces(backend):
    assign_namespace(backend, "prod/db", "ns-a")
    assign_namespace(backend, "prod/db", "ns-b")
    assert "prod/db" not in get_namespace_keys(backend, "ns-a")
    assert "prod/db" in get_namespace_keys(backend, "ns-b")


def test_assign_missing_key_raises(backend):
    with pytest.raises(KeyError, match="nonexistent"):
        assign_namespace(backend, "nonexistent", "production")


def test_list_namespaces_empty(backend):
    assert list_namespaces(backend) == []


def test_list_namespaces_returns_sorted(backend):
    assign_namespace(backend, "prod/db", "zzz")
    assign_namespace(backend, "prod/app", "aaa")
    ns = list_namespaces(backend)
    assert ns == ["aaa", "zzz"]


def test_remove_from_namespace(backend):
    assign_namespace(backend, "prod/db", "production")
    found = remove_from_namespace(backend, "prod/db", "production")
    assert found is True
    assert "prod/db" not in get_namespace_keys(backend, "production")


def test_remove_nonexistent_returns_false(backend):
    found = remove_from_namespace(backend, "prod/db", "production")
    assert found is False


def test_remove_last_key_deletes_namespace(backend):
    assign_namespace(backend, "prod/db", "solo")
    remove_from_namespace(backend, "prod/db", "solo")
    assert "solo" not in list_namespaces(backend)


def test_delete_namespace(backend):
    assign_namespace(backend, "prod/db", "production")
    deleted = delete_namespace(backend, "production")
    assert deleted is True
    assert "production" not in list_namespaces(backend)


def test_delete_namespace_not_found(backend):
    deleted = delete_namespace(backend, "ghost")
    assert deleted is False


def test_get_namespace_keys_unknown_namespace(backend):
    assert get_namespace_keys(backend, "does-not-exist") == []
