"""Tests for envault.cascade."""
from __future__ import annotations

import pytest

from envault.backends.local import LocalBackend
from envault.cascade import CascadeResult, cascade_envs
from envault.crypto import decrypt, encrypt

PASS = "test-passphrase"


def _store(backend: LocalBackend, key: str, content: str, passphrase: str = PASS) -> None:
    backend.upload(key, encrypt(content, passphrase))


@pytest.fixture()
def backend(tmp_path):
    return LocalBackend(root=str(tmp_path))


def test_cascade_returns_cascade_result(backend):
    _store(backend, "base", "A=1\nB=2")
    result = cascade_envs(backend, ["base"], PASS)
    assert isinstance(result, CascadeResult)


def test_cascade_single_source(backend):
    _store(backend, "base", "A=1\nB=2")
    result = cascade_envs(backend, ["base"], PASS)
    assert result.merged == {"A": "1", "B": "2"}


def test_cascade_later_overrides_earlier(backend):
    _store(backend, "base", "A=1\nB=2")
    _store(backend, "override", "B=99\nC=3")
    result = cascade_envs(backend, ["base", "override"], PASS)
    assert result.merged["B"] == "99"
    assert result.merged["A"] == "1"
    assert result.merged["C"] == "3"


def test_cascade_sources_tracks_origin(backend):
    _store(backend, "base", "A=1")
    _store(backend, "override", "A=2")
    result = cascade_envs(backend, ["base", "override"], PASS)
    assert result.sources["A"] == "override"


def test_cascade_overrides_list_populated(backend):
    _store(backend, "base", "X=hello")
    _store(backend, "prod", "X=world")
    result = cascade_envs(backend, ["base", "prod"], PASS)
    assert len(result.overrides) == 1
    var, old, new = result.overrides[0]
    assert var == "X"
    assert old == "base"
    assert new == "prod"


def test_cascade_no_overrides_when_disjoint(backend):
    _store(backend, "a", "A=1")
    _store(backend, "b", "B=2")
    result = cascade_envs(backend, ["a", "b"], PASS)
    assert result.overrides == []


def test_cascade_stores_merged_blob(backend):
    _store(backend, "a", "A=1")
    _store(backend, "b", "B=2")
    cascade_envs(backend, ["a", "b"], PASS, out_key="merged")
    assert backend.exists("merged")
    blob = decrypt(backend.download("merged"), PASS)
    assert "A=1" in blob
    assert "B=2" in blob


def test_cascade_stores_with_different_out_passphrase(backend):
    _store(backend, "a", "KEY=val")
    cascade_envs(backend, ["a"], PASS, out_key="out", out_passphrase="other-pass")
    blob = decrypt(backend.download("out"), "other-pass")
    assert "KEY=val" in blob


def test_cascade_ignores_comments_and_blank_lines(backend):
    _store(backend, "a", "# comment\n\nA=1")
    result = cascade_envs(backend, ["a"], PASS)
    assert list(result.merged.keys()) == ["A"]
