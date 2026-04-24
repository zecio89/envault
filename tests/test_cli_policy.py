"""CLI tests for envault policy commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_policy import policy


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_dir(tmp_path):
    from envault.backends.local import LocalBackend

    b = LocalBackend(root=str(tmp_path))
    b.upload("staging", b"blob")
    b.upload("production", b"blob2")
    return str(tmp_path)


def test_set_and_get_policy(runner, env_dir):
    result = runner.invoke(
        policy,
        ["set", "staging", "--user", "alice", "--read-only", "--dir", env_dir],
    )
    assert result.exit_code == 0, result.output
    assert "Policy set" in result.output

    result = runner.invoke(policy, ["get", "staging", "--dir", env_dir])
    assert result.exit_code == 0
    assert "alice" in result.output
    assert "read_only" in result.output


def test_get_no_policy(runner, env_dir):
    result = runner.invoke(policy, ["get", "staging", "--dir", env_dir])
    assert result.exit_code == 0
    assert "No policy set" in result.output


def test_set_missing_key_errors(runner, env_dir):
    result = runner.invoke(policy, ["set", "ghost", "--user", "alice", "--dir", env_dir])
    assert result.exit_code != 0
    assert "ghost" in result.output


def test_rm_policy(runner, env_dir):
    runner.invoke(policy, ["set", "staging", "--user", "alice", "--dir", env_dir])
    result = runner.invoke(policy, ["rm", "staging", "--dir", env_dir])
    assert result.exit_code == 0
    assert "removed" in result.output

    result = runner.invoke(policy, ["get", "staging", "--dir", env_dir])
    assert "No policy set" in result.output


def test_list_policies(runner, env_dir):
    result = runner.invoke(policy, ["list", "--dir", env_dir])
    assert "No policies" in result.output

    runner.invoke(policy, ["set", "staging", "--dir", env_dir])
    runner.invoke(policy, ["set", "production", "--dir", env_dir])
    result = runner.invoke(policy, ["list", "--dir", env_dir])
    assert "staging" in result.output
    assert "production" in result.output


def test_check_allowed(runner, env_dir):
    runner.invoke(policy, ["set", "staging", "--user", "alice", "--dir", env_dir])
    result = runner.invoke(policy, ["check", "staging", "alice", "--dir", env_dir])
    assert "ALLOWED" in result.output


def test_check_denied(runner, env_dir):
    runner.invoke(policy, ["set", "staging", "--user", "alice", "--dir", env_dir])
    result = runner.invoke(policy, ["check", "staging", "eve", "--dir", env_dir])
    assert "DENIED" in result.output
