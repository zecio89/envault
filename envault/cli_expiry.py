"""CLI commands for managing env-key expiry (TTL)."""

from __future__ import annotations

import click

from envault.backends import get_backend
from envault.expiry import set_expiry, get_expiry, delete_expiry, is_expired, list_expiring


@click.group("expiry")
def expiry() -> None:
    """Manage expiry (TTL) for env keys."""


def _backend(env_dir: str):
    return get_backend("local", root=env_dir)


@expiry.command("set")
@click.argument("env_key")
@click.argument("ttl_days", type=int)
@click.option("--env-dir", default=".envault", show_default=True, help="Backend directory.")
def set_cmd(env_key: str, ttl_days: int, env_dir: str) -> None:
    """Set a TTL of TTL_DAYS days on ENV_KEY."""
    backend = _backend(env_dir)
    try:
        record = set_expiry(backend, env_key, ttl_days)
    except KeyError as exc:
        raise click.ClickException(str(exc))
    except ValueError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"Expiry set: {env_key!r} expires at {record['expires_at']}")


@expiry.command("get")
@click.argument("env_key")
@click.option("--env-dir", default=".envault", show_default=True)
def get_cmd(env_key: str, env_dir: str) -> None:
    """Show the expiry record for ENV_KEY."""
    backend = _backend(env_dir)
    record = get_expiry(backend, env_key)
    if record is None:
        click.echo(f"No expiry set for {env_key!r}.")
        return
    expired_label = "  [EXPIRED]" if is_expired(backend, env_key) else ""
    click.echo(
        f"{env_key}: expires_at={record['expires_at']}  ttl_days={record['ttl_days']}{expired_label}"
    )


@expiry.command("rm")
@click.argument("env_key")
@click.option("--env-dir", default=".envault", show_default=True)
def rm_cmd(env_key: str, env_dir: str) -> None:
    """Remove the expiry record for ENV_KEY."""
    backend = _backend(env_dir)
    deleted = delete_expiry(backend, env_key)
    if deleted:
        click.echo(f"Expiry removed for {env_key!r}.")
    else:
        click.echo(f"No expiry record found for {env_key!r}.")


@expiry.command("list")
@click.option("--within-days", default=0, show_default=True,
              help="Include keys expiring within this many days (0 = expired only).")
@click.option("--env-dir", default=".envault", show_default=True)
def list_cmd(within_days: int, env_dir: str) -> None:
    """List keys that are expired or expiring soon."""
    backend = _backend(env_dir)
    records = list_expiring(backend, within_days=within_days)
    if not records:
        click.echo("No expiring keys found.")
        return
    for r in records:
        click.echo(f"{r['env_key']}: expires_at={r['expires_at']}  ttl_days={r['ttl_days']}")
