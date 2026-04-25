"""Tests for envault.cli_cascade CLI commands."""
from __future__ import annotations

import os

import pytest
from click.testing import CliRunner

from envault.backends.local import LocalBackend
from envault.cli_cascade import cascade
from envault.crypto import decrypt, encrypt

PASS = "cli-cascade-pass"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_dir(tmp_path):
    backend = LocalBackend(root=str(tmp_path))
    backend.upload("base", encrypt("A=1\nB=2", PASS))
    backend.upload("prod", encrypt("B=99\nC=3", PASS))
    return str(tmp_path)


def test_cascade_run_prints_merged(runner, env_dir):
    result = runner.invoke(
        cascade,
        ["run", "base", "prod", "--passphrase", PASS, "--env-dir", env_dir],
    )
    assert result.exit_code == 0
    assert "A=1" in result.output
    assert "B=99" in result.output
    assert "C=3" in result.output


def test_cascade_run_reports_variable_count(runner, env_dir):
    result = runner.invoke(
        cascade,
        ["run", "base", "prod", "--passphrase", PASS, "--env-dir", env_dir],
    )
    assert "3 variable(s)" in result.output


def test_cascade_run_show_overrides(runner, env_dir):
    result = runner.invoke(
        cascade,
        ["run", "base", "prod", "--passphrase", PASS, "--env-dir", env_dir, "--show-overrides"],
    )
    assert result.exit_code == 0
    assert "B: base -> prod" in result.output


def test_cascade_run_no_overrides_message(runner, env_dir):
    result = runner.invoke(
        cascade,
        ["run", "base", "--passphrase", PASS, "--env-dir", env_dir, "--show-overrides"],
    )
    assert result.exit_code == 0
    assert "No overrides" in result.output


def test_cascade_run_stores_out_key(runner, env_dir):
    result = runner.invoke(
        cascade,
        ["run", "base", "prod", "--passphrase", PASS, "--env-dir", env_dir, "--out", "merged"],
    )
    assert result.exit_code == 0
    assert "merged" in result.output
    backend = LocalBackend(root=env_dir)
    assert backend.exists("merged")
    blob = decrypt(backend.download("merged"), PASS)
    assert "A=1" in blob
    assert "B=99" in blob
