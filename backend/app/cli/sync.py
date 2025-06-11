# cli.py
import click
from app.helpers.refresh_dispatcher import refresh_all_accounts
from flask.cli import with_appcontext


@click.command("sync-accounts")
@with_appcontext
def sync_accounts():
    """Run account sync manually from CLI."""
    click.echo("🔄 Starting account sync...")
    refresh_all_accounts()
    click.echo("✅ Account sync complete.")
