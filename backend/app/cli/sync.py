# cli.py
import click
from app.helpers.account_refresh_dispatcher import refresh_all_accounts


@click.command("sync-accounts")
def sync_accounts():
    """Run account sync manually from CLI."""
    logger.warning("This module is not build out.")
