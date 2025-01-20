# Checks LinkAccounts.json and LinkItems.json to provide a summary
# Of the currently active Plaid items and saves to 
# CheckedAccounts.txt and CheckedInstitutions.txt

import json

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
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Results saved to {file_path}")
    except Exception as e:
        print(f"Error saving to {file_path}: {e}")

# Load data from LinkAccounts.json and LinkItems.json
link_accounts = load_json('LinkAccounts.json')
link_items = load_json('LinkItems.json')

# First File: Institution Name and Billed Products
institution_name = link_items.get("item", {}).get("institution_name", "Unknown Institution")
billed_products = link_items.get("item", {}).get("billed_products", [])

first_file_content = f"Institution: {institution_name}\nBilled Products: {', '.join(billed_products)}\n"
save_results_to_file(r"C:\Users\chaff\Projects\pyNance\Plaid\deploy\data\CheckedInstitutions.txt", first_file_content)

# Second File: Enhanced Output with last_successful_update
output = []
output.append("Linked Banks and Accounts:")
output.append("=" * 40)

institution_items = {}  # Store institution details by item_id
last_successful_update = link_items.get("status", {}).get("transactions", {}).get("last_successful_update", "N/A")

# Extract institution information from LinkItems
if "item" in link_items:
    institution_items[link_items["item"]["item_id"]] = link_items["item"]["institution_name"]

# Display linked accounts grouped by institution
for account_id, account_details in link_accounts.items():
    item_id = account_details.get("item_id")
    institution_name = institution_items.get(item_id, "Unknown Institution")
    
    output.append(f"Institution: {institution_name}")
    output.append(f"  - Account Name: {account_details['account_name']}")
    output.append(f"    Type: {account_details['type']} ({account_details['subtype']})")
    output.append(f"    Current Balance: {account_details['balances']['current']} {account_details['balances'].get('iso_currency_code', 'Unknown Currency')}")
    output.append(f"    Last Successful Update: {last_successful_update}")
    output.append("-" * 40)

output.append("Done.")

# Save to file
results_str = "\n".join(output)
save_results_to_file(r"C:\Users\chaff\Projects\pyNance\Plaid\deploy\data\CheckedAccounts.txt", results_str)
