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

# Finance Dashboard Project

## Overview
This project is a finance dashboard built using Python (Flask) for the backend, React/JavaScript for the frontend, and the Plaid API for financial data integration. The application enables users to link financial accounts, view transactions, analyze spending trends, and manage settings through a web interface.

## Features
- **Account Linking**: Securely link financial accounts via the Plaid API.
- **Transaction Viewing**: Display detailed transaction data with filters and search.
- **Spending Analysis**: Visualize cash flow and spending trends over time.
- **Custom Themes**: Users can switch between multiple themes for the dashboard.
- **Data Persistence**: Transactions and linked account data are stored in JSON files and an SQLite database.

---

## Project Structure

### 1. Backend
- **Framework**: Flask
- **Key Files**:
  - `MainDash.py`: Core Flask application handling routes, data processing, and API integrations.
  - `config.py`: Configuration file for directories, environment variables, logging, and file management.
  - `plaid_utils.py`: Helper functions to interact with the Plaid API (e.g., generating link tokens, fetching account data).
  - `sql_utils.py`: Database models and functions for managing transaction and refresh data.
- **Dependencies**:
  - Flask
  - SQLAlchemy
  - Python Plaid library

### 2. Frontend
- **Languages**: HTML, CSS, JavaScript
- **Key Files**:
  - `transactions.html`: Displays transaction data in a searchable, sortable table.
  - `dashboard.html`: Home page with visualizations for cash flow and reminders.
  - `settings.html`: Settings page for theme management.
  - `accounts.html`: Account management interface.
  - `error.html`: Error page for handling unlinked accounts or data loading failures.
- **Scripts**:
  - `link.js`: Handles Plaid account linking workflow.
  - `accounts.js`: Manages account rendering, refreshing, and linking.
  - `settings.js`: Dynamically updates themes without requiring a page reload.
  - `finance-dashroad.js`: Handles visualizations like the cash flow chart and table updates.

### 3. Data Files
- **Location**: `data/`
  - `LinkAccounts.json`: Stores linked account details.
  - `LinkItems.json`: Stores item-level data from Plaid.
  - `usbank_transactions.json`: Example transaction data.
- **Temporary Files**: `temp/`
  - `ResponseTransactions.json`: Stores temporary transaction responses.
  - `TransactionRefresh.json`: Stores temporary transaction refresh data.

---

## Setup

### 1. Environment Configuration
Copy the provided `.env` file and fill in your Plaid API credentials:
```env
CLIENT_ID=your-client-id
SECRET_KEY=your-secret-key
PLAID_ENV=production
PRODUCTS="transactions"
PHONE_NBR="+1 123 4567890"
```

### 2. Install Dependencies
Install Python packages:
```bash
pip install -r requirements.txt
```

Install Node.js dependencies if required for the frontend:
```bash
npm install
```

### 3. Database Initialization
Run the following command to initialize the SQLite database:
```bash
python -c "from sql_utils import init_db; init_db()"
```

### 4. Running the Application
Start the Flask server:
```bash
python MainDash.py
```
Access the application at `http://localhost:5000`.

---

## Key Functionalities

### Account Linking
1. Navigate to the **Accounts** page.
2. Click the **Link New Account** button.
3. Complete the Plaid linking process.

### Transactions
1. Navigate to the **Transactions** page.
2. Use filters, search, and sort to view and analyze transactions.

### Spending Trends
1. View visualizations on the **Dashboard** page.
2. Analyze monthly income vs. spending and overall cash flow.

### Theme Management
1. Navigate to the **Settings** page.
2. Select a theme from the dropdown menu and apply it.

---

## Files and Directories
### Python Files
- **`config.py`**: Sets up logging, environment variables, and file paths.
- **`plaid_utils.py`**: Contains Plaid API integration logic (e.g., generating tokens, fetching data).
- **`sql_utils.py`**: Models and database functions for managing transaction and refresh data.
- **`MainDash.py`**: Main entry point for the Flask application.

### HTML Templates
- **`templates/dashboard.html`**: Displays dashboard visualizations.
- **`templates/transactions.html`**: Table for transaction data.
- **`templates/accounts.html`**: Account management page.
- **`templates/settings.html`**: Theme settings page.
- **`templates/error.html`**: Error handling page.

### JavaScript Files
- **`static/scripts/accounts.js`**: Manages account linking and refresh logic.
- **`static/scripts/link.js`**: Plaid Link initialization.
- **`static/scripts/settings.js`**: Handles theme switching.
- **`static/scripts/finance-dashroad.js`**: Renders charts and updates transaction tables.

### JSON Data
- **`data/LinkAccounts.json`**: Contains linked account metadata.
- **`data/LinkItems.json`**: Contains linked item metadata.
- **`data/Transactions.json`**: Stores transaction data.

---

### Logs
Logs are stored in the `logs/` directory. Check `testing.log` for application errors and API responses.

---

## Future Enhancements
- Get the loading of transactions completed.
- Detailed categorical spending analysis
- Cash flow analysis
- (feel free to add some ideas here)

---

## Acknowledgments
- **Plaid API**: For enabling account linking and transaction data retrieval.
- **Flask**: Lightweight backend framework.
- **Chart.js**: For interactive visualizations.

---

## License
This project is licensed under the MIT License. See `LICENSE` for more details.

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

