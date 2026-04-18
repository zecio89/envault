import pytest
from click.testing import CliRunner
from envault.cli_alias import alias
from envault.backends.local import LocalBackend


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_dir(tmp_path):
    b = LocalBackend(str(tmp_path))
    b.upload("production", b"blob")
    b.upload("staging", b"blob2")
    return str(tmp_path)


def test_set_alias_success(runner, env_dir):
    result = runner.invoke(alias, ["set", "prod", "production", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "prod" in result.output
    assert "production" in result.output


def test_set_alias_missing_key(runner, env_dir):
    result = runner.invoke(alias, ["set", "ghost", "nonexistent", "--env-dir", env_dir])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_get_alias(runner, env_dir):
    runner.invoke(alias, ["set", "prod", "production", "--env-dir", env_dir])
    result = runner.invoke(alias, ["get", "prod", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "production" in result.output


def test_get_alias_missing(runner, env_dir):
    result = runner.invoke(alias, ["get", "nope", "--env-dir", env_dir])
    assert result.exit_code == 1


def test_rm_alias(runner, env_dir):
    runner.invoke(alias, ["set", "prod", "production", "--env-dir", env_dir])
    result = runner.invoke(alias, ["rm", "prod", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_list_aliases(runner, env_dir):
    runner.invoke(alias, ["set", "prod", "production", "--env-dir", env_dir])
    runner.invoke(alias, ["set", "stg", "staging", "--env-dir", env_dir])
    result = runner.invoke(alias, ["list", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "prod -> production" in result.output
    assert "stg -> staging" in result.output


def test_list_aliases_empty(runner, tmp_path):
    result = runner.invoke(alias, ["list", "--env-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "No aliases" in result.output
