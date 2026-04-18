"""Tests for envault.tags module."""
import pytest
from envault.backends.local import LocalBackend
from envault.tags import set_tags, get_tags, delete_tags, list_tagged


@pytest.fixture
def backend(tmp_path):
    b = LocalBackend(str(tmp_path))
    # seed a couple of env keys
    b.upload("prod/app", b"encrypted-blob-1")
    b.upload("staging/app", b"encrypted-blob-2")
    return b


def test_set_and_get_tags(backend):
    set_tags(backend, "prod/app", {"team": "backend", "env": "production"})
    result = get_tags(backend, "prod/app")
    assert result == {"team": "backend", "env": "production"}


def test_get_tags_returns_empty_when_none(backend):
    result = get_tags(backend, "staging/app")
    assert result == {}


def test_set_tags_raises_for_missing_key(backend):
    with pytest.raises(KeyError, match="ghost/key"):
        set_tags(backend, "ghost/key", {"x": "y"})


def test_delete_tags(backend):
    set_tags(backend, "prod/app", {"team": "backend"})
    delete_tags(backend, "prod/app")
    assert get_tags(backend, "prod/app") == {}


def test_delete_tags_noop_when_none(backend):
    # Should not raise
    delete_tags(backend, "staging/app")


def test_list_tagged_returns_tagged_keys(backend):
    set_tags(backend, "prod/app", {"team": "backend"})
    result = list_tagged(backend)
    assert "prod/app" in result
    assert "staging/app" not in result


def test_list_tagged_filter_by_tag(backend):
    set_tags(backend, "prod/app", {"team": "backend"})
    set_tags(backend, "staging/app", {"team": "frontend"})
    result = list_tagged(backend, filter_tag="team", filter_value="backend")
    assert result == ["prod/app"]


def test_list_tagged_filter_tag_no_value(backend):
    set_tags(backend, "prod/app", {"team": "backend"})
    set_tags(backend, "staging/app", {"team": "frontend"})
    result = list_tagged(backend, filter_tag="team")
    assert set(result) == {"prod/app", "staging/app"}


def test_list_tagged_empty(backend):
    result = list_tagged(backend)
    assert result == []
