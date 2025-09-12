"""CLI: Reconcile saved Plaid Items against live Plaid API.

Usage examples:

- flask --app backend.run reconcile-plaid-items
- flask --app backend.run reconcile-plaid-items --verbose

This command:
- Collects distinct item_ids from local storage (PlaidItem, PlaidAccount)
- Resolves an access_token for each item_id
- Calls Plaid /item/get to verify the Item exists and report status
- Prints a summary and any discrepancies (invalid/expired/missing tokens)

Note: Plaid does not expose a global "list all items" API for a client.
This reconciliation verifies each locally-known Item with Plaid and flags
problems. To detect Items existing in Plaid that we do not know about,
compare with a dashboard export separately (future enhancement).
"""

from __future__ import annotations

import click
from flask.cli import with_appcontext

from app.config import logger, plaid_client
from app.models import PlaidAccount, PlaidItem
from plaid.model.item_get_request import ItemGetRequest


@click.command("reconcile-plaid-items")
@click.option("--verbose", is_flag=True, help="Print per-item details")
@with_appcontext
def reconcile_plaid_items(verbose: bool) -> None:
    if plaid_client is None:
        click.echo("Plaid client is not configured. Check backend/.env.")
        return

    # Build a map of item_id -> access_token (prefer PlaidItem token if present)
    item_tokens: dict[str, str] = {}

    # Prefer secure table first
    for pi in PlaidItem.query.all():
        if pi.item_id and pi.access_token:
            item_tokens[pi.item_id] = pi.access_token

    # Fallbacks from PlaidAccount (one token per item)
    rows = (
        PlaidAccount.query.with_entities(PlaidAccount.item_id, PlaidAccount.access_token)
        .filter(PlaidAccount.item_id.isnot(None))
        .filter(PlaidAccount.item_id != "")
        .all()
    )
    for item_id, token in rows:
        if item_id and token and item_id not in item_tokens:
            item_tokens[item_id] = token

    if not item_tokens:
        click.echo("No Plaid items found locally.")
        return

    live_ok = 0
    errors: list[tuple[str, str]] = []  # (item_id, error)

    for item_id, token in item_tokens.items():
        try:
            req = ItemGetRequest(access_token=token)
            resp = plaid_client.item_get(req)
            status = getattr(resp.item, "error", None)
            if verbose:
                click.echo(f"✔ {item_id} OK (institution={getattr(resp.item, 'institution_id', 'n/a')})")
            live_ok += 1
        except Exception as e:  # Plaid ApiException or transport error
            msg = getattr(e, "body", str(e)) or str(e)
            errors.append((item_id, msg))
            if verbose:
                click.echo(f"✖ {item_id} ERROR: {msg}")

    click.echo("")
    click.echo("Reconciliation Summary")
    click.echo("---------------------")
    click.echo(f"Local distinct Items: {len(item_tokens)}")
    click.echo(f"Verified with Plaid:  {live_ok}")
    click.echo(f"Errors/Unverified:     {len(errors)}")

    if errors:
        click.echo("")
        click.echo("Problem Items:")
        for iid, err in errors:
            # Keep first line short if Plaid returns JSON
            msg = str(err).splitlines()[0][:200]
            click.echo(f"- {iid}: {msg}")

