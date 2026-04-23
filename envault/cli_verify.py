"""CLI commands for verifying encrypted env blobs."""
from __future__ import annotations

import click

from envault.backends import get_backend
from envault.verify import verify_env


@click.group("verify")
def verify() -> None:
    """Verify integrity of stored encrypted env files."""


@verify.command("run")
@click.option("--env-dir", default=".", show_default=True, help="Backend directory.")
@click.option("--key", default=None, help="Specific env key to verify (default: all).")
@click.option(
    "--passphrase",
    prompt=True,
    hide_input=True,
    envvar="ENVAULT_PASSPHRASE",
    help="Decryption passphrase.",
)
def run_cmd(env_dir: str, key: str | None, passphrase: str) -> None:
    """Decrypt and verify one or all stored env blobs."""
    backend = get_backend("local", path=env_dir)
    summary = verify_env(backend, passphrase, key=key)

    if not summary.results:
        click.echo("No env keys found to verify.")
        return

    for result in summary.results:
        status = click.style("OK", fg="green") if result.ok else click.style("FAIL", fg="red")
        line = f"  [{status}] {result.key}"
        if result.error:
            line += f"  — {result.error}"
        click.echo(line)

    total = len(summary.results)
    passed = len(summary.passed)
    failed = len(summary.failed)
    click.echo(f"\nResult: {passed}/{total} passed", err=False)

    if not summary.all_ok:
        raise SystemExit(1)
