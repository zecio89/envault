"""Tests for envault.template.render_template."""
import pytest

from envault.backends.local import LocalBackend
from envault.crypto import encrypt
from envault.template import render_template

PASSPHRASE = "test-secret"
ENV_CONTENT = "DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc123\n"


@pytest.fixture()
def backend(tmp_path):
    b = LocalBackend(str(tmp_path))
    blob = encrypt(ENV_CONTENT, PASSPHRASE).encode()
    b.upload("prod", blob)
    return b


def test_render_simple_substitution(backend):
    tmpl = "host={{ DB_HOST }} port={{ DB_PORT }}"
    result = render_template(tmpl, backend, "prod", PASSPHRASE)
    assert result == "host=localhost port=5432"


def test_render_multiple_occurrences(backend):
    tmpl = "{{ DB_HOST }}:{{ DB_PORT }}/{{ DB_HOST }}"
    result = render_template(tmpl, backend, "prod", PASSPHRASE)
    assert result == "localhost:5432/localhost"


def test_render_missing_var_raises(backend):
    tmpl = "value={{ UNDEFINED_VAR }}"
    with pytest.raises(KeyError, match="UNDEFINED_VAR"):
        render_template(tmpl, backend, "prod", PASSPHRASE)


def test_render_missing_var_ok_when_missing_ok(backend):
    tmpl = "value={{ UNDEFINED_VAR }}"
    result = render_template(tmpl, backend, "prod", PASSPHRASE, missing_ok=True)
    assert result == "value={{ UNDEFINED_VAR }}"


def test_render_wrong_passphrase_raises(backend):
    from envault.crypto import DecryptionError
    with pytest.raises(DecryptionError):
        render_template("{{ DB_HOST }}", backend, "prod", "wrong")


def test_render_missing_env_key_raises(backend):
    with pytest.raises(FileNotFoundError, match="nonexistent"):
        render_template("{{ DB_HOST }}", backend, "nonexistent", PASSPHRASE)


def test_render_no_placeholders(backend):
    tmpl = "no substitutions here"
    result = render_template(tmpl, backend, "prod", PASSPHRASE)
    assert result == tmpl
