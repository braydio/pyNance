# Checks LinkAccounts.json and LinkItems.json to provide a summary
# Of the currently active Plaid items and saves to ActiveLinks.txt

import json

def load_json(file_path):
    """Utility function to load JSON data from a file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}

# Function to save the output to a file
def save_results_to_file(file_path, content):
    """Save the processed results to a text file."""
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Results saved to {file_path}")
    except Exception as e:
        print(f"Error saving to {file_path}: {e}")

# Load data from the provided JSON files
link_accounts = load_json('LinkAccounts.json')
link_items = load_json('LinkItems.json')

# Process and display linked banks and accounts
output = []
output.append("Linked Banks and Accounts:")
output.append("=" * 40)

institution_items = {}  # Store institution details by item_id

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
    output.append("-" * 40)

output.append("Done.")

# Join the results into a single string
results_str = "\n".join(output)

# Define the output file path
output_file_path = r"C:\Users\chaff\Projects\pyNance\Plaid\deploy\data\ActiveLinks.txt"

# Save the results to the file
save_results_to_file(output_file_path, results_str)
