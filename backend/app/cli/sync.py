# cli.py
import click
from app import create_app
from app.helpers.account_refresh_dispatcher import refresh_all_accounts


@click.command("sync-accounts")
def sync_accounts():
    """Run account sync manually from CLI."""
    app = create_app()
    with app.app_context():
        click.echo("🔄 Starting account sync...")
        refresh_all_accounts()
        click.echo("✅ Account sync complete.")
