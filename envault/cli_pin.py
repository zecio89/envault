"""CLI commands for pinning env versions."""
import click
from envault.backends.local import LocalBackend
from envault import pin as pin_mod


def _backend(env_dir: str) -> LocalBackend:
    return LocalBackend(env_dir)


@click.group()
def pin():
    """Pin a specific version of an env as a stable reference."""


@pin.command("set")
@click.argument("key")
@click.argument("version_id")
@click.option("--label", default="stable", show_default=True, help="Pin label")
@click.option("--env-dir", default=".envault", show_default=True)
def set_cmd(key: str, version_id: str, label: str, env_dir: str):
    """Pin KEY at VERSION_ID."""
    backend = _backend(env_dir)
    try:
        record = pin_mod.pin_version(backend, key, version_id, label)
        click.echo(f"Pinned '{key}' at version '{record['version_id']}' [{label}]")
    except KeyError as exc:
        raise click.ClickException(str(exc))


@pin.command("get")
@click.argument("key")
@click.option("--env-dir", default=".envault", show_default=True)
def get_cmd(key: str, env_dir: str):
    """Show the pin for KEY."""
    backend = _backend(env_dir)
    record = pin_mod.get_pin(backend, key)
    if record is None:
        click.echo(f"No pin set for '{key}'.")
    else:
        click.echo(f"{record['env_key']}  version={record['version_id']}  label={record['label']}")


@pin.command("rm")
@click.argument("key")
@click.option("--env-dir", default=".envault", show_default=True)
def rm_cmd(key: str, env_dir: str):
    """Remove the pin for KEY."""
    backend = _backend(env_dir)
    removed = pin_mod.delete_pin(backend, key)
    if removed:
        click.echo(f"Pin removed for '{key}'.")
    else:
        click.echo(f"No pin found for '{key}'.")


@pin.command("list")
@click.option("--env-dir", default=".envault", show_default=True)
def list_cmd(env_dir: str):
    """List all pinned envs."""
    backend = _backend(env_dir)
    pins = pin_mod.list_pins(backend)
    if not pins:
        click.echo("No pins set.")
    else:
        for p in pins:
            click.echo(f"{p['env_key']}  version={p['version_id']}  label={p['label']}")
