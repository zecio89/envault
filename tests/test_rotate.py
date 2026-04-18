"""Tests for envault.rotate."""
import pytest

from envault.backends.local import LocalBackend
from envault.crypto import decrypt, encrypt
from envault.rotate import rotate_key


@pytest.fixture()
def backend(tmp_path):
    return LocalBackend(str(tmp_path))


@pytest.fixture()
def populated_backend(backend):
    old_pass = "old-secret"
    for name, value in [("prod", "A=1\nB=2"), ("staging", "A=3")]:
        backend.upload(name, encrypt(value, old_pass))
    return backend


def test_rotate_returns_all_keys(populated_backend):
    rotated = rotate_key(populated_backend, "old-secret", "new-secret")
    assert set(rotated) == {"prod", "staging"}


def test_rotated_values_decryptable(populated_backend):
    rotate_key(populated_backend, "old-secret", "new-secret")
    for key in ["prod", "staging"]:
        ct = populated_backend.download(key)
        plaintext = decrypt(ct, "new-secret")
        assert plaintext  # non-empty


def test_old_passphrase_no_longer_works(populated_backend):
    rotate_key(populated_backend, "old-secret", "new-secret")
    ct = populated_backend.download("prod")
    with pytest.raises(Exception):
        decrypt(ct, "old-secret")


def test_wrong_old_passphrase_raises(populated_backend):
    with pytest.raises(Exception):
        rotate_key(populated_backend, "wrong-pass", "new-secret")


def test_rotate_with_prefix(backend):
    old_pass = "old"
    backend.upload("prod/app", encrypt("X=1", old_pass))
    backend.upload("dev/app", encrypt("X=2", old_pass))
    rotated = rotate_key(backend, "old", "new", prefix="prod/")
    assert rotated == ["prod/app"]
    # dev/app still decryptable with old passphrase
    ct = backend.download("dev/app")
    assert decrypt(ct, "old") == "X=2"


def test_rotate_empty_backend(backend):
    rotated = rotate_key(backend, "old", "new")
    assert rotated == []
