"""cli_cascade.py — CLI commands for the cascade (priority-merge) feature."""
from __future__ import annotations

import click

from envault.backends import get_backend
from envault.cascade import cascade_envs


@click.group("cascade")
def cascade() -> None:
    """Merge multiple env files in priority order."""


@cascade.command("run")
@click.argument("env_keys", nargs=-1, required=True)
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
@click.option("--out", default=None, help="Store merged result under this key.")
@click.option("--out-passphrase", default=None, hide_input=True, help="Passphrase for the output key (defaults to --passphrase).")
@click.option("--env-dir", default=".envault", show_default=True)
@click.option("--show-overrides", is_flag=True, default=False, help="Print variables that were overridden.")
def run_cmd(
    env_keys: tuple,
    passphrase: str,
    out: str | None,
    out_passphrase: str | None,
    env_dir: str,
    show_overrides: bool,
) -> None:
    """Merge ENV_KEYS in order; later keys override earlier ones."""
    backend = get_backend("local", root=env_dir)
    result = cascade_envs(
        backend,
        list(env_keys),
        passphrase,
        out_key=out,
        out_passphrase=out_passphrase,
    )

    click.echo(f"Merged {len(result.merged)} variable(s) from {len(env_keys)} source(s).")

    if show_overrides:
        if result.overrides:
            click.echo("Overrides (var: old-source -> new-source):")
            for var, old, new in result.overrides:
                click.echo(f"  {var}: {old} -> {new}")
        else:
            click.echo("No overrides.")

    if out:
        click.echo(f"Merged env stored as '{out}'.")
    else:
        click.echo("\nMerged variables:")
        for k, v in sorted(result.merged.items()):
            click.echo(f"  {k}={v}")
