"""Tests for envault.search module."""
import pytest
from envault.backends.local import LocalBackend
from envault.crypto import encrypt
from envault.search import search_keys

PASS = "hunter2"


@pytest.fixture()
def backend(tmp_path):
    b = LocalBackend(root=str(tmp_path))
    b.upload("staging/app", encrypt("DB_HOST=localhost\nDB_PORT=5432", PASS).encode())
    b.upload("staging/worker", encrypt("REDIS_URL=redis://localhost\nDEBUG=false", PASS).encode())
    b.upload("prod/app", encrypt("DB_HOST=prod.db\nSECRET_KEY=abc123", PASS).encode())
    return b


def test_search_key_match(backend):
    results = search_keys(backend, "staging")
    keys = [r["key"] for r in results]
    assert "staging/app" in keys
    assert "staging/worker" in keys
    assert "prod/app" not in keys


def test_search_key_case_insensitive(backend):
    results = search_keys(backend, "STAGING")
    assert len(results) == 2


def test_search_no_match(backend):
    results = search_keys(backend, "nonexistent")
    assert results == []


def test_search_values_requires_passphrase(backend):
    with pytest.raises(ValueError, match="passphrase is required"):
        search_keys(backend, "localhost", search_values=True)


def test_search_values_finds_match(backend):
    results = search_keys(backend, "localhost", passphrase=PASS, search_values=True)
    matched_keys = [r["key"] for r in results]
    assert "staging/app" in matched_keys
    assert "staging/worker" in matched_keys


def test_search_values_line_numbers(backend):
    results = search_keys(backend, "DB_PORT", passphrase=PASS, search_values=True)
    assert len(results) == 1
    assert results[0]["key"] == "staging/app"
    assert results[0]["value_matches"][0]["line"] == 2


def test_search_key_and_value_combined(backend):
    # 'app' matches key; 'SECRET_KEY' only in prod/app values
    results = search_keys(backend, "app", passphrase=PASS, search_values=True)
    keys = [r["key"] for r in results]
    assert "staging/app" in keys
    assert "prod/app" in keys
