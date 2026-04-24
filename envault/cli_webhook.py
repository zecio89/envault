"""CLI commands for webhook management."""

from __future__ import annotations

import click

from envault.backends import get_backend
from envault.webhook import (
    register_webhook,
    get_webhook,
    delete_webhook,
    list_webhooks,
)


def _backend(env_dir: str):
    return get_backend("local", root=env_dir)


@click.group("webhook")
def webhook():
    """Manage webhook notifications."""


@webhook.command("register")
@click.argument("name")
@click.argument("url")
@click.option(
    "--event",
    "events",
    multiple=True,
    default=["push", "pull", "rotate"],
    show_default=True,
    help="Event type to subscribe to (repeatable).",
)
@click.option("--env-dir", default=".", show_default=True)
def register_cmd(name: str, url: str, events: tuple[str, ...], env_dir: str) -> None:
    """Register a webhook URL for one or more event types."""
    backend = _backend(env_dir)
    record = register_webhook(backend, name, url, list(events))
    click.echo(f"Registered webhook '{record['name']}' -> {record['url']}")
    click.echo(f"Events: {', '.join(record['events'])}")


@webhook.command("get")
@click.argument("name")
@click.option("--env-dir", default=".", show_default=True)
def get_cmd(name: str, env_dir: str) -> None:
    """Show details for a registered webhook."""
    backend = _backend(env_dir)
    record = get_webhook(backend, name)
    if record is None:
        click.echo(f"No webhook named '{name}'.")
        raise SystemExit(1)
    click.echo(f"URL: {record['url']}")
    click.echo(f"Events: {', '.join(record['events'])}")


@webhook.command("rm")
@click.argument("name")
@click.option("--env-dir", default=".", show_default=True)
def rm_cmd(name: str, env_dir: str) -> None:
    """Remove a registered webhook."""
    backend = _backend(env_dir)
    removed = delete_webhook(backend, name)
    if removed:
        click.echo(f"Removed webhook '{name}'.")
    else:
        click.echo(f"No webhook named '{name}'.")
        raise SystemExit(1)


@webhook.command("list")
@click.option("--env-dir", default=".", show_default=True)
def list_cmd(env_dir: str) -> None:
    """List all registered webhooks."""
    backend = _backend(env_dir)
    hooks = list_webhooks(backend)
    if not hooks:
        click.echo("No webhooks registered.")
        return
    for h in hooks:
        click.echo(f"{h['name']:20s}  {h['url']}  [{', '.join(h['events'])}]")
