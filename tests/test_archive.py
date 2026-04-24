"""Tests for envault.archive."""

import pytest

from envault.archive import (
    create_archive,
    delete_archive,
    list_archives,
    restore_archive,
)
from envault.backends.local import LocalBackend
from envault.crypto import decrypt, encrypt


@pytest.fixture()
def backend(tmp_path):
    return LocalBackend(root=str(tmp_path / "vault"))


@pytest.fixture()
def populated_backend(backend):
    passphrase = "secret"
    for key in ("prod", "staging", "dev"):
        blob = encrypt(f"APP_ENV={key}\nDEBUG=false", passphrase)
        backend.upload(key, blob)
    return backend, passphrase


def test_create_archive_returns_metadata(populated_backend):
    backend, passphrase = populated_backend
    meta = create_archive(backend, passphrase)
    assert "name" in meta
    assert "created_at" in meta
    assert set(meta["keys"]) == {"prod", "staging", "dev"}


def test_create_archive_stored_in_backend(populated_backend):
    backend, passphrase = populated_backend
    meta = create_archive(backend, passphrase)
    archive_key = f"__archives__/{meta['name']}.tar.gz"
    assert backend.exists(archive_key)


def test_create_archive_custom_name(populated_backend):
    backend, passphrase = populated_backend
    meta = create_archive(backend, passphrase, name="my-archive")
    assert meta["name"] == "my-archive"
    assert backend.exists("__archives__/my-archive.tar.gz")


def test_create_archive_with_prefix(populated_backend):
    backend, passphrase = populated_backend
    meta = create_archive(backend, passphrase, prefix="prod")
    assert meta["keys"] == ["prod"]


def test_create_archive_wrong_passphrase_raises(populated_backend):
    backend, _ = populated_backend
    with pytest.raises(Exception):
        create_archive(backend, "wrong-passphrase")


def test_create_archive_no_keys_raises(backend):
    with pytest.raises(ValueError, match="No env keys found"):
        create_archive(backend, "secret")


def test_list_archives_empty(backend):
    assert list_archives(backend) == []


def test_list_archives_returns_all(populated_backend):
    backend, passphrase = populated_backend
    create_archive(backend, passphrase, name="arch-1")
    create_archive(backend, passphrase, name="arch-2")
    archives = list_archives(backend)
    names = [a["name"] for a in archives]
    assert "arch-1" in names
    assert "arch-2" in names


def test_restore_archive_roundtrip(populated_backend, tmp_path):
    backend, passphrase = populated_backend
    meta = create_archive(backend, passphrase, name="backup")

    # New empty backend
    dest = LocalBackend(root=str(tmp_path / "restore"))
    # Copy archive marker into dest
    raw = backend.download(f"__archives__/backup.tar.gz")
    dest.upload("__archives__/backup.tar.gz", raw)

    restored = restore_archive(dest, "backup")
    assert set(restored) == {"prod", "staging", "dev"}
    for key in restored:
        blob = dest.download(key)
        plaintext = decrypt(blob, passphrase)
        assert "APP_ENV" in plaintext


def test_restore_archive_no_overwrite(populated_backend):
    backend, passphrase = populated_backend
    create_archive(backend, passphrase, name="snap")
    # All keys already exist — nothing should be restored without --overwrite
    restored = restore_archive(backend, "snap", overwrite=False)
    assert restored == []


def test_restore_archive_with_overwrite(populated_backend):
    backend, passphrase = populated_backend
    create_archive(backend, passphrase, name="snap")
    restored = restore_archive(backend, "snap", overwrite=True)
    assert set(restored) == {"prod", "staging", "dev"}


def test_delete_archive(populated_backend):
    backend, passphrase = populated_backend
    meta = create_archive(backend, passphrase, name="to-delete")
    delete_archive(backend, "to-delete")
    assert not backend.exists(f"__archives__/to-delete.tar.gz")


def test_delete_archive_missing_raises(backend):
    with pytest.raises(KeyError, match="not found"):
        delete_archive(backend, "ghost")
