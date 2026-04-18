"""Lint .env files for common issues."""
from __future__ import annotations
import re
from typing import NamedTuple


class LintIssue(NamedTuple):
    line: int
    code: str
    message: str


_VALID_KEY_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$')


def lint_content(content: str) -> list[LintIssue]:
    """Return a list of lint issues found in *content*."""
    issues: list[LintIssue] = []
    seen_keys: dict[str, int] = {}

    for lineno, raw in enumerate(content.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue

        if '=' not in line:
            issues.append(LintIssue(lineno, 'E001', f'Missing "=" in line: {raw!r}'))
            continue

        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip()

        if not _VALID_KEY_RE.match(key):
            issues.append(LintIssue(lineno, 'E002', f'Invalid key name: {key!r}'))

        if key in seen_keys:
            issues.append(
                LintIssue(lineno, 'W001', f'Duplicate key {key!r} (first seen on line {seen_keys[key]})')
            )
        else:
            seen_keys[key] = lineno

        if not value:
            issues.append(LintIssue(lineno, 'W002', f'Empty value for key {key!r}'))

        if value.startswith(' ') or value.endswith(' '):
            issues.append(LintIssue(lineno, 'W003', f'Value for {key!r} has surrounding whitespace'))

        if (value.startswith('"') and not value.endswith('"')) or \
           (value.startswith("'") and not value.endswith("'")):
            issues.append(LintIssue(lineno, 'E003', f'Unmatched quote for key {key!r}'))

    return issues
