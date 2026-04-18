"""Tests for envault.diff."""
import pytest

from envault.backends.local import LocalBackend
from envault.vault import Vault
from envault.diff import diff_envs, _parse_env


PASS = "secret"


@pytest.fixture()
def vault(tmp_path):
    backend = LocalBackend(str(tmp_path))
    return Vault(backend=backend, passphrase=PASS)


# --- unit: _parse_env ---

def test_parse_env_basic():
    text = "FOO=bar\nBAZ=qux\n"
    assert _parse_env(text) == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_ignores_comments_and_blanks():
    text = "# comment\n\nKEY=val\n"
    assert _parse_env(text) == {"KEY": "val"}


def test_parse_env_empty():
    assert _parse_env("") == {}


# --- integration: diff_envs ---

def test_diff_no_changes(vault):
    content = "A=1\nB=2\n"
    k1 = vault.push(content, key="snap/v1")
    k2 = vault.push(content, key="snap/v2")
    assert diff_envs(vault, k1, k2, PASS) == []


def test_diff_changed_value(vault):
    k1 = vault.push("A=old\nB=same\n", key="snap/v1")
    k2 = vault.push("A=new\nB=same\n", key="snap/v2")
    changes = diff_envs(vault, k1, k2, PASS)
    assert len(changes) == 1
    assert changes[0] == ("A", "old", "new")


def test_diff_added_key(vault):
    k1 = vault.push("A=1\n", key="snap/v1")
    k2 = vault.push("A=1\nB=2\n", key="snap/v2")
    changes = diff_envs(vault, k1, k2, PASS)
    assert changes == [("B", None, "2")]


def test_diff_removed_key(vault):
    k1 = vault.push("A=1\nB=2\n", key="snap/v1")
    k2 = vault.push("A=1\n", key="snap/v2")
    changes = diff_envs(vault, k1, k2, PASS)
    assert changes == [("B", "2", None)]


def test_diff_multiple_changes(vault):
    k1 = vault.push("A=1\nB=2\nC=3\n", key="snap/v1")
    k2 = vault.push("A=1\nB=99\nD=4\n", key="snap/v2")
    changes = diff_envs(vault, k1, k2, PASS)
    keys = [c[0] for c in changes]
    assert "B" in keys
    assert "C" in keys
    assert "D" in keys
    assert "A" not in keys
