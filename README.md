# pyNance-Dash

## Quickstart

```
# Clone project
git clone https://github.com/braydio/pyNance.git

# Set up python environment at root: /pyNance/.venv
python -m venv .venv

.venv/Scripts/activate # Windows
source .venv/bin/activate # virgin-ized

pip install -r requirements.txt

# Everything will be run from the root dir pyNance/. for the time being

cp Dash/example.env Dash/.env

@ Run the script to start Flask server:
python Dash/MainDash.py
```

This starts a Flask server at localhost:5006. You can change the port at the bottom of MainDash.py

Use a web browser to navigate to the ip address listed in the terminal and check out my sick website.

## End Quickstart

### Current Development State (1/24)
- Deleting /Plaid/ (or removing everything in it for now) since the app is fully contained in /Dash/

### Current Development State (1/21) 
- Plaid Link is ready. Saves account link tokens to data/
- Run python CheckLinks.py to consolidate all link tokens to a text file
- Time for the dashroad

### Current Development State (1/20) 
- Should be able to run from pyNance/Plaid

    Create python .venv at pyNance/Plaid using Plaid/requirements.txt
    Make a .env and fill out per example.env
    Run LinkPlaid.py to initiate the Plaid Link

### Current Development State (1/18) 
- Developing Plaid Link in pyNance/Plaid/deploy

Currently the account link process happens in Plaid. So for the sake of file paths etc. cd into pyNance/Plaid before running link scripts.

    I believe I copied deploy to Plaid. I added CheckLinks.py to Plaid/data. cd into Plaid/data and run 'python CheckLinks.py' to see active Plaid Link Items

    Actually immedate state is in pyNance/Plaid/deploy, but will copy deploy to Plaid.

# Plaid Financial Dashboard API

This project is a Flask-based API for integrating with the Plaid API to manage and refresh financial data such as transactions and account details. It includes dynamic handling of date ranges for transaction fetching and supports frontend interaction with a React or vanilla JavaScript-based UI.

## Features
- Fetch transaction data dynamically using Plaid's API.
- Support for handling large transaction datasets.
- Automatic fallback for date ranges (e.g., last successful update or 60 days ago).
- JSON-based data storage for linked accounts and items.
- Graceful handling of errors (e.g., missing files, invalid data).
- JavaScript frontend integration for triggering data refreshes.

---

## Slower Quickstart

### Prerequisites
- Python 3.8+
- Plaid Developer account
- Plaid API credentials (`client_id` and `secret`)
- Flask
- Docker (optional for containerized deployment)

### Setup

1. Clone the repository:
   ```bash
   git clone http://github.com/braydio/pyNance.git
   cd pyNance
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   Create a `.env` file in the root directory and add your Plaid API credentials:
   ```env
   PLAID_CLIENT_ID=<your-client-id>
   PLAID_SECRET=<your-secret>
   PLAID_BASE_URL=https://sandbox.plaid.com  # Use Sandbox, Development, or Production URL
   ```

4. Run the Flask server:
   ```bash
   python Dash/MainDash.py
   ```
---

## API Endpoints

### `/refresh_account`
**Method**: `POST`

**Description**: Refreshes account data and transactions for a specified `item_id`. Automatically determines the appropriate date range.

**Request Body**:
```json
{
  "item_id": "<institution_item_id>"
}
```

**Response**:
```json
{
  "status": "success",
  "start_date": "<start_date>",
  "end_date": "<end_date>",
  "transactions": [ ... ],
  "total_transactions": <number>
}
```

---

## Directory Structure

```plaintext
Dash
├── .pre-commit-config.yaml        # Configuration for pre-commit hooks to enforce code formatting and linting.
├── .env                           # Contains environment variables such as API keys and database configurations.
├── example.env                    # Example environment configuration for local setup.
├── config.py                      # Configuration file for global settings and reusable constants.
├── MainDash.py                    # Main application script for handling routes and core application logic. 
├── plaid_utils.py                 # Utilities for interacting with the Plaid API.
├── sql_utils.py                   # Utilities for handling SQL database operations.
│
├── data                           # Directory for application data and backups.
│   ├── ExampleAccounts.json            # Sample data file for accounts, used for testing or demos.
│   ├── ExampleItems.json               # Sample data file for items, used for testing or demos.
│   ├── LinkAccounts.json               # Stores linked account data.
│   ├── LinkAccounts.json.bak           # Backup file for linked account data.
│   ├── LinkItems.json                  # Stores linked item data.
│   ├── LinkItems.json.bak              # Backup file for linked item data.
│   └── Transactions.json               # Stores transaction data to be loaded in.
│
├── templates                      # HTML templates for the application's frontend.
│    ├── accounts.html                  # HTML template for the accounts page.
│    ├── dashboard.html                 # HTML template for the main dashboard.
│    ├── error.html                     # HTML template for displaying error messages.
│    ├── settings.html                  # HTML template for the settings page.
│    └── transactions.html              # HTML template for displaying transactions.

