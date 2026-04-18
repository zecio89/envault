import os
import pytest
from click.testing import CliRunner
from envault.cli_lock import lock
from envault.backends.local import LocalBackend


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_dir(tmp_path):
    d = str(tmp_path / "store")
    os.makedirs(d)
    b = LocalBackend(d)
    b.upload("prod", b"some-encrypted-blob")
    b.upload("staging", b"another-blob")
    return d


def test_lock_success(runner, env_dir):
    result = runner.invoke(lock, ["lock", "prod", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "Locked: prod" in result.output


def test_lock_missing_key(runner, env_dir):
    result = runner.invoke(lock, ["lock", "missing", "--env-dir", env_dir])
    assert result.exit_code != 0
    assert "No such env" in result.output


def test_unlock_success(runner, env_dir):
    runner.invoke(lock, ["lock", "prod", "--env-dir", env_dir])
    result = runner.invoke(lock, ["unlock", "prod", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "Unlocked: prod" in result.output


def test_unlock_not_locked(runner, env_dir):
    result = runner.invoke(lock, ["unlock", "prod", "--env-dir", env_dir])
    assert result.exit_code != 0
    assert "not locked" in result.output


def test_status_locked(runner, env_dir):
    runner.invoke(lock, ["lock", "staging", "--env-dir", env_dir])
    result = runner.invoke(lock, ["status", "staging", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "locked" in result.output


def test_status_unlocked(runner, env_dir):
    result = runner.invoke(lock, ["status", "prod", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "unlocked" in result.output


def test_list_locked_output(runner, env_dir):
    runner.invoke(lock, ["lock", "prod", "--env-dir", env_dir])
    runner.invoke(lock, ["lock", "staging", "--env-dir", env_dir])
    result = runner.invoke(lock, ["list", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "prod" in result.output
    assert "staging" in result.output


def test_list_locked_empty(runner, env_dir):
    result = runner.invoke(lock, ["list", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "No locked envs" in result.output
