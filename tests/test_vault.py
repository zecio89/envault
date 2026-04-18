"""Tests for the Vault high-level push/pull operations."""

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.backends.local import LocalBackend


PASSPHRASE = "test-passphrase-123"
SAMPLE_ENV = "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=supersecret\n"


@pytest.fixture
def vault(tmp_path):
    backend = LocalBackend(str(tmp_path / "store"))
    return Vault(backend, PASSPHRASE)


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(SAMPLE_ENV, encoding="utf-8")
    return p


def test_push_returns_key(vault, env_file):
    key = vault.push(env_file)
    assert key == ".env"


def test_push_custom_key(vault, env_file):
    key = vault.push(env_file, key="production")
    assert key == "production"
    assert vault.backend.exists("production")


def test_pull_roundtrip(vault, env_file):
    vault.push(env_file)
    plaintext = vault.pull(".env")
    assert plaintext == SAMPLE_ENV


def test_pull_writes_file(vault, env_file, tmp_path):
    vault.push(env_file)
    out = tmp_path / "recovered.env"
    vault.pull(".env", output_path=out)
    assert out.read_text(encoding="utf-8") == SAMPLE_ENV


def test_pull_wrong_passphrase_raises(vault, env_file):
    vault.push(env_file)
    bad_vault = Vault(vault.backend, "wrong-passphrase")
    with pytest.raises(Exception):
        bad_vault.pull(".env")


def test_push_missing_file_raises(vault, tmp_path):
    with pytest.raises(FileNotFoundError):
        vault.push(tmp_path / "nonexistent.env")


def test_list_envs(vault, env_file):
    vault.push(env_file, key="staging")
    vault.push(env_file, key="production")
    keys = vault.list_envs()
    assert set(keys) == {"staging", "production"}


def test_delete_env(vault, env_file):
    vault.push(env_file, key="temp")
    vault.delete_env("temp")
    assert not vault.backend.exists("temp")
