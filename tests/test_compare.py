import pytest
from envault.backends.local import LocalBackend
from envault.crypto import encrypt
from envault.compare import compare_envs, CompareResult


@pytest.fixture
def backend(tmp_path):
    return LocalBackend(env_dir=str(tmp_path))


def _store(backend, key, content: str, passphrase: str):
    blob = encrypt(content.encode(), passphrase)
    backend.upload(key, blob)


def test_compare_identical(backend):
    content = "A=1\nB=2\n"
    _store(backend, "env/a", content, "pass")
    _store(backend, "env/b", content, "pass")
    r = compare_envs(backend, "env/a", "env/b", "pass")
    assert r.same == ["A", "B"]
    assert r.different == []
    assert r.only_in_a == []
    assert r.only_in_b == []


def test_compare_different_values(backend):
    _store(backend, "env/a", "A=1\nB=2\n", "pass")
    _store(backend, "env/b", "A=1\nB=99\n", "pass")
    r = compare_envs(backend, "env/a", "env/b", "pass")
    assert "B" in r.different
    assert "A" in r.same


def test_compare_only_in_a(backend):
    _store(backend, "env/a", "A=1\nX=2\n", "pass")
    _store(backend, "env/b", "A=1\n", "pass")
    r = compare_envs(backend, "env/a", "env/b", "pass")
    assert "X" in r.only_in_a
    assert r.only_in_b == []


def test_compare_only_in_b(backend):
    _store(backend, "env/a", "A=1\n", "pass")
    _store(backend, "env/b", "A=1\nY=3\n", "pass")
    r = compare_envs(backend, "env/a", "env/b", "pass")
    assert "Y" in r.only_in_b
    assert r.only_in_a == []


def test_compare_different_passphrases(backend):
    _store(backend, "env/a", "A=1\n", "passA")
    _store(backend, "env/b", "A=1\n", "passB")
    r = compare_envs(backend, "env/a", "env/b", "passA", passphrase_b="passB")
    assert "A" in r.same


def test_compare_missing_key_raises(backend):
    _store(backend, "env/a", "A=1\n", "pass")
    with pytest.raises(KeyError, match="env/missing"):
        compare_envs(backend, "env/a", "env/missing", "pass")


def test_compare_ignores_comments(backend):
    _store(backend, "env/a", "# comment\nA=1\n", "pass")
    _store(backend, "env/b", "A=1\n", "pass")
    r = compare_envs(backend, "env/a", "env/b", "pass")
    assert r.same == ["A"]
    assert r.only_in_a == []
