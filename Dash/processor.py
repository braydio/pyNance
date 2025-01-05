import json
import re


def process_plaid_logs(log_file_path):
    item_info = {}
    accounts_info = {}

    with open(log_file_path, 'r') as f:
        logs = f.read()

    # Extract item info from /item/get
    item_match = re.search(r'"institution_name": "(.*?)".*?"item_id": "(.*?)".*?"products": \[(.*?)\]', logs, re.DOTALL)
    if item_match:
        item_info = {
            "institution_name": item_match.group(1),
            "item_id": item_match.group(2),
            "products": [p.strip().strip('"') for p in item_match.group(3).split(",")]
        }

    # Extract accounts info from /accounts/get
    account_matches = re.finditer(r'"account_id": "(.*?)".*?"name": "(.*?)".*?"type": "(.*?)".*?"subtype": "(.*?)".*?"balances": {(.*?)}', logs, re.DOTALL)
    for match in account_matches:
        account_id = match.group(1)
        accounts_info[account_id] = {
            "account_name": match.group(2),
            "type": match.group(3),
            "subtype": match.group(4),
            "balances": json.loads("{" + match.group(5) + "}")
        }

    # Save item_info.json
    with open("item_info.json", "w") as f:
        json.dump(item_info, f, indent=2)
    print("Saved item info to item_info.json")

    # Save accounts_info.json
    with open("accounts_info.json", "w") as f:
        json.dump(accounts_info, f, indent=2)
    print("Saved accounts info to accounts_info.json")

# Example usage
process_plaid_logs("plaid_api.log")

