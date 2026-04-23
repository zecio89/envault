"""Tests for envault.verify."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.backends.local import LocalBackend
from envault.cli_verify import verify
from envault.crypto import encrypt
from envault.verify import VerifySummary, verify_env


PASSPHRASE = "test-secret"


@pytest.fixture()
def backend(tmp_path):
    return LocalBackend(path=str(tmp_path))


@pytest.fixture()
def populated_backend(backend):
    for name in ("prod", "staging", "dev"):
        blob = encrypt(f"KEY=value-{name}", PASSPHRASE)
        backend.upload(name, blob)
    return backend


def test_verify_returns_summary(populated_backend):
    summary = verify_env(populated_backend, PASSPHRASE)
    assert isinstance(summary, VerifySummary)
    assert len(summary.results) == 3


def test_verify_all_pass(populated_backend):
    summary = verify_env(populated_backend, PASSPHRASE)
    assert summary.all_ok
    assert len(summary.failed) == 0


def test_verify_single_key(populated_backend):
    summary = verify_env(populated_backend, PASSPHRASE, key="prod")
    assert len(summary.results) == 1
    assert summary.results[0].key == "prod"
    assert summary.results[0].ok


def test_verify_wrong_passphrase_fails(populated_backend):
    summary = verify_env(populated_backend, "wrong-passphrase")
    assert not summary.all_ok
    assert len(summary.failed) == 3
    for result in summary.failed:
        assert result.error is not None


def test_verify_skips_metadata_keys(backend):
    backend.upload("__tags__prod", b"metadata")
    blob = encrypt("KEY=val", PASSPHRASE)
    backend.upload("prod", blob)
    summary = verify_env(backend, PASSPHRASE)
    assert all(not r.key.startswith("__") for r in summary.results)
    assert len(summary.results) == 1


def test_verify_empty_backend(backend):
    summary = verify_env(backend, PASSPHRASE)
    assert summary.results == []
    assert summary.all_ok


# --- CLI tests ---


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_dir(tmp_path):
    backend = LocalBackend(path=str(tmp_path))
    blob = encrypt("SECRET=abc", PASSPHRASE)
    backend.upload("prod", blob)
    return str(tmp_path)


def test_cli_verify_success(runner, env_dir):
    result = runner.invoke(
        verify, ["run", "--env-dir", env_dir, "--passphrase", PASSPHRASE]
    )
    assert result.exit_code == 0
    assert "OK" in result.output
    assert "prod" in result.output


def test_cli_verify_wrong_passphrase_exits_nonzero(runner, env_dir):
    result = runner.invoke(
        verify, ["run", "--env-dir", env_dir, "--passphrase", "bad"]
    )
    assert result.exit_code != 0
    assert "FAIL" in result.output
