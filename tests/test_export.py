"""Tests for envault.export and cli_export."""
from __future__ import annotations
import json
import pytest
from click.testing import CliRunner
from envault.export import export_env, _parse_env
from envault.cli_export import export


ENV_CONTENT = "DB_HOST=localhost\nDB_PORT=5432\n# comment\nSECRET=abc123\n"


def test_parse_env_basic():
    pairs = _parse_env(ENV_CONTENT)
    assert pairs == {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc123"}


def test_export_dotenv_passthrough():
    assert export_env(ENV_CONTENT, "dotenv") == ENV_CONTENT


def test_export_json():
    result = export_env(ENV_CONTENT, "json")
    data = json.loads(result)
    assert data["DB_HOST"] == "localhost"
    assert data["SECRET"] == "abc123"
    assert "# comment" not in result


def test_export_shell():
    result = export_env(ENV_CONTENT, "shell")
    assert 'export DB_HOST="localhost"' in result
    assert 'export SECRET="abc123"' in result


def test_export_unknown_format_raises():
    with pytest.raises(ValueError, match="Unknown format"):
        export_env(ENV_CONTENT, "xml")  # type: ignore[arg-type]


@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_export_json(runner, tmp_path):
    from envault.cli import push as push_cmd
    env_file = tmp_path / ".env"
    env_file.write_text(ENV_CONTENT)
    env_dir = str(tmp_path / "store")
    result = runner.invoke(
        push_cmd,
        [str(env_file), "--passphrase", "secret", "--backend", "local", "--env-dir", env_dir],
    )
    assert result.exit_code == 0
    key = result.output.strip().split()[-1]
    result = runner.invoke(
        export,
        [key, "--passphrase", "secret", "--format", "json", "--backend", "local", "--env-dir", env_dir],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["DB_HOST"] == "localhost"


def test_cli_export_to_file(runner, tmp_path):
    from envault.cli import push as push_cmd
    env_file = tmp_path / ".env"
    env_file.write_text(ENV_CONTENT)
    env_dir = str(tmp_path / "store")
    out_file = str(tmp_path / "out.json")
    result = runner.invoke(
        push_cmd,
        [str(env_file), "--passphrase", "pw", "--backend", "local", "--env-dir", env_dir],
    )
    key = result.output.strip().split()[-1]
    result = runner.invoke(
        export,
        [key, "--passphrase", "pw", "--format", "json", "--output", out_file, "--backend", "local", "--env-dir", env_dir],
    )
    assert result.exit_code == 0
    assert "Exported to" in result.output
    with open(out_file) as fh:
        data = json.load(fh)
    assert "DB_PORT" in data
