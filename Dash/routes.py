import json
import os
import flask

from utils.helper_utils import logger

# Directory to store themes
THEMES_DIR = 'static/themes'
DEFAULT_THEME = 'brayden_dashroad.css'



# Process transactions for visuals
def process_transactions(transactions_file, accounts_file, link_accounts_file, output_file):
    """
    Reads transactions, accounts, and LinkAccounts JSON files, processes the data, and saves the enriched data.
    """
    try:
        # Load transactions data
        with open(transactions_file, 'r') as tf:
            transactions_data = json.load(tf)
        
        # Load accounts data
        with open(accounts_file, 'r') as af:
            accounts_data = {acc["account_id"]: acc for acc in json.load(af).get("accounts", [])}
        
        # Load LinkAccounts data
        with open(link_accounts_file, 'r') as laf:
            link_accounts_data = json.load(laf)
        
        # Process transactions: Enrich with account info and linked account details
        processed_transactions = []
        for t in transactions_data.get("transactions", []):
            account_id = t["account_id"]
            account_info = accounts_data.get(account_id, {})
            link_account_info = link_accounts_data.get(account_id, {})
            
            processed_transactions.append({
                "date": t["date"],
                "name": t["name"],
                "amount": t["amount"],
                "category": t["category"][0] if t.get("category") else "Unknown",
                "merchant_name": t.get("merchant_name", "Unknown"),
                "account_name": account_info.get("name", link_account_info.get("account_name", "Unknown Account")),
                "account_type": account_info.get("type", link_account_info.get("type", "Unknown")),
                "account_subtype": account_info.get("subtype", link_account_info.get("subtype", "Unknown")),
                "institution_name": link_account_info.get("institution_name", "Unknown Institution"),
                "available_balance": link_account_info.get("balances", {}).get("available", "Unknown"),
                "current_balance": link_account_info.get("balances", {}).get("current", "Unknown"),
                "currency": link_account_info.get("balances", {}).get("iso_currency_code", "Unknown"),
            })
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save the enriched transactions
        with open(output_file, 'w') as f:
            json.dump(processed_transactions, f, indent=4)
        
        return {
            "status": "success",
            "message": f"Processed {len(processed_transactions)} transactions.",
            "output_file": output_file
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Themes
def get_available_themes():
    try:
        themes = [f for f in os.listdir(THEMES_DIR) if f.endswith('.css')]
        return themes
    except FileNotFoundError:
        return []
    
def inject_theme():
    try:
        with open('current_theme.txt', 'r') as f:
            current_theme = f.read().strip()
    except FileNotFoundError:
        current_theme = DEFAULT_THEME

# Themes
def get_available_themes():
    try:
        themes = [f for f in os.listdir(THEMES_DIR) if f.endswith('.css')]
        return themes
    except FileNotFoundError:
        return []