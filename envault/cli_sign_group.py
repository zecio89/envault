"""Attach the sign command group to the main CLI."""
from __future__ import annotations

from envault.cli_sign import sign


def attach_sign(cli_group):
    """Register the `sign` sub-group onto *cli_group*.

    Call this from the main cli setup, e.g.::

        from envault.cli_sign_group import attach_sign
        attach_sign(cli)
    """
    cli_group.add_command(sign)
