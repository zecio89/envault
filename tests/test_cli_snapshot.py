import pytest
from click.testing import CliRunner
from envault.backends.local import LocalBackend
from envault.crypto import encrypt
from envault.cli_snapshot import snapshot


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_dir(tmp_path):
    backend = LocalBackend(str(tmp_path))
    pp = "testpass"
    backend.upload("prod", encrypt("KEY=hello", pp).encode())
    backend.upload("staging", encrypt("KEY=world", pp).encode())
    return tmp_path


def test_create_snapshot_success(runner, env_dir):
    result = runner.invoke(snapshot, ["create", "--dir", str(env_dir), "--passphrase", "testpass", "--name", "mysnap"])
    assert result.exit_code == 0
    assert "mysnap" in result.output
    assert "2 keys" in result.output


def test_list_snapshots(runner, env_dir):
    runner.invoke(snapshot, ["create", "--dir", str(env_dir), "--passphrase", "testpass", "--name", "snap1"])
    result = runner.invoke(snapshot, ["list", "--dir", str(env_dir), "--passphrase", "testpass"])
    assert result.exit_code == 0
    assert "snap1" in result.output


def test_list_snapshots_empty(runner, tmp_path):
    result = runner.invoke(snapshot, ["list", "--dir", str(tmp_path), "--passphrase", "testpass"])
    assert result.exit_code == 0
    assert "No snapshots" in result.output


def test_restore_snapshot(runner, env_dir):
    runner.invoke(snapshot, ["create", "--dir", str(env_dir), "--passphrase", "testpass", "--name", "snap1"])
    result = runner.invoke(snapshot, ["restore", "snap1", "--dir", str(env_dir), "--passphrase", "testpass"])
    assert result.exit_code == 0
    assert "Restored" in result.output


def test_delete_snapshot(runner, env_dir):
    runner.invoke(snapshot, ["create", "--dir", str(env_dir), "--passphrase", "testpass", "--name", "snap1"])
    result = runner.invoke(snapshot, ["delete", "snap1", "--dir", str(env_dir), "--passphrase", "testpass"])
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_delete_missing_snapshot(runner, tmp_path):
    result = runner.invoke(snapshot, ["delete", "ghost", "--dir", str(tmp_path), "--passphrase", "testpass"])
    assert result.exit_code != 0
    assert "ghost" in result.output
