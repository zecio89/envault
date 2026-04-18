import pytest
from pathlib import Path

from envault.backends.local import LocalBackend
from envault.backends import get_backend


@pytest.fixture
def local_backend(tmp_path):
    return LocalBackend(storage_dir=str(tmp_path / "envault_test"))


def test_upload_and_download(local_backend):
    local_backend.upload("myapp/prod", b"encrypted-data")
    result = local_backend.download("myapp/prod")
    assert result == b"encrypted-data"


def test_exists_true(local_backend):
    local_backend.upload("key1", b"data")
    assert local_backend.exists("key1") is True


def test_exists_false(local_backend):
    assert local_backend.exists("nonexistent") is False


def test_list_keys(local_backend):
    local_backend.upload("alpha", b"a")
    local_backend.upload("beta", b"b")
    keys = local_backend.list_keys()
    assert sorted(keys) == ["alpha", "beta"]


def test_delete(local_backend):
    local_backend.upload("to-delete", b"data")
    local_backend.delete("to-delete")
    assert local_backend.exists("to-delete") is False


def test_delete_nonexistent_raises(local_backend):
    with pytest.raises(FileNotFoundError):
        local_backend.delete("ghost")


def test_download_nonexistent_raises(local_backend):
    with pytest.raises(FileNotFoundError):
        local_backend.download("missing")


def test_get_backend_local(tmp_path):
    backend = get_backend("local", storage_dir=str(tmp_path / "store"))
    assert isinstance(backend, LocalBackend)


def test_get_backend_invalid():
    with pytest.raises(ValueError, match="Unknown backend"):
        get_backend("gcs")


def test_slash_in_key_stored_safely(local_backend, tmp_path):
    local_backend.upload("team/staging", b"secret")
    files = list(Path(local_backend.storage_dir).iterdir())
    assert any("__" in f.name for f in files)
    assert local_backend.download("team/staging") == b"secret"
