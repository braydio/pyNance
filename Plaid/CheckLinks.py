import json
import os

def load_json(file_path):
    """Utility function to load JSON data from a file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}

def save_results_to_file(file_path, content):
    """Save the processed results to a text file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Results saved to {file_path}")
    except Exception as e:
        print(f"Error saving to {file_path}: {e}")

# Load data from LinkAccounts.json and LinkItems.json
link_accounts = load_json('data/LinkAccounts.json')
link_items = load_json('data/LinkItems.json')

# Generate CheckedInstitutions.txt
institutions_output = ["Checked Institutions Summary", "=" * 40]
for item_id, item_details in link_items.items():
    institution_name = item_details.get("institution_name", "Unknown Institution")
    billed_products = item_details.get("products", [])
    last_successful_update = item_details.get("status", {}).get("transactions", {}).get("last_successful_update", "N/A")
    institutions_output.append(f"Institution: {institution_name}")
    institutions_output.append(f"  - Billed Products: {', '.join(billed_products)}")
    institutions_output.append(f"  - Last Successful Update: {last_successful_update}")
    institutions_output.append("-" * 40)

save_results_to_file("data/CheckedInstitutions.txt", "\n".join(institutions_output))

# Generate CheckedAccounts.txt
accounts_output = ["Checked Accounts Summary", "=" * 40]
accounts_by_item = {}

# Group accounts by item_id
for account_id, account_details in link_accounts.items():
    item_id = account_details.get("item_id", "unknown")
    if item_id not in accounts_by_item:
        accounts_by_item[item_id] = []
    accounts_by_item[item_id].append(account_details)

# Create summary for each institution's accounts
for item_id, accounts in accounts_by_item.items():
    institution_name = link_items.get(item_id, {}).get("institution_name", "Unknown Institution")
    accounts_output.append(f"Institution: {institution_name}")
    for account in accounts:
        account_name = account.get("account_name", "Unknown")
        account_type = account.get("type", "Unknown")
        account_subtype = account.get("subtype", "Unknown")
        current_balance = account.get("balances", {}).get("current", "N/A")
        currency = account.get("balances", {}).get("iso_currency_code", "Unknown Currency")
        accounts_output.append(f"  - Account Name: {account_name}")
        accounts_output.append(f"    Type: {account_type} ({account_subtype})")
        accounts_output.append(f"    Current Balance: {current_balance} {currency}")
    accounts_output.append("-" * 40)

save_results_to_file("data/CheckedAccounts.txt", "\n".join(accounts_output))
