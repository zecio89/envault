import pytest
from envault.backends.local import LocalBackend
from envault.alias import set_alias, get_alias, delete_alias, list_aliases, resolve


@pytest.fixture
def backend(tmp_path):
    return LocalBackend(str(tmp_path))


@pytest.fixture
def populated_backend(backend):
    backend.upload("production", b"encrypted-blob")
    backend.upload("staging", b"encrypted-blob-2")
    return backend


def test_set_alias_returns_mapping(populated_backend):
    result = set_alias(populated_backend, "prod", "production")
    assert result == {"alias": "prod", "key": "production"}


def test_get_alias_returns_key(populated_backend):
    set_alias(populated_backend, "prod", "production")
    assert get_alias(populated_backend, "prod") == "production"


def test_get_alias_none_when_unset(populated_backend):
    assert get_alias(populated_backend, "nope") is None


def test_set_alias_raises_for_missing_key(backend):
    with pytest.raises(KeyError, match="Key not found"):
        set_alias(backend, "prod", "nonexistent")


def test_delete_alias(populated_backend):
    set_alias(populated_backend, "prod", "production")
    delete_alias(populated_backend, "prod")
    assert get_alias(populated_backend, "prod") is None


def test_delete_alias_raises_when_missing(populated_backend):
    with pytest.raises(KeyError, match="Alias not found"):
        delete_alias(populated_backend, "ghost")


def test_list_aliases(populated_backend):
    set_alias(populated_backend, "prod", "production")
    set_alias(populated_backend, "stg", "staging")
    aliases = list_aliases(populated_backend)
    assert aliases == {"prod": "production", "stg": "staging"}


def test_resolve_alias(populated_backend):
    set_alias(populated_backend, "prod", "production")
    assert resolve(populated_backend, "prod") == "production"


def test_resolve_passthrough_when_no_alias(populated_backend):
    assert resolve(populated_backend, "production") == "production"
