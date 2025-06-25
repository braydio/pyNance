#!/usr/bin/env python3
"""
Script to add missing columns to main_dash.db.

Usage:
  cd backend && python scripts/update_db_schema.py
"""
import sqlite3
import sys
from pathlib import Path

# Ensure the backend 'app' package is on the path
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))

from app.config.constants import DATABASE_NAME
from app.config.paths import DIRECTORIES


def main():
    db_path = DIRECTORIES["DATA_DIR"] / DATABASE_NAME
    if not db_path.exists():
        print(f"Error: Database file not found at {db_path}")
        sys.exit(1)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    statements = [
        # Accounts table: add FK to institutions
        "ALTER TABLE accounts ADD COLUMN institution_db_id INTEGER;",
        "CREATE INDEX IF NOT EXISTS ix_accounts_institution_db_id ON accounts (institution_db_id);",
        # PlaidAccounts: add missing columns
        "ALTER TABLE plaid_accounts ADD COLUMN plaid_institution_id VARCHAR(128);",
        "ALTER TABLE plaid_accounts ADD COLUMN institution_db_id INTEGER;",
        "CREATE INDEX IF NOT EXISTS ix_plaid_accounts_institution_db_id ON plaid_accounts (institution_db_id);",
        # TellerAccounts: add missing columns
        "ALTER TABLE teller_accounts ADD COLUMN teller_institution_id VARCHAR(128);",
        "ALTER TABLE teller_accounts ADD COLUMN institution_db_id INTEGER;",
        "CREATE INDEX IF NOT EXISTS ix_teller_accounts_institution_db_id ON teller_accounts (institution_db_id);",
    ]
    for stmt in statements:
        try:
            cursor.execute(stmt)
            print(f"Executed: {stmt}")
        except sqlite3.OperationalError as e:
            print(f"Skipped (likely exists): {stmt} -> {e}")
    conn.commit()
    conn.close()
    print("Schema update complete.")


if __name__ == "__main__":
    main()
