"""CLI commands for managing deprecated env keys."""

from __future__ import annotations

import sys

import click

from envault.backends import get_backend
from envault.deprecate import (
    clear_deprecation,
    get_deprecation,
    is_sunset,
    list_deprecated,
    mark_deprecated,
)


def _backend(env_dir: str):
    return get_backend("local", root=env_dir)


@click.group()
def deprecate():
    """Manage deprecated env keys."""


@deprecate.command("mark")
@click.argument("env_key")
@click.option("--reason", required=True, help="Why this key is deprecated.")
@click.option("--replacement", default=None, help="Key to use instead.")
@click.option("--sunset", default=None, help="ISO date after which key is removed.")
@click.option("--env-dir", default=".", show_default=True)
def mark_cmd(env_key, reason, replacement, sunset, env_dir):
    """Mark ENV_KEY as deprecated."""
    backend = _backend(env_dir)
    try:
        record = mark_deprecated(backend, env_key, reason, replacement=replacement, sunset=sunset)
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    click.echo(f"Marked {record['key']!r} as deprecated.")
    if replacement:
        click.echo(f"  Replacement: {replacement}")
    if sunset:
        click.echo(f"  Sunset: {sunset}")


@deprecate.command("get")
@click.argument("env_key")
@click.option("--env-dir", default=".", show_default=True)
def get_cmd(env_key, env_dir):
    """Show deprecation info for ENV_KEY."""
    backend = _backend(env_dir)
    record = get_deprecation(backend, env_key)
    if record is None:
        click.echo(f"{env_key!r} is not deprecated.")
        return
    click.echo(f"Key:         {record['key']}")
    click.echo(f"Reason:      {record['reason']}")
    click.echo(f"Replacement: {record.get('replacement') or '(none)'}")
    click.echo(f"Sunset:      {record.get('sunset') or '(none)'}")
    click.echo(f"Deprecated:  {record['deprecated_at']}")
    if is_sunset(record):
        click.echo("  *** SUNSET DATE HAS PASSED ***", err=True)


@deprecate.command("rm")
@click.argument("env_key")
@click.option("--env-dir", default=".", show_default=True)
def rm_cmd(env_key, env_dir):
    """Remove the deprecation marker for ENV_KEY."""
    backend = _backend(env_dir)
    removed = clear_deprecation(backend, env_key)
    if removed:
        click.echo(f"Deprecation marker removed for {env_key!r}.")
    else:
        click.echo(f"No deprecation marker found for {env_key!r}.")


@deprecate.command("list")
@click.option("--env-dir", default=".", show_default=True)
def list_cmd(env_dir):
    """List all deprecated keys."""
    backend = _backend(env_dir)
    records = list_deprecated(backend)
    if not records:
        click.echo("No deprecated keys.")
        return
    for rec in records:
        sunset_flag = " [SUNSET]" if is_sunset(rec) else ""
        repl = f" -> {rec['replacement']}" if rec.get("replacement") else ""
        click.echo(f"  {rec['key']}{repl}{sunset_flag}  ({rec['reason']})")