├── static                         # Static assets for the frontend (CSS, JS, themes).
│   ├── css                             # Directory for CSS stylesheets.
│   │   ├── base.css                    # Base styles applied across the application.
│   │   ├── forms.css                   # Styles for forms and input elements.
│   │   ├── header.css                  # Styles for the header section.
│   │   ├── sections.css                # Styles for main content sections.
│   │   └── visuals.css                 # Styles for visual elements and charts.
│   ├── scripts                    # Directory for JavaScript files.
│   │   ├── accounts.js                 # JavaScript for account management functionality.
│   │   ├── finance-dashroad.js         # Core JavaScript for the dashboard functionality.
│   │   ├── link.js                     # JavaScript for managing Plaid Link integration.
│   │   └── settings.js                 # JavaScript for handling theme and settings interactions.
│   └── themes                     # Directory for theme-specific CSS files.
│       ├── current_theme.txt           # Tracks the currently active theme.
│       └── default.css                 # Default application theme.
│
├── logs                           # Directory for log files and debugging information.
│   ├── dashroad.log                    # Main log file for the application.
│   ├── logs_init                       # Log initialization files or additional logs.
│   ├── testing.log                     # Log file for testing-related output.
│   └── testing copy.log                # Backup or copy of testing logs.
│
└── temp                           # Directory for temporary files and API responses.
    ├── exchange_response.json          # Temporary storage for API exchange responses.
    ├── item_get_response.json          # Temporary storage for item retrieval responses.
    ├── link_session.json               # Stores temporary session data for linking accounts.
    └── public_token.txt                # Stores temporary public tokens for API interactions.

```

---

## JavaScript Integration

The frontend communicates with the backend via the `/refresh_account` endpoint. Below is an example function for refreshing institution data:

```javascript
function refreshInstitution(institutionId, institutionName) {
    const refreshButton = document.querySelector(`button[data-institution-id="${institutionId}"]`);
    refreshButton.disabled = true;
    refreshButton.textContent = "Refreshing...";

    fetchData("/refresh_account", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            item_id: institutionId,
        }),
    })
        .then((response) => {
            refreshButton.disabled = false;
            refreshButton.textContent = "Refresh";
            if (response.status === "success") {
                alert(`Institution "${institutionName}" refreshed successfully!`);
            } else {
                alert(`Error refreshing "${institutionName}": ${response.error}`);
            }
        })
        .catch((error) => {
            refreshButton.disabled = false;
            refreshButton.textContent = "Refresh";
            alert(`Error refreshing "${institutionName}": ${error.message}`);
        });
}
```

---

## Troubleshooting

### Common Errors
1. **"Missing item_id"**:
   Ensure the frontend sends the `item_id` as part of the request payload.

2. **"No access token found for item ID"**:
   Verify that `linked_accounts.json` contains a valid `access_token` for the specified `item_id`.

3. **Plaid API Request Errors**:
   Check that your Plaid credentials are correct and the base URL corresponds to the right environment (Sandbox, Development, or Production).

---

## License
This project is licensed under the MIT License. See the LICENSE file for details.

