"""Tests for envault.import_env."""
import pytest

from envault.backends.local import LocalBackend
from envault.crypto import decrypt, encrypt
from envault.import_env import import_env

OLD_PASS = "old-secret"
NEW_PASS = "new-secret"
PLAINTEXT = b"DB_URL=postgres://localhost/db\nAPI_KEY=abc123\n"


@pytest.fixture()
def source_backend(tmp_path):
    backend = LocalBackend(tmp_path / "source")
    backend.upload("prod", encrypt(PLAINTEXT, OLD_PASS))
    backend.upload("staging", encrypt(b"STAGE=1\n", OLD_PASS))
    return backend


@pytest.fixture()
def dest_backend(tmp_path):
    return LocalBackend(tmp_path / "dest")


def test_import_all_keys(source_backend, dest_backend):
    imported = import_env(source_backend, dest_backend, OLD_PASS, NEW_PASS)
    assert set(imported) == {"prod", "staging"}
    assert set(dest_backend.list_keys()) == {"prod", "staging"}


def test_imported_values_decryptable(source_backend, dest_backend):
    import_env(source_backend, dest_backend, OLD_PASS, NEW_PASS)
    result = decrypt(dest_backend.download("prod"), NEW_PASS)
    assert result == PLAINTEXT


def test_import_subset_of_keys(source_backend, dest_backend):
    imported = import_env(source_backend, dest_backend, OLD_PASS, NEW_PASS, keys=["prod"])
    assert imported == ["prod"]
    assert not dest_backend.exists("staging")


def test_skip_existing_without_overwrite(source_backend, dest_backend):
    sentinel = encrypt(b"ORIGINAL=1\n", NEW_PASS)
    dest_backend.upload("prod", sentinel)

    import_env(source_backend, dest_backend, OLD_PASS, NEW_PASS, overwrite=False)

    # original must be untouched
    assert decrypt(dest_backend.download("prod"), NEW_PASS) == b"ORIGINAL=1\n"


def test_overwrite_replaces_existing(source_backend, dest_backend):
    dest_backend.upload("prod", encrypt(b"ORIGINAL=1\n", NEW_PASS))

    import_env(source_backend, dest_backend, OLD_PASS, NEW_PASS, overwrite=True)

    assert decrypt(dest_backend.download("prod"), NEW_PASS) == PLAINTEXT


def test_wrong_old_passphrase_raises(source_backend, dest_backend):
    from envault.crypto import DecryptionError

    with pytest.raises(DecryptionError):
        import_env(source_backend, dest_backend, "wrong", NEW_PASS)
