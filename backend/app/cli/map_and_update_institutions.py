"""CLI utilities for mapping and updating Plaid institutions."""

import csv
from pathlib import Path

from app.config import logger
from app.extensions import db
from app.helpers.path_utils import resolve_data_path
from app.models import Institution, PlaidAccount


# --- Step 1: Build mapping from institution names to DB IDs ---
def get_institution_name_to_id():
    return {inst.name.strip().lower(): inst.id for inst in Institution.query.all()}


# --- Step 2: Read Plaid institutions CSV ---
def load_plaid_institutions(path: str | Path = "PlaidInstitutions.csv"):
    """Load Plaid institution mappings from a CSV file.

    Args:
        path: CSV filename or path relative to the backend data directory.

    Returns:
        A mapping of lowercase institution names to Plaid institution IDs.
    """
    plaid_map = {}
    resolved_path = resolve_data_path(path)
    with open(resolved_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Map name (lowercased) to Plaid institution_id
            plaid_map[row["name"].strip().lower()] = row["plaid_institution_id"]
    return plaid_map


def update_plaid_accounts(institution_name_to_id, plaid_name_to_id):
    updated = 0
    # For each PlaidAccount, look up the institution by name
    for pa in PlaidAccount.query.all():
        # Find which institution this account should map to
        # This assumes pa.plaid_institution_id is set, and you have PlaidInstitutions.csv with names
        for name, plaid_id in plaid_name_to_id.items():
            if pa.plaid_institution_id == plaid_id:
                institution_id = institution_name_to_id.get(name)
                if institution_id and pa.institution_db_id != institution_id:
                    pa.institution_db_id = institution_id
                    updated += 1
    db.session.commit()
    logger.info("Updated %d plaid_accounts rows.", updated)


def main():
    institution_name_to_id = get_institution_name_to_id()
    plaid_name_to_id = load_plaid_institutions()

    update_plaid_accounts(institution_name_to_id, plaid_name_to_id)


if __name__ == "__main__":
    main()
