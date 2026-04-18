"""CLI commands for rotation reminders."""

import click
from envault.cli import make_vault
from envault.remind import (
    record_rotation,
    get_rotation_info,
    list_overdue,
)


@click.group("remind")
def remind():
    """Rotation reminder commands."""


@remind.command("record")
@click.argument("key")
@click.option("--env-dir", default=".envault", show_default=True)
def record_cmd(key, env_dir):
    """Record that KEY was rotated now."""
    from envault.backends import get_backend
    backend = get_backend("local", env_dir=env_dir)
    try:
        entry = record_rotation(backend, key)
        click.echo(f"Recorded rotation for '{key}' at {entry['last_rotated']}.")
    except KeyError as e:
        click.echo(str(e), err=True)
        raise SystemExit(1)


@remind.command("status")
@click.argument("key")
@click.option("--env-dir", default=".envault", show_default=True)
@click.option("--max-days", default=30, show_default=True)
def status_cmd(key, env_dir, max_days):
    """Show rotation status for KEY."""
    from envault.backends import get_backend
    from envault.remind import check_overdue
    backend = get_backend("local", env_dir=env_dir)
    info = get_rotation_info(backend, key)
    if info is None:
        click.echo(f"No rotation record for '{key}'. Consider rotating soon.")
        return
    overdue = check_overdue(backend, key, max_days)
    status = "OVERDUE" if overdue else "OK"
    click.echo(f"[{status}] '{key}' last rotated: {info['last_rotated']} (max {max_days} days)")


@remind.command("list-overdue")
@click.option("--env-dir", default=".envault", show_default=True)
@click.option("--max-days", default=30, show_default=True)
def list_cmd(env_dir, max_days):
    """List all keys overdue for rotation."""
    from envault.backends import get_backend
    backend = get_backend("local", env_dir=env_dir)
    overdue = list_overdue(backend, max_days)
    if not overdue:
        click.echo("All keys are up to date.")
    else:
        click.echo(f"Overdue keys (>{max_days} days):")
        for k in overdue:
            click.echo(f"  {k}")
