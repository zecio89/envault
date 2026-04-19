"""Tests for envault.cli_watch."""
from __future__ import annotations

import unittest.mock as mock
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_watch import watch


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    d = tmp_path / "store"
    d.mkdir()
    return d


def test_watch_start_invokes_watch_file(runner: CliRunner, env_dir: Path, tmp_path: Path) -> None:
    env_file = tmp_path / "app.env"
    env_file.write_text("FOO=bar\n")

    with mock.patch("envault.cli_watch.watch_file") as mocked:
        result = runner.invoke(
            watch,
            [
                "start",
                str(env_file),
                "--passphrase", "secret",
                "--backend", "local",
                "--backend-path", str(env_dir),
                "--interval", "0.5",
            ],
        )

    assert result.exit_code == 0, result.output
    assert mocked.called
    _, kwargs = mocked.call_args
    assert kwargs["interval"] == 0.5


def test_watch_start_missing_file(runner: CliRunner, env_dir: Path, tmp_path: Path) -> None:
    result = runner.invoke(
        watch,
        [
            "start",
            str(tmp_path / "missing.env"),
            "--passphrase", "secret",
            "--backend", "local",
            "--backend-path", str(env_dir),
        ],
    )
    assert result.exit_code != 0
