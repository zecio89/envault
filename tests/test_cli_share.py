import pytest
from click.testing import CliRunner
from envault.backends.local import LocalBackend
from envault.crypto import encrypt
from envault.cli_share import share


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_dir(tmp_path):
    backend = LocalBackend(str(tmp_path))
    content = "API_KEY=abc123\nSECRET=xyz\n"
    blob = encrypt(content, "old-pass")
    backend.upload("staging", blob.encode())
    return str(tmp_path)


def test_send_creates_share(runner, env_dir):
    result = runner.invoke(
        share, ["send", "staging", "alice",
                "--passphrase", "old-pass",
                "--recipient-passphrase", "recv-pass",
                "--env-dir", env_dir]
    )
    assert result.exit_code == 0
    assert "__shares__/staging/alice" in result.output


def test_receive_decrypts_share(runner, env_dir):
    runner.invoke(
        share, ["send", "staging", "alice",
                "--passphrase", "old-pass",
                "--recipient-passphrase", "recv-pass",
                "--env-dir", env_dir]
    )
    result = runner.invoke(
        share, ["receive", "staging", "alice",
                "--recipient-passphrase", "recv-pass",
                "--env-dir", env_dir]
    )
    assert result.exit_code == 0
    assert "API_KEY=abc123" in result.output


def test_list_shares_shows_entries(runner, env_dir):
    runner.invoke(
        share, ["send", "staging", "alice",
                "--passphrase", "old-pass",
                "--recipient-passphrase", "recv-pass",
                "--env-dir", env_dir]
    )
    result = runner.invoke(share, ["list", "staging", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "alice" in result.output


def test_list_shares_empty(runner, env_dir):
    result = runner.invoke(share, ["list", "staging", "--env-dir", env_dir])
    assert "No shares found" in result.output


def test_send_missing_key_errors(runner, env_dir):
    result = runner.invoke(
        share, ["send", "nonexistent", "alice",
                "--passphrase", "old-pass",
                "--recipient-passphrase", "recv-pass",
                "--env-dir", env_dir]
    )
    assert result.exit_code != 0
    assert "not found" in result.output


def test_delete_share(runner, env_dir):
    runner.invoke(
        share, ["send", "staging", "alice",
                "--passphrase", "old-pass",
                "--recipient-passphrase", "recv-pass",
                "--env-dir", env_dir]
    )
    result = runner.invoke(share, ["delete", "staging", "alice", "--env-dir", env_dir])
    assert result.exit_code == 0
    assert "Deleted" in result.output
