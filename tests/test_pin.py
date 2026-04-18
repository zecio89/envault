"""Tests for envault.pin and envault.cli_pin."""
import pytest
from click.testing import CliRunner
from envault.backends.local import LocalBackend
from envault import pin as pin_mod
from envault.cli_pin import pin


@pytest.fixture()
def backend(tmp_path):
    b = LocalBackend(str(tmp_path))
    b.upload("prod", b"encrypted-blob")
    return b


def test_pin_version_returns_record(backend):
    rec = pin_mod.pin_version(backend, "prod", "v1", "stable")
    assert rec["env_key"] == "prod"
    assert rec["version_id"] == "v1"
    assert rec["label"] == "stable"


def test_get_pin_returns_record(backend):
    pin_mod.pin_version(backend, "prod", "v2")
    rec = pin_mod.get_pin(backend, "prod")
    assert rec["version_id"] == "v2"


def test_get_pin_none_when_unset(backend):
    assert pin_mod.get_pin(backend, "prod") is None


def test_pin_missing_key_raises(backend):
    with pytest.raises(KeyError):
        pin_mod.pin_version(backend, "missing", "v1")


def test_delete_pin_returns_true(backend):
    pin_mod.pin_version(backend, "prod", "v1")
    assert pin_mod.delete_pin(backend, "prod") is True
    assert pin_mod.get_pin(backend, "prod") is None


def test_delete_pin_returns_false_when_none(backend):
    assert pin_mod.delete_pin(backend, "prod") is False


def test_list_pins(backend):
    backend.upload("staging", b"blob2")
    pin_mod.pin_version(backend, "prod", "v1")
    pin_mod.pin_version(backend, "staging", "v3", "rc")
    pins = pin_mod.list_pins(backend)
    keys = {p["env_key"] for p in pins}
    assert keys == {"prod", "staging"}


# CLI tests

@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_dir(tmp_path):
    b = LocalBackend(str(tmp_path))
    b.upload("prod", b"blob")
    return str(tmp_path)


def test_cli_set_and_get(runner, env_dir):
    result = runner.invoke(pin, ["set", "prod", "abc123", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "abc123" in result.output
    result = runner.invoke(pin, ["get", "prod", "--env-dir", env_dir])
    assert "abc123" in result.output


def test_cli_list_empty(runner, env_dir):
    result = runner.invoke(pin, ["list", "--env-dir", env_dir])
    assert "No pins" in result.output


def test_cli_rm(runner, env_dir):
    runner.invoke(pin, ["set", "prod", "v1", "--env-dir", env_dir])
    result = runner.invoke(pin, ["rm", "prod", "--env-dir", env_dir])
    assert "removed" in result.output
