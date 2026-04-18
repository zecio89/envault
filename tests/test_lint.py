import pytest
from envault.lint import lint_content, LintIssue


def test_no_issues_for_clean_content():
    content = "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc123\n"
    assert lint_content(content) == []


def test_ignores_comments_and_blank_lines():
    content = "# comment\n\nDB_HOST=localhost\n"
    assert lint_content(content) == []


def test_missing_equals_sign():
    issues = lint_content("BADLINE\n")
    assert any(i.code == 'E001' for i in issues)


def test_invalid_key_name_lowercase():
    issues = lint_content("bad_key=value\n")
    assert any(i.code == 'E002' for i in issues)


def test_invalid_key_name_starts_with_digit():
    issues = lint_content("1BAD=value\n")
    assert any(i.code == 'E002' for i in issues)


def test_duplicate_key_warning():
    content = "DB_HOST=localhost\nDB_HOST=remotehost\n"
    issues = lint_content(content)
    w = [i for i in issues if i.code == 'W001']
    assert len(w) == 1
    assert 'DB_HOST' in w[0].message


def test_empty_value_warning():
    issues = lint_content("SECRET=\n")
    assert any(i.code == 'W002' for i in issues)


def test_whitespace_value_warning():
    issues = lint_content("SECRET= value \n")
    assert any(i.code == 'W003' for i in issues)


def test_unmatched_quote_error():
    issues = lint_content('SECRET="oops\n')
    assert any(i.code == 'E003' for i in issues)


def test_multiple_issues_in_one_file():
    content = "bad_key=\nbad_key=\n"
    issues = lint_content(content)
    codes = {i.code for i in issues}
    assert 'E002' in codes
    assert 'W002' in codes
    assert 'W001' in codes


def test_lint_issue_is_named_tuple():
    issue = LintIssue(1, 'E001', 'msg')
    assert issue.line == 1
    assert issue.code == 'E001'
    assert issue.message == 'msg'
