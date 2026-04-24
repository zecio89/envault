"""Tests for envault.cli_webhook."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_webhook import webhook
from envault.backends.local import LocalBackend
from envault.webhook import register_webhook


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_dir(tmp_path):
    return str(tmp_path)


def test_register_success(runner, env_dir):
    result = runner.invoke(
        webhook,
        ["register", "slack", "https://hooks.example.com/abc",
         "--event", "push", "--event", "rotate",
         "--env-dir", env_dir],
    )
    assert result.exit_code == 0
    assert "slack" in result.output
    assert "https://hooks.example.com/abc" in result.output


def test_get_webhook(runner, env_dir):
    backend = LocalBackend(root=env_dir)
    register_webhook(backend, "ci", "https://ci.example.com", ["push"])

    result = runner.invoke(webhook, ["get", "ci", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "https://ci.example.com" in result.output
    assert "push" in result.output


def test_get_missing_webhook_exits_nonzero(runner, env_dir):
    result = runner.invoke(webhook, ["get", "ghost", "--env-dir", env_dir])
    assert result.exit_code != 0
    assert "No webhook" in result.output


def test_rm_webhook(runner, env_dir):
    backend = LocalBackend(root=env_dir)
    register_webhook(backend, "slack", "https://hooks.example.com/abc", ["push"])

    result = runner.invoke(webhook, ["rm", "slack", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_rm_missing_webhook_exits_nonzero(runner, env_dir):
    result = runner.invoke(webhook, ["rm", "ghost", "--env-dir", env_dir])
    assert result.exit_code != 0


def test_list_empty(runner, env_dir):
    result = runner.invoke(webhook, ["list", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "No webhooks" in result.output


def test_list_shows_all(runner, env_dir):
    backend = LocalBackend(root=env_dir)
    register_webhook(backend, "slack", "https://slack.example.com", ["push"])
    register_webhook(backend, "pagerduty", "https://pd.example.com", ["rotate"])

    result = runner.invoke(webhook, ["list", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "slack" in result.output
    assert "pagerduty" in result.output
