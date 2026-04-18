"""Integration tests for the `envault rotate` CLI sub-command."""
import pytest
from click.testing import CliRunner

from envault.cli import cli
from envault.crypto import encrypt
import envault.cli_rotate  # noqa: F401 – registers the rotate command


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_dir(tmp_path):
    return str(tmp_path)


def _seed(env_dir, passphrase="old"):
    from envault.backends.local import LocalBackend
    b = LocalBackend(env_dir)
    b.upload("prod", encrypt("K=1", passphrase))
    b.upload("staging", encrypt("K=2", passphrase))


def test_rotate_success(runner, env_dir):
    _seed(env_dir)
    result = runner.invoke(
        cli,
        ["rotate", "--old-passphrase", "old", "--new-passphrase", "new",
         "--path", env_dir],
    )
    assert result.exit_code == 0, result.output
    assert "Rotated 2 key(s)" in result.output


def test_rotate_wrong_old_passphrase(runner, env_dir):
    _seed(env_dir)
    result = runner.invoke(
        cli,
        ["rotate", "--old-passphrase", "wrong", "--new-passphrase", "new",
         "--path", env_dir],
    )
    assert result.exit_code != 0
    assert "Rotation failed" in result.output


def test_rotate_empty_store(runner, env_dir):
    result = runner.invoke(
        cli,
        ["rotate", "--old-passphrase", "old", "--new-passphrase", "new",
         "--path", env_dir],
    )
    assert result.exit_code == 0
    assert "Nothing to rotate" in result.output


def test_rotate_with_prefix(runner, env_dir):
    _seed(env_dir)
    result = runner.invoke(
        cli,
        ["rotate", "--old-passphrase", "old", "--new-passphrase", "new",
         "--prefix", "prod", "--path", env_dir],
    )
    assert result.exit_code == 0
    assert "Rotated 1 key(s)" in result.output
    assert "prod" in result.output
