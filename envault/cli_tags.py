"""CLI commands for tag management."""
import click
from envault.cli import make_vault
from envault.tags import set_tags, get_tags, delete_tags, list_tagged


@click.group()
def tags():
    """Manage metadata tags on stored env keys."""


@tags.command("set")
@click.argument("env_key")
@click.argument("pairs", nargs=-1, required=True, metavar="KEY=VALUE...")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
@click.option("--env-dir", default=".envault", show_default=True)
def set_cmd(env_key, pairs, passphrase, env_dir):
    """Set tags on ENV_KEY. Provide tags as KEY=VALUE pairs."""
    vault = make_vault(passphrase, env_dir)
    tag_dict = {}
    for pair in pairs:
        if "=" not in pair:
            raise click.BadParameter(f"Expected KEY=VALUE, got: {pair}")
        k, v = pair.split("=", 1)
        tag_dict[k] = v
    set_tags(vault.backend, env_key, tag_dict)
    click.echo(f"Tags set on '{env_key}': {tag_dict}")


@tags.command("get")
@click.argument("env_key")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
@click.option("--env-dir", default=".envault", show_default=True)
def get_cmd(env_key, passphrase, env_dir):
    """Show tags for ENV_KEY."""
    vault = make_vault(passphrase, env_dir)
    tag_dict = get_tags(vault.backend, env_key)
    if not tag_dict:
        click.echo(f"No tags for '{env_key}'.")
    else:
        for k, v in tag_dict.items():
            click.echo(f"  {k}={v}")


@tags.command("rm")
@click.argument("env_key")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
@click.option("--env-dir", default=".envault", show_default=True)
def rm_cmd(env_key, passphrase, env_dir):
    """Remove all tags from ENV_KEY."""
    vault = make_vault(passphrase, env_dir)
    delete_tags(vault.backend, env_key)
    click.echo(f"Tags removed from '{env_key}'.")


@tags.command("list")
@click.option("--filter", "filter_tag", default=None, help="Filter by tag key.")
@click.option("--value", "filter_value", default=None, help="Filter by tag value (requires --filter).")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
@click.option("--env-dir", default=".envault", show_default=True)
def list_cmd(filter_tag, filter_value, passphrase, env_dir):
    """List env keys that have tags."""
    vault = make_vault(passphrase, env_dir)
    keys = list_tagged(vault.backend, filter_tag, filter_value)
    if not keys:
        click.echo("No tagged keys found.")
    else:
        for k in keys:
            click.echo(k)
