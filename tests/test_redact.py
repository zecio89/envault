"""Tests for envault.redact."""

import pytest
from envault.redact import redact_env, _REDACT_PLACEHOLDER, _is_sensitive


CLEAN_CONTENT = """APP_NAME=myapp
APP_ENV=production
PORT=8080
"""

SENSITIVE_CONTENT = """APP_NAME=myapp
API_KEY=super-secret-key-1234
DB_PASSWORD=hunter2
PORT=8080
AUTH_TOKEN=tok_abcdefghijklmnop
"""


def test_no_redaction_for_clean_content():
    result = redact_env(CLEAN_CONTENT)
    assert result.redacted_count == 0
    assert result.original_count == 3
    assert result.all_clear


def test_sensitive_keys_are_redacted():
    result = redact_env(SENSITIVE_CONTENT)
    assert result.redacted_count == 3
    assert result.original_count == 5
    assert not result.all_clear


def test_redacted_lines_contain_placeholder():
    result = redact_env(SENSITIVE_CONTENT)
    joined = "\n".join(result.lines)
    assert "super-secret-key-1234" not in joined
    assert "hunter2" not in joined
    assert "tok_abcdefghijklmnop" not in joined
    assert _REDACT_PLACEHOLDER in joined


def test_non_sensitive_values_preserved():
    result = redact_env(SENSITIVE_CONTENT)
    joined = "\n".join(result.lines)
    assert "APP_NAME=myapp" in joined
    assert "PORT=8080" in joined


def test_partial_mode_shows_partial_value():
    result = redact_env(SENSITIVE_CONTENT, partial=True)
    joined = "\n".join(result.lines)
    # Should show first 4 chars of API_KEY value
    assert "supe" in joined
    assert "1234" in joined
    # Full value should not appear
    assert "super-secret-key-1234" not in joined


def test_partial_mode_short_value_fully_redacted():
    content = "SECRET=ab\n"
    result = redact_env(content, partial=True)
    assert _REDACT_PLACEHOLDER in "\n".join(result.lines)


def test_extra_keys_are_redacted():
    content = "DEPLOY_HOST=192.168.1.1\nAPP_NAME=myapp\n"
    result = redact_env(content, extra_keys=["DEPLOY_HOST"])
    joined = "\n".join(result.lines)
    assert "192.168.1.1" not in joined
    assert "APP_NAME=myapp" in joined


def test_comments_and_blank_lines_preserved():
    content = "# This is a comment\n\nAPP_NAME=myapp\n"
    result = redact_env(content)
    assert "# This is a comment" in result.lines
    assert "" in result.lines


def test_is_sensitive_matches_common_keys():
    assert _is_sensitive("API_KEY")
    assert _is_sensitive("db_password")
    assert _is_sensitive("AUTH_TOKEN")
    assert _is_sensitive("PRIVATE_KEY")
    assert not _is_sensitive("APP_NAME")
    assert not _is_sensitive("PORT")


def test_line_without_equals_is_passed_through():
    content = "MALFORMED_LINE\nGOOD=value\n"
    result = redact_env(content)
    assert "MALFORMED_LINE" in result.lines
    assert result.original_count == 1
