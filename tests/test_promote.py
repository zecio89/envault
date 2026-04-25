"""Tests for envault.promote."""

from __future__ import annotations

import pytest

from envault.backends.local import LocalBackend
from envault.crypto import decrypt, encrypt
from envault.promote import PromoteResult, promote_env

PASS_A = "passphrase-staging"
PASS_B = "passphrase-production"
PLAINTEXT = "DB_URL=postgres://localhost/mydb\nSECRET=abc123\n"


@pytest.fixture()
def backend(tmp_path):
    b = LocalBackend(str(tmp_path))
    blob = encrypt(PLAINTEXT, PASS_A).encode()
    b.upload("staging/app", blob)
    return b


def test_promote_returns_result(backend):
    result = promote_env(backend, "staging/app", "production/app", PASS_A)
    assert isinstance(result, PromoteResult)
    assert result.source_key == "staging/app"
    assert result.dest_key == "production/app"


def test_promote_dest_exists_in_backend(backend):
    promote_env(backend, "staging/app", "production/app", PASS_A)
    assert backend.exists("production/app")


def test_promote_same_passphrase_not_reencrypted(backend):
    result = promote_env(backend, "staging/app", "production/app", PASS_A)
    assert result.re_encrypted is False
    # Original passphrase still decrypts the promoted blob
    blob = backend.download("production/app")
    assert decrypt(blob.decode(), PASS_A) == PLAINTEXT


def test_promote_reencrypt_with_new_passphrase(backend):
    result = promote_env(
        backend, "staging/app", "production/app", PASS_A, dest_passphrase=PASS_B
    )
    assert result.re_encrypted is True
    blob = backend.download("production/app")
    assert decrypt(blob.decode(), PASS_B) == PLAINTEXT


def test_promote_reencrypt_old_passphrase_fails(backend):
    promote_env(
        backend, "staging/app", "production/app", PASS_A, dest_passphrase=PASS_B
    )
    blob = backend.download("production/app")
    with pytest.raises(Exception):
        decrypt(blob.decode(), PASS_A)


def test_promote_missing_source_raises(backend):
    with pytest.raises(KeyError, match="staging/missing"):
        promote_env(backend, "staging/missing", "production/app", PASS_A)


def test_promote_existing_dest_raises_without_overwrite(backend):
    promote_env(backend, "staging/app", "production/app", PASS_A)
    with pytest.raises(FileExistsError, match="production/app"):
        promote_env(backend, "staging/app", "production/app", PASS_A)


def test_promote_overwrite_replaces_dest(backend):
    # Store a different value at the destination first
    old_blob = encrypt("OLD=1\n", PASS_A).encode()
    backend.upload("production/app", old_blob)

    promote_env(
        backend, "staging/app", "production/app", PASS_A, overwrite=True
    )
    blob = backend.download("production/app")
    assert decrypt(blob.decode(), PASS_A) == PLAINTEXT
