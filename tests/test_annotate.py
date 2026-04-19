import pytest
from envault.backends.local import LocalBackend
from envault.annotate import set_annotation, get_annotation, delete_annotation, list_annotations


@pytest.fixture
def backend(tmp_path):
    return LocalBackend(str(tmp_path))


@pytest.fixture
def populated_backend(backend):
    backend.upload("staging", b"encrypted-blob")
    backend.upload("production", b"encrypted-blob-2")
    return backend


def test_set_annotation_returns_record(populated_backend):
    rec = set_annotation(populated_backend, "staging", "Used for QA", author="alice")
    assert rec["key"] == "staging"
    assert rec["note"] == "Used for QA"
    assert rec["author"] == "alice"


def test_get_annotation_returns_record(populated_backend):
    set_annotation(populated_backend, "staging", "QA env", author="bob")
    rec = get_annotation(populated_backend, "staging")
    assert rec is not None
    assert rec["note"] == "QA env"
    assert rec["author"] == "bob"


def test_get_annotation_none_when_unset(populated_backend):
    assert get_annotation(populated_backend, "staging") is None


def test_set_annotation_raises_for_missing_key(backend):
    with pytest.raises(KeyError):
        set_annotation(backend, "nonexistent", "some note")


def test_delete_annotation_returns_true(populated_backend):
    set_annotation(populated_backend, "staging", "temp note")
    assert delete_annotation(populated_backend, "staging") is True
    assert get_annotation(populated_backend, "staging") is None


def test_delete_annotation_returns_false_when_absent(populated_backend):
    assert delete_annotation(populated_backend, "staging") is False


def test_list_annotations_returns_all(populated_backend):
    set_annotation(populated_backend, "staging", "note1")
    set_annotation(populated_backend, "production", "note2")
    annotations = list_annotations(populated_backend)
    keys = {a["key"] for a in annotations}
    assert keys == {"staging", "production"}


def test_list_annotations_empty(populated_backend):
    assert list_annotations(populated_backend) == []
