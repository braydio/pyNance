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
   python pyNance/MainDash.py
   ```

5. (Optional) Run the server with Docker:
   ```bash
   docker compose up --build -d
   docker run -p 
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
├── app.py                 # Main Flask application.
├── helper_utils.py        # Utility functions for file and JSON handling.
├── plaid_utils.py         # Helper functions for interacting with the Plaid API.
├── routes.py              # API route handlers.
├── templates/
│   ├── dashboard.html     # HTML for the dashboard view.
│   ├── accounts.html      # HTML for accounts view.
│   ├── transactions.html  # HTML for transactions view.
│   └── settings.html      # HTML for settings page.
├── static/
│   ├── finance-dashroad.js # JavaScript for dynamic frontend interactions.
│   ├── accounts.js         # JavaScript for account management.
│   └── settings.js         # JavaScript for app settings.
├── .env                   # Environment variables (not committed to version control).
├── Dockerfile             # Configuration for containerized deployment.
├── requirements.txt       # Python dependencies.
├── linked_items.json      # Storage for linked Plaid items.
├── linked_accounts.json   # Storage for account details and access tokens.
├── refreshed_transactions.json # Output file for refreshed transaction data.
└── README.md              # Project documentation.
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

