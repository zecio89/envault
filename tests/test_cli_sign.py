"""Tests for envault.cli_sign."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.backends.local import LocalBackend
from envault.cli_sign import sign

SECRET = "cli-test-secret"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_dir(tmp_path):
    b = LocalBackend(root=str(tmp_path))
    b.upload("production", b"SOME_ENCRYPTED_DATA")
    b.upload("staging", b"OTHER_ENCRYPTED_DATA")
    return str(tmp_path)


def test_sign_success(runner, env_dir):
    result = runner.invoke(
        sign, ["sign", "production", "--secret", SECRET, "--env-dir", env_dir]
    )
    assert result.exit_code == 0
    assert "Signed" in result.output
    assert "production" in result.output


def test_sign_missing_key_errors(runner, env_dir):
    result = runner.invoke(
        sign, ["sign", "missing", "--secret", SECRET, "--env-dir", env_dir]
    )
    assert result.exit_code != 0
    assert "missing" in result.output.lower() or "Error" in result.output


def test_verify_valid_signature(runner, env_dir):
    runner.invoke(sign, ["sign", "production", "--secret", SECRET, "--env-dir", env_dir])
    result = runner.invoke(
        sign, ["verify", "production", "--secret", SECRET, "--env-dir", env_dir]
    )
    assert result.exit_code == 0
    assert "OK" in result.output


def test_verify_wrong_secret_exits_nonzero(runner, env_dir):
    runner.invoke(sign, ["sign", "production", "--secret", SECRET, "--env-dir", env_dir])
    result = runner.invoke(
        sign, ["verify", "production", "--secret", "bad-secret", "--env-dir", env_dir]
    )
    assert result.exit_code != 0
    assert "FAIL" in result.output


def test_show_signature(runner, env_dir):
    runner.invoke(sign, ["sign", "production", "--secret", SECRET, "--env-dir", env_dir])
    result = runner.invoke(sign, ["show", "production", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "hmac-sha256" in result.output
    assert "production" in result.output


def test_show_no_signature(runner, env_dir):
    result = runner.invoke(sign, ["show", "staging", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "No signature" in result.output


def test_rm_signature(runner, env_dir):
    runner.invoke(sign, ["sign", "production", "--secret", SECRET, "--env-dir", env_dir])
    result = runner.invoke(sign, ["rm", "production", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_list_signed_keys(runner, env_dir):
    runner.invoke(sign, ["sign", "production", "--secret", SECRET, "--env-dir", env_dir])
    runner.invoke(sign, ["sign", "staging", "--secret", SECRET, "--env-dir", env_dir])
    result = runner.invoke(sign, ["list", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "production" in result.output
    assert "staging" in result.output


def test_list_empty(runner, env_dir):
    result = runner.invoke(sign, ["list", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "No signed" in result.output
