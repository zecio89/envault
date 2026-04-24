"""CLI commands for managing env key policies."""

from __future__ import annotations

import click

from envault.backends import get_backend
from envault.policy import (
    delete_policy,
    get_policy,
    is_allowed,
    list_policies,
    set_policy,
)


@click.group("policy")
def policy() -> None:
    """Manage access policies for env keys."""


@policy.command("set")
@click.argument("env_key")
@click.option("--user", "users", multiple=True, help="Allowed user (repeatable).")
@click.option("--read-only", is_flag=True, default=False, help="Mark key as read-only.")
@click.option("--max-age-days", type=int, default=None, help="Max age in days before rotation.")
@click.option("--backend", "backend_name", default="local", show_default=True)
@click.option("--dir", "env_dir", default=".envault", show_default=True)
def set_cmd(
    env_key: str,
    users: tuple[str, ...],
    read_only: bool,
    max_age_days: int | None,
    backend_name: str,
    env_dir: str,
) -> None:
    """Set a policy on ENV_KEY."""
    backend = get_backend(backend_name, root=env_dir)
    try:
        rec = set_policy(
            backend,
            env_key,
            allowed_users=list(users) if users else None,
            read_only=read_only,
            max_age_days=max_age_days,
        )
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Policy set for '{env_key}': {rec}")


@policy.command("get")
@click.argument("env_key")
@click.option("--backend", "backend_name", default="local", show_default=True)
@click.option("--dir", "env_dir", default=".envault", show_default=True)
def get_cmd(env_key: str, backend_name: str, env_dir: str) -> None:
    """Show the policy for ENV_KEY."""
    backend = get_backend(backend_name, root=env_dir)
    rec = get_policy(backend, env_key)
    if rec is None:
        click.echo(f"No policy set for '{env_key}'.")
    else:
        for k, v in rec.items():
            click.echo(f"  {k}: {v}")


@policy.command("rm")
@click.argument("env_key")
@click.option("--backend", "backend_name", default="local", show_default=True)
@click.option("--dir", "env_dir", default=".envault", show_default=True)
def rm_cmd(env_key: str, backend_name: str, env_dir: str) -> None:
    """Remove the policy for ENV_KEY."""
    backend = get_backend(backend_name, root=env_dir)
    delete_policy(backend, env_key)
    click.echo(f"Policy removed for '{env_key}'.")


@policy.command("list")
@click.option("--backend", "backend_name", default="local", show_default=True)
@click.option("--dir", "env_dir", default=".envault", show_default=True)
def list_cmd(backend_name: str, env_dir: str) -> None:
    """List all keys with an active policy."""
    backend = get_backend(backend_name, root=env_dir)
    keys = list_policies(backend)
    if not keys:
        click.echo("No policies defined.")
    else:
        for k in keys:
            click.echo(k)


@policy.command("check")
@click.argument("env_key")
@click.argument("user")
@click.option("--backend", "backend_name", default="local", show_default=True)
@click.option("--dir", "env_dir", default=".envault", show_default=True)
def check_cmd(env_key: str, user: str, backend_name: str, env_dir: str) -> None:
    """Check whether USER is allowed access to ENV_KEY."""
    backend = get_backend(backend_name, root=env_dir)
    allowed = is_allowed(backend, env_key, user)
    status = "ALLOWED" if allowed else "DENIED"
    click.echo(f"{user} -> {env_key}: {status}")
