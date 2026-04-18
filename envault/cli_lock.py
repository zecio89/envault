"""CLI commands for locking and unlocking env entries."""

import click
from envault.cli import make_vault
from envault.lock import lock_env, unlock_env, is_locked, list_locked


@click.group()
def lock():
    """Lock/unlock env entries to prevent pull access."""


@lock.command("lock")
@click.argument("env_key")
@click.option("--env-dir", default=".envault", show_default=True)
@click.option("--backend", "backend_type", default="local", show_default=True)
def lock_cmd(env_key, env_dir, backend_type):
    """Lock an env entry."""
    from envault.backends import get_backend
    backend = get_backend(backend_type, env_dir)
    try:
        lock_env(backend, env_key)
        click.echo(f"Locked: {env_key}")
    except KeyError as exc:
        raise click.ClickException(str(exc))


@lock.command("unlock")
@click.argument("env_key")
@click.option("--env-dir", default=".envault", show_default=True)
@click.option("--backend", "backend_type", default="local", show_default=True)
def unlock_cmd(env_key, env_dir, backend_type):
    """Unlock an env entry."""
    from envault.backends import get_backend
    backend = get_backend(backend_type, env_dir)
    try:
        unlock_env(backend, env_key)
        click.echo(f"Unlocked: {env_key}")
    except KeyError as exc:
        raise click.ClickException(str(exc))


@lock.command("status")
@click.argument("env_key")
@click.option("--env-dir", default=".envault", show_default=True)
@click.option("--backend", "backend_type", default="local", show_default=True)
def status_cmd(env_key, env_dir, backend_type):
    """Show lock status of an env entry."""
    from envault.backends import get_backend
    backend = get_backend(backend_type, env_dir)
    state = "locked" if is_locked(backend, env_key) else "unlocked"
    click.echo(f"{env_key}: {state}")


@lock.command("list")
@click.option("--env-dir", default=".envault", show_default=True)
@click.option("--backend", "backend_type", default="local", show_default=True)
def list_cmd(env_dir, backend_type):
    """List all currently locked env entries."""
    from envault.backends import get_backend
    backend = get_backend(backend_type, env_dir)
    locked = list_locked(backend)
    if not locked:
        click.echo("No locked envs.")
    else:
        for key in sorted(locked):
            click.echo(key)
