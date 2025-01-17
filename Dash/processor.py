import json
import re
import argparse
import os
import shutil
import logging

# Set up detailed logging
logging.basicConfig(filename="./logs/processor_debug.log", level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def read_log_file(log_file_path):
    """ Reads and returns the contents of the log file. """
    if not os.path.exists(log_file_path):
        raise FileNotFoundError(f"Log file not found: {log_file_path}")
    with open(log_file_path, 'r') as f:
        content = f.read()
    logging.debug(f"Read log file: {log_file_path} with length {len(content)} characters.")
    return content

def extract_item_info(logs):
    """ Extracts institution and item data from the logs. """
    item_info = {}
    item_match = re.search(r'"institution_name": "(.*?)".*?"item_id": "(.*?)".*?"products": \[(.*?)\]', logs, re.DOTALL)
    if item_match:
        item_info = {
            "institution_name": item_match.group(1),
            "item_id": item_match.group(2),
            "products": [p.strip().strip('"') for p in item_match.group(3).split(",")]
        }
        logging.debug(f"Extracted item info: {item_info}")
    else:
        logging.warning("No item information found in logs.")
    return item_info

def extract_accounts_info(logs):
    """ Extracts account-related information from the logs. """
    accounts_info = {}
    account_matches = re.finditer(r'"account_id": "(.*?)".*?"name": "(.*?)".*?"type": "(.*?)".*?"subtype": "(.*?)".*?"balances": {(.*?)}', logs, re.DOTALL)
    for match in account_matches:
        account_id = match.group(1)
        try:
            balances = json.loads("{" + match.group(5) + "}")
        except json.JSONDecodeError:
            logging.error(f"Failed to parse balances for account {account_id}")
            continue
        account_data = {
            "account_name": match.group(2),
            "type": match.group(3),
            "subtype": match.group(4),
            "balances": balances
        }
        if account_id in accounts_info:
            logging.warning(f"Duplicate account ID detected: {account_id}. Merging balances.")
        accounts_info[account_id] = account_data
        logging.debug(f"Extracted account info for account_id {account_id}: {account_data}")
    if not accounts_info:
        logging.warning("No accounts information found in logs.")
    return accounts_info

def save_to_file(filename, new_data):
    """ Saves data to a JSON file, merging with existing data if any. """
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    # Load existing data if file exists
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                existing_data = json.load(f)
                logging.debug(f"Loaded existing data from {filename}: {existing_data}")
            except json.JSONDecodeError:
                logging.error(f"JSON decode error in {filename}. Overwriting with new data.")
                existing_data = {}
    else:
        existing_data = {}

    # Merge the new data with existing data based on type
    if isinstance(existing_data, dict) and isinstance(new_data, dict):
        for key, value in new_data.items():
            if key in existing_data and isinstance(existing_data[key], dict) and isinstance(value, dict):
                existing_data[key].update(value)
            else:
                existing_data[key] = value
        logging.debug(f"Merged data for {filename}: {existing_data}")
    else:
        logging.warning(f"Unexpected data format in {filename}, overwriting with new data.")
        existing_data = new_data

    # Save the merged data
    with open(filename, "w") as f:
        json.dump(existing_data, f, indent=2)
    logging.info(f"Saved data to {filename}")

def extract_access_token_info(logs):
    """ Extracts the access token and its related information from the logs. """
    access_token_match = re.search(r'"access_token": "(.*?)"', logs)
    item_match = re.search(r'"institution_name": "(.*?)".*?"item_id": "(.*?)"', logs, re.DOTALL)

    if access_token_match and item_match:
        access_token_info = {
            "access_token": access_token_match.group(1),
            "institution_name": item_match.group(1),
            "item_id": item_match.group(2)
        }
        logging.debug(f"Extracted access token info: {access_token_info}")
        return access_token_info
    logging.warning("No access token information found in logs.")
    return None

def archive_log_file(log_file_path):
    """ Moves the processed log file to an archive folder with a 'processed.' prefix. """
    archive_dir = "./archive"
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)

    log_filename = os.path.basename(log_file_path)
    archived_log_path = os.path.join(archive_dir, f"processed.{log_filename}")

    shutil.move(log_file_path, archived_log_path)
    logging.info(f"Moved log file to {archived_log_path}")

def process_plaid_logs(log_file_path):
    """ Main function to process the Plaid API logs. """
    try:
        logs = read_log_file(log_file_path)
        logging.info(f"Processing log file: {log_file_path}")

        item_info = extract_item_info(logs)
        accounts_info = extract_accounts_info(logs)
        access_token_info = extract_access_token_info(logs)

        if item_info:
            save_to_file("./data/item_info.json", {item_info["item_id"]: item_info})
        if accounts_info:
            save_to_file("./data/accounts_info.json", accounts_info)
        if access_token_info:
            access_token_file = "./data/access_token_info.json"
            save_to_file(access_token_file, {access_token_info["item_id"]: access_token_info})

        # Log final summary of what was saved
        logging.info(f"Summary: Item Info - {bool(item_info)}, Accounts Info - {len(accounts_info)} entries, Access Token Info - {bool(access_token_info)}")

        # Move the log file to the archive after processing
        archive_log_file(log_file_path)

    except Exception as e:
        logging.error(f"Error processing logs: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Plaid API logs and save output to JSON.')
    parser.add_argument('-l', '--log-file', type=str, required=True, help='Path to the Plaid API log file')
    args = parser.parse_args()

    process_plaid_logs(args.log_file)

