"""Tests for the envault CLI commands."""
import pytest
from pathlib import Path
from click.testing import CliRunner

from envault.cli import cli


PASSPHRASE = "test-passphrase"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_content():
    return "DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc123\n"


def test_push_and_pull_roundtrip(runner, tmp_path, env_content):
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)
    storage = str(tmp_path / "vault")

    result = runner.invoke(cli, [
        "push", str(env_file),
        "--backend", "local",
        "--storage", storage,
        "--passphrase", PASSPHRASE,
    ])
    assert result.exit_code == 0, result.output
    assert "Pushed to key:" in result.output

    out_file = tmp_path / "pulled.env"
    result = runner.invoke(cli, [
        "pull", ".env",
        "--output", str(out_file),
        "--backend", "local",
        "--storage", storage,
        "--passphrase", PASSPHRASE,
    ])
    assert result.exit_code == 0, result.output
    assert out_file.read_text() == env_content


def test_list_shows_keys(runner, tmp_path, env_content):
    env_file = tmp_path / "prod.env"
    env_file.write_text(env_content)
    storage = str(tmp_path / "vault")

    runner.invoke(cli, [
        "push", str(env_file),
        "--backend", "local",
        "--storage", storage,
        "--passphrase", PASSPHRASE,
    ])

    result = runner.invoke(cli, [
        "list",
        "--backend", "local",
        "--storage", storage,
        "--passphrase", PASSPHRASE,
    ])
    assert result.exit_code == 0
    assert "prod.env" in result.output


def test_list_empty(runner, tmp_path):
    storage = str(tmp_path / "vault")
    result = runner.invoke(cli, [
        "list",
        "--backend", "local",
        "--storage", storage,
        "--passphrase", PASSPHRASE,
    ])
    assert result.exit_code == 0
    assert "No environments stored." in result.output


def test_delete_removes_key(runner, tmp_path, env_content):
    env_file = tmp_path / "staging.env"
    env_file.write_text(env_content)
    storage = str(tmp_path / "vault")

    runner.invoke(cli, [
        "push", str(env_file),
        "--backend", "local",
        "--storage", storage,
        "--passphrase", PASSPHRASE,
    ])

    result = runner.invoke(cli, [
        "delete", "staging.env",
        "--backend", "local",
        "--storage", storage,
        "--passphrase", PASSPHRASE,
    ])
    assert result.exit_code == 0
    assert "Deleted 'staging.env'" in result.output
