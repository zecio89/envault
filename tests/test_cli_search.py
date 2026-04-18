"""Tests for envault CLI search command."""
import pytest
from click.testing import CliRunner
from envault.cli_search import search
from envault.backends.local import LocalBackend
from envault.crypto import encrypt

PASS = "hunter2"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_dir(tmp_path):
    b = LocalBackend(root=str(tmp_path))
    b.upload("staging/app", encrypt("DB_HOST=localhost\nAPI_KEY=secret", PASS).encode())
    b.upload("prod/app", encrypt("DB_HOST=prod.db\nAPI_KEY=live", PASS).encode())
    return tmp_path


def test_search_key_match(runner, env_dir):
    result = runner.invoke(search, ["run", "staging", "--env-dir", str(env_dir)])
    assert result.exit_code == 0
    assert "staging/app" in result.output


def test_search_no_match(runner, env_dir):
    result = runner.invoke(search, ["run", "zzznope", "--env-dir", str(env_dir)])
    assert result.exit_code == 0
    assert "No matches found" in result.output


def test_search_values_without_passphrase_errors(runner, env_dir):
    result = runner.invoke(search, ["run", "localhost", "--env-dir", str(env_dir), "--values"])
    assert result.exit_code != 0
    assert "passphrase" in result.output.lower()


def test_search_values_with_passphrase(runner, env_dir):
    result = runner.invoke(search, [
        "run", "localhost",
        "--env-dir", str(env_dir),
        "--values",
        "--passphrase", PASS,
    ])
    assert result.exit_code == 0
    assert "staging/app" in result.output
