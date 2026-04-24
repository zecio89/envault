"""CLI commands for managing backend quotas."""

from __future__ import annotations

import click

from envault.backends import get_backend
from envault.quota import set_quota, get_quota, delete_quota, check_quota


@click.group()
def quota() -> None:
    """Manage storage quotas for the vault backend."""


def _backend(env_dir: str):
    return get_backend("local", root=env_dir)


@quota.command("set")
@click.option("--env-dir", default=".envault", show_default=True, help="Backend directory.")
@click.option("--max-keys", required=True, type=int, help="Maximum number of env keys allowed.")
@click.option(
    "--warn-at",
    default=0.8,
    show_default=True,
    type=float,
    help="Fraction of max-keys at which to show a warning (0–1).",
)
def set_cmd(env_dir: str, max_keys: int, warn_at: float) -> None:
    """Set or update the quota configuration."""
    try:
        config = set_quota(_backend(env_dir), max_keys=max_keys, warn_threshold=warn_at)
        click.echo(f"Quota set: max_keys={config.max_keys}, warn_at={config.warn_threshold:.0%}")
    except ValueError as exc:
        raise click.ClickException(str(exc))


@quota.command("status")
@click.option("--env-dir", default=".envault", show_default=True, help="Backend directory.")
def status_cmd(env_dir: str) -> None:
    """Show current quota usage."""
    status = check_quota(_backend(env_dir))
    if status is None:
        click.echo("No quota configured.")
        return
    bar = "#" * int(status.usage_fraction * 20)
    click.echo(f"Keys: {status.current}/{status.max_keys}  [{bar:<20}] {status.usage_fraction:.0%}")
    if status.exceeded:
        click.echo(click.style("EXCEEDED: quota limit reached.", fg="red"))
    elif status.warning:
        click.echo(click.style("WARNING: approaching quota limit.", fg="yellow"))
    else:
        click.echo(click.style("OK", fg="green"))


@quota.command("get")
@click.option("--env-dir", default=".envault", show_default=True, help="Backend directory.")
def get_cmd(env_dir: str) -> None:
    """Show the configured quota limits."""
    config = get_quota(_backend(env_dir))
    if config is None:
        click.echo("No quota configured.")
    else:
        click.echo(f"max_keys={config.max_keys}  warn_threshold={config.warn_threshold:.0%}")


@quota.command("rm")
@click.option("--env-dir", default=".envault", show_default=True, help="Backend directory.")
def rm_cmd(env_dir: str) -> None:
    """Remove the quota configuration."""
    delete_quota(_backend(env_dir))
    click.echo("Quota configuration removed.")
