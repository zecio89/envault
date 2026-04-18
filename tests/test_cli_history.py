"""Tests for the history CLI commands."""
import pytest
from pathlib import Path
from click.testing import CliRunner
from envault.cli_history import history
from envault.backends.local import LocalBackend
from envault.history import record_version
from envault.crypto import encrypt


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_dir(tmp_path: Path) -> str:
    return str(tmp_path)


def _seed(env_dir: str, key: str, passphrase: str, content: str, versions: int = 2):
    backend = LocalBackend(env_dir)
    for i in range(1, versions + 1):
        blob = encrypt(f"{content}_v{i}", passphrase)
        backend.upload(key, blob)
        record_version(backend, key, blob, actor="tester", note=f"version {i}")


def test_log_shows_versions(runner, env_dir):
    _seed(env_dir, "prod", "secret", "DATA", versions=3)
    result = runner.invoke(
        history, ["log", "prod", "--env-dir", env_dir]
    )
    assert result.exit_code == 0
    assert "v1" in result.output
    assert "v2" in result.output
    assert "v3" in result.output


def test_log_empty(runner, env_dir):
    result = runner.invoke(
        history, ["log", "nokey", "--env-dir", env_dir]
    )
    assert result.exit_code == 0
    assert "No history" in result.output


def test_restore_prints_plaintext(runner, env_dir):
    _seed(env_dir, "staging", "mypass", "CONTENT", versions=2)
    result = runner.invoke(
        history,
        ["restore", "staging", "1", "--passphrase", "mypass", "--env-dir", env_dir],
    )
    assert result.exit_code == 0
    assert "CONTENT_v1" in result.output


def test_restore_wrong_version(runner, env_dir):
    _seed(env_dir, "dev", "pw", "X", versions=1)
    result = runner.invoke(
        history,
        ["restore", "dev", "99", "--passphrase", "pw", "--env-dir", env_dir],
    )
    assert result.exit_code != 0
    assert "Version 99" in result.output


def test_restore_wrong_passphrase(runner, env_dir):
    _seed(env_dir, "prod", "correct", "SECRET", versions=1)
    result = runner.invoke(
        history,
        ["restore", "prod", "1", "--passphrase", "wrong", "--env-dir", env_dir],
    )
    assert result.exit_code != 0
    assert "Decryption failed" in result.output
