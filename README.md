# pyNance-Dash
> Quickstart moved to end

### Current Development State (1/26)
- Plaid Link is fully integrated. SQL Server initialized. 
    - I'm using DB Browser for SQL DB Mgmt
    - Currently all API responses are saved as JSON files in Dash/data where they are loaded by the handlers.
        - See the MainDash.py backend for the account refresh and account link logic - it's easier to follow IMO.
    - TO-DO includes finish polished the Account Refresh logic, passing the data correctly to the DB.
        - Not sure if we want to use SQL and ditch the JSON logic, or use JSON for the recent activity and SQL for older transactions.

We could probably work on a more robust workflow. I'll make a second markdown file with version notes / working notes in the root dir. Probably call it something like README_DevNotes.md

---
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

### 3. Database Initialization
The SQLite Database is initialized in sql_utils.py, and imported to the main python module. 
```python
if __name__ == "__main__":
    logger.info("Starting Flask application, initializing SQL Database.")
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
```

### 4. Running the Application
Start the Flask server:
```bash
python Dash/MainDash.py
```
Access the application at the Local IP Address of you host machine port :5000

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

# Some example code from the real life code: 

``` HTML
                <!-- Link New Account Button The --> 
                <button id="link-button" onclick="fetchLinkToken()">Link New Account</button>
            </div>
```

### JavaScript Integration
- The frontend communicates with the backend via the `/refresh_account` endpoint. Below is a JS (front end) example for handling to Plaid Link functionality:

```javascript
// Plaid Link functionality
function initializePlaidLink() {
    // Fetch a link token from the backend
    fetchData("/get_link_token")
        .then((data) => {
            // Check if the link token was successfully received
            if (data.link_token) {
                // Create the Plaid Link handler using the received link token
                const handler = Plaid.create({
                    token: data.link_token, // The link token obtained from the backend

                    // Callback triggered upon successful account linking
                    onSuccess: function (public_token, metadata) {
                        // Log the public token received from Plaid
                        console.log("Public Token:", public_token);

                        // Send the public token to the backend to exchange it for an access token
                        fetchData("/save_public_token", {
                            method: "POST", // HTTP method for sending the data
                            headers: { "Content-Type": "application/json" }, // Set the request headers
                            body: JSON.stringify({ public_token }), // Include the public token in the request body
                        })
                            .then((response) => {
                                // Check if an access token was successfully received
                                if (response.access_token) {
                                    // Update the status in the UI to indicate success
                                    statusContainer.textContent = "Access token received!";
                                } else {
                                    // Log the error if the access token wasn't saved successfully
                                    console.error("Error saving public token:", response.error);
                                    // Update the status in the UI to indicate failure
                                    statusContainer.textContent = "Failed to save public token.";
                                }
                            })
                            .catch((error) => {
                                // Handle any errors that occur during the save public token request
                                console.error("Error saving public token:", error);
                                statusContainer.textContent = "An error occurred.";
                            });
                    },

                    // Callback triggered when the user exits the Plaid Link flow
                    onExit: function (err, metadata) {
                        // Check if the user exited due to an error
                        if (err) {
                            // Update the status in the UI to indicate an error
                            statusContainer.textContent = "User exited with an error.";
                        } else {
                            // Update the status in the UI to indicate a normal exit
                            statusContainer.textContent = "User exited without error.";
                        }
                    },
                });

                // Attach the Plaid Link handler to a button for user interaction
                linkButton.onclick = () => handler.open();
            } else {
                // Handle the case where the link token couldn't be fetched
                statusContainer.textContent = "Error fetching link token.";
            }
        })
        .catch((error) => {
            // Handle any errors that occur while fetching the link token
            statusContainer.textContent = "Error initializing Plaid Link.";
        });
}

```

---

### Python Flask
- The Flask app in MainDash.py handles the back end routes.

```python
# Link token routes
@app.route("/save_public_token", methods=["POST"])
def save_public_token():
    try:
        # Check if the request contains JSON data
        if not request.is_json:
            logger.error("Invalid request: Content-Type must be application/json")
            return (
                jsonify({"error": "Invalid Content-Type. Must be application/json."}),
                400,
            )

        # Parse the JSON payload from the request
        data = request.get_json()
        logger.debug(f"Received POST data: {json.dumps(data, indent=2)}")

        # Extract the public token from the request data
        public_token = data.get("public_token")
        if public_token:
            # Ensure the temporary directory exists
            ensure_directory_exists(TEMP_DIR)

            # Save the public token to a file for temporary storage
            with open(os.path.join(TEMP_DIR, "public_token.txt"), "w") as f:
                f.write(public_token)
            logger.info("Public token saved to file")

            # Exchange the public token for an access token
            access_token = exchange_public_token(public_token)
            if access_token:
                # Retrieve item metadata using the access token
                item_id, institution_name = get_item_info(access_token)
                if item_id:
                    # Save initial account data to the database or files
                    save_initial_account_data(access_token, item_id)
                    logger.info(
                        f"Linked to {institution_name} successfully with item ID: {item_id}"
                    )

                    # Return a success response with the access token and institution details
                    return (
                        jsonify(
                            {
                                "message": f"Linked to {institution_name} successfully",
                                "access_token": access_token,
                            }
                        ),
                        200,
                    )
                else:
                    # Log and return an error if item metadata retrieval fails
                    logger.error("Failed to retrieve item metadata")
                    return jsonify({"error": "Failed to retrieve item metadata"}), 400

            else:
                # Log and return an error if public token exchange fails
                logger.error("No public token provided")
                return jsonify({"error": "No public token provided"}), 400

    except json.JSONDecodeError as jde:
        # Handle JSON decoding errors and log the details
        logger.error(f"JSON decode error: {str(jde)}")
        return jsonify({"error": "Invalid JSON payload", "details": str(jde)}), 400

    except Exception as e:
        # Handle unexpected errors and log the details
        logger.error(f"Error processing public token: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Server error while processing public token",
                    "details": str(e),
                }
            ),
            500,
        )
```


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

# Run the script to start Flask server:
python Dash/MainDash.py
```

This starts a Flask server at localhost:5000. You can change the port at the bottom of MainDash.py

Use a web browser to navigate to the ip address listed in the terminal and to see the riced out website.

## End Quickstart
