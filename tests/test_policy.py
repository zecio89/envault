"""Tests for envault.policy."""

from __future__ import annotations

import pytest

from envault.backends.local import LocalBackend
from envault.policy import (
    delete_policy,
    get_policy,
    is_allowed,
    list_policies,
    set_policy,
)


@pytest.fixture()
def backend(tmp_path):
    b = LocalBackend(root=str(tmp_path))
    # seed a couple of real env keys
    b.upload("staging", b"encrypted-blob-staging")
    b.upload("production", b"encrypted-blob-production")
    return b


def test_set_and_get_policy(backend):
    rec = set_policy(backend, "staging", allowed_users=["alice", "bob"], read_only=True)
    assert rec["env_key"] == "staging"
    assert "alice" in rec["allowed_users"]
    assert rec["read_only"] is True
    fetched = get_policy(backend, "staging")
    assert fetched == rec


def test_get_policy_returns_none_when_unset(backend):
    assert get_policy(backend, "staging") is None


def test_set_policy_raises_for_missing_key(backend):
    with pytest.raises(KeyError, match="nonexistent"):
        set_policy(backend, "nonexistent", allowed_users=["alice"])


def test_set_policy_deduplicates_users(backend):
    rec = set_policy(backend, "staging", allowed_users=["alice", "alice", "bob"])
    assert rec["allowed_users"].count("alice") == 1


def test_set_policy_max_age_days(backend):
    rec = set_policy(backend, "staging", max_age_days=30)
    assert rec["max_age_days"] == 30


def test_delete_policy(backend):
    set_policy(backend, "staging", allowed_users=["alice"])
    delete_policy(backend, "staging")
    assert get_policy(backend, "staging") is None


def test_delete_policy_noop_when_unset(backend):
    delete_policy(backend, "staging")  # should not raise


def test_is_allowed_no_policy(backend):
    assert is_allowed(backend, "staging", "anyone") is True


def test_is_allowed_with_user_in_list(backend):
    set_policy(backend, "staging", allowed_users=["alice"])
    assert is_allowed(backend, "staging", "alice") is True


def test_is_allowed_user_not_in_list(backend):
    set_policy(backend, "staging", allowed_users=["alice"])
    assert is_allowed(backend, "staging", "eve") is False


def test_is_allowed_empty_list_means_all(backend):
    set_policy(backend, "staging", allowed_users=[])
    assert is_allowed(backend, "staging", "anyone") is True


def test_list_policies(backend):
    assert list_policies(backend) == []
    set_policy(backend, "staging", read_only=True)
    set_policy(backend, "production", allowed_users=["carol"])
    keys = list_policies(backend)
    assert set(keys) == {"staging", "production"}
