import csv
import json

from app.config import logger
from app.models import Institution, PlaidAccount, TellerAccount
from extensions import db


# --- Step 1: Build mapping from institution names to DB IDs ---
def get_institution_name_to_id():
    return {inst.name.strip().lower(): inst.id for inst in Institution.query.all()}


# --- Step 2: Read Plaid institutions CSV ---
def load_plaid_institutions(path="data/PlaidInstitutions.csv"):
    plaid_map = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Map name (lowercased) to Plaid institution_id
            plaid_map[row["name"].strip().lower()] = row["plaid_institution_id"]
    return plaid_map


# --- Step 3: Read Teller institutions JSON ---
def load_teller_institutions(path="data/TellerInstitutions.json"):
    teller_map = {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
        for entry in data:
            teller_map[entry["name"].strip().lower()] = entry["id"]
    return teller_map


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
    logger.info(f"Updated {updated} plaid_accounts rows.")


def update_teller_accounts(institution_name_to_id, teller_name_to_id):
    updated = 0
    for ta in TellerAccount.query.all():
        for name, teller_id in teller_name_to_id.items():
            if ta.teller_institution_id == teller_id:
                institution_id = institution_name_to_id.get(name)
                if institution_id and ta.institution_db_id != institution_id:
                    ta.institution_db_id = institution_id
                    updated += 1
    db.session.commit()
    logger.info(f"Updated {updated} teller_accounts rows.")


def main():
    institution_name_to_id = get_institution_name_to_id()
    plaid_name_to_id = load_plaid_institutions("PlaidInstitutions.csv")
    teller_name_to_id = load_teller_institutions("TellerInstitutions.json")

    update_plaid_accounts(institution_name_to_id, plaid_name_to_id)
    update_teller_accounts(institution_name_to_id, teller_name_to_id)


if __name__ == "__main__":
    main()
