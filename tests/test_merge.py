"""Tests for envault.merge."""
import pytest

from envault.crypto import decrypt, encrypt
from envault.merge import MergeResult, merge_envs

PASS_A = "passphrase-a"
PASS_B = "passphrase-b"
PASS_OUT = "passphrase-out"


def _make_blob(content: str, passphrase: str) -> str:
    return encrypt(content, passphrase)


@pytest.fixture
def base_blob():
    return _make_blob("FOO=bar\nSHARED=base_val\nONLY_BASE=yes\n", PASS_A)


@pytest.fixture
def other_blob():
    return _make_blob("FOO=baz\nSHARED=base_val\nONLY_OTHER=yes\n", PASS_B)


def test_merge_returns_merge_result(base_blob, other_blob):
    result = merge_envs(base_blob, other_blob, PASS_A, PASS_B, PASS_OUT)
    assert isinstance(result, MergeResult)


def test_merge_added_keys(base_blob, other_blob):
    result = merge_envs(base_blob, other_blob, PASS_A, PASS_B, PASS_OUT)
    assert "ONLY_OTHER" in result.added


def test_merge_removed_keys(base_blob, other_blob):
    result = merge_envs(base_blob, other_blob, PASS_A, PASS_B, PASS_OUT)
    assert "ONLY_BASE" in result.removed


def test_merge_conflict_detected(base_blob, other_blob):
    result = merge_envs(base_blob, other_blob, PASS_A, PASS_B, PASS_OUT)
    assert "FOO" in result.conflicts
    assert result.conflicts["FOO"] == ("bar", "baz")


def test_merge_strategy_ours(base_blob, other_blob):
    result = merge_envs(base_blob, other_blob, PASS_A, PASS_B, PASS_OUT, strategy="ours")
    assert result.merged["FOO"] == "bar"


def test_merge_strategy_theirs(base_blob, other_blob):
    result = merge_envs(base_blob, other_blob, PASS_A, PASS_B, PASS_OUT, strategy="theirs")
    assert result.merged["FOO"] == "baz"


def test_merge_no_conflict_for_equal_values(base_blob, other_blob):
    result = merge_envs(base_blob, other_blob, PASS_A, PASS_B, PASS_OUT)
    assert "SHARED" not in result.conflicts
    assert result.merged["SHARED"] == "base_val"


def test_merge_output_blob_decryptable(base_blob, other_blob):
    result = merge_envs(base_blob, other_blob, PASS_A, PASS_B, PASS_OUT)
    blob = result.merged["__blob__"]
    plaintext = decrypt(blob, PASS_OUT)
    assert "SHARED=base_val" in plaintext


def test_merge_invalid_strategy(base_blob, other_blob):
    with pytest.raises(ValueError, match="Unknown strategy"):
        merge_envs(base_blob, other_blob, PASS_A, PASS_B, PASS_OUT, strategy="bad")
