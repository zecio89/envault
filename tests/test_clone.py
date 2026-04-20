"""Tests for envault.clone and envault.cli_clone."""

from __future__ import annotations

import os
import pytest
from click.testing import CliRunner

from envault.backends.local import LocalBackend
from envault.clone import clone_env
from envault.crypto import decrypt, encrypt
from envault.cli_clone import clone


PASS = "secret"
NEW_PASS = "newsecret"
PLAIN = b"API_KEY=abc123\nDEBUG=true\n"


@pytest.fixture()
def backend(tmp_path):
    b = LocalBackend(str(tmp_path))
    b.upload("prod", encrypt(PLAIN, PASS))
    return b


def test_clone_returns_dict(backend):
    result = clone_env(backend, "prod", backend, "staging", PASS)
    assert result["source_key"] == "prod"
    assert result["dest_key"] == "staging"
    assert result["reencrypted"] is False


def test_clone_dest_exists_in_backend(backend):
    clone_env(backend, "prod", backend, "staging", PASS)
    assert backend.exists("staging")


def test_clone_roundtrip_same_passphrase(backend):
    clone_env(backend, "prod", backend, "staging", PASS)
    blob = backend.download("staging")
    assert decrypt(blob, PASS) == PLAIN


def test_clone_reencrypt_with_new_passphrase(backend):
    result = clone_env(backend, "prod", backend, "staging", PASS, new_passphrase=NEW_PASS)
    assert result["reencrypted"] is True
    blob = backend.download("staging")
    assert decrypt(blob, NEW_PASS) == PLAIN


def test_clone_missing_source_raises(backend):
    with pytest.raises(KeyError, match="missing"):
        clone_env(backend, "missing", backend, "dest", PASS)


def test_clone_existing_dest_raises(backend):
    clone_env(backend, "prod", backend, "staging", PASS)
    with pytest.raises(FileExistsError):
        clone_env(backend, "prod", backend, "staging", PASS)


def test_clone_overwrite_allowed(backend):
    clone_env(backend, "prod", backend, "staging", PASS)
    clone_env(backend, "prod", backend, "staging", PASS, overwrite=True)
    assert backend.exists("staging")


# --- CLI tests ---

@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_dir(tmp_path):
    b = LocalBackend(str(tmp_path))
    b.upload("prod", encrypt(PLAIN, PASS))
    return str(tmp_path)


def test_cli_clone_success(runner, env_dir):
    result = runner.invoke(
        clone,
        ["run", "prod", "staging", "--passphrase", PASS, "--env-dir", env_dir],
    )
    assert result.exit_code == 0, result.output
    assert "prod" in result.output
    assert "staging" in result.output


def test_cli_clone_missing_key_error(runner, env_dir):
    result = runner.invoke(
        clone,
        ["run", "nope", "staging", "--passphrase", PASS, "--env-dir", env_dir],
    )
    assert result.exit_code != 0
    assert "Error" in result.output
