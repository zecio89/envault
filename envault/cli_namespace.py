"""CLI commands for namespace management."""

from __future__ import annotations

import os
import sys

import click

from envault.backends import get_backend
from envault.namespace import (
    assign_namespace,
    delete_namespace,
    get_namespace_keys,
    list_namespaces,
    remove_from_namespace,
)


def _backend(env_dir: str):
    return get_backend("local", root=env_dir)


@click.group()
def namespace():
    """Manage env-key namespaces."""


@namespace.command("assign")
@click.argument("env_key")
@click.argument("ns")
@click.option("--dir", "env_dir", default=".", show_default=True, help="Backend root dir.")
def assign_cmd(env_key: str, ns: str, env_dir: str):
    """Assign ENV_KEY to namespace NS."""
    backend = _backend(env_dir)
    try:
        result = assign_namespace(backend, env_key, ns)
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    click.echo(f"Assigned '{result['env_key']}' to namespace '{result['namespace']}'.")


@namespace.command("remove")
@click.argument("env_key")
@click.argument("ns")
@click.option("--dir", "env_dir", default=".", show_default=True)
def remove_cmd(env_key: str, ns: str, env_dir: str):
    """Remove ENV_KEY from namespace NS."""
    backend = _backend(env_dir)
    found = remove_from_namespace(backend, env_key, ns)
    if not found:
        click.echo(f"'{env_key}' was not in namespace '{ns}'.", err=True)
        sys.exit(1)
    click.echo(f"Removed '{env_key}' from namespace '{ns}'.")


@namespace.command("list")
@click.option("--dir", "env_dir", default=".", show_default=True)
def list_cmd(env_dir: str):
    """List all namespaces."""
    backend = _backend(env_dir)
    namespaces = list_namespaces(backend)
    if not namespaces:
        click.echo("No namespaces defined.")
        return
    for ns in namespaces:
        click.echo(ns)


@namespace.command("show")
@click.argument("ns")
@click.option("--dir", "env_dir", default=".", show_default=True)
def show_cmd(ns: str, env_dir: str):
    """Show all env keys in namespace NS."""
    backend = _backend(env_dir)
    keys = get_namespace_keys(backend, ns)
    if not keys:
        click.echo(f"Namespace '{ns}' is empty or does not exist.")
        return
    for k in keys:
        click.echo(k)


@namespace.command("delete")
@click.argument("ns")
@click.option("--dir", "env_dir", default=".", show_default=True)
def delete_cmd(ns: str, env_dir: str):
    """Delete namespace NS (env keys are not deleted)."""
    backend = _backend(env_dir)
    deleted = delete_namespace(backend, ns)
    if not deleted:
        click.echo(f"Namespace '{ns}' not found.", err=True)
        sys.exit(1)
    click.echo(f"Deleted namespace '{ns}'.")
