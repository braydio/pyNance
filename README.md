# pyNance

pyNance is a personal finance dashboard application that integrates with Plaid and Teller APIs to link bank accounts, refresh transactions, and display financial charts. The project is split into a Flask backend and a Vue (Vite) frontend.

## Project Structure

```
pyNance/
├── backend/
│   ├── app/  # Flask application code
│   │   ├── config.py  # Application configuration (loads .env)
│   │   ├── extensions.py  # SQLAlchemy initialization
│   │   ├── models.py  # Database models (Account, Transaction, etc.)
│   │   ├── routes/  # Flask endpoints (plaid.py, teller.py, etc.)
│   │   └── sql/  # SQL utility functions (account_logic.py, etc.)
│   ├── example.env  # Example backend environment file (rename to .env)
│   ├── requirements.txt  # Python dependencies
│   └── run.py  # Entry point for Flask backend
├── frontend/
│   ├── public/  # Public assets for Vue
│   ├── src/
│   │   ├── components/  # Vue components
│   │   │   ├── LinkAccount.vue  # For generating/uploading tokens
│   │   │   ├── RefreshPlaidControls.vue  # Refresh controls for Plaid accounts
│   │   │   ├── RefreshTellerControls.vue  # Refresh controls for Teller accounts
│   │   │   └── ... (other components)
│   │   ├── views/  # Vue views/pages
│   │   ├── App.vue  # Main Vue component
│   │   └── main.js  # Vue entry point
│   ├── package.json  # Node dependencies
│   └── example.env  # Example frontend environment file (rename to .env)
├── venv/  # (Optional) Python virtual environment
└── README.md  # This file
```

## Quickstart

### Prerequisites

- **Python 3.8+** installed  
- **Node.js and npm** installed  
- **Virtualenv for Python** (package dependency isolation)

### Setup Backend

1. **Clone the Repository and Create Virtual Environment**

```bash
git clone https://github.com/braydio/pyNance.git
cd pyNance
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

2. **Install Python Dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure Environment Variables**

Navigate to the backend directory:

```bash
cd backend
```

Copy `example.env` to `.env` and update the values as needed:

```
# Plaid Link API Items
PLAID_CLIENT_ID="YOUR_PLAID_CLIENT_ID"
PLAID_SECRET_KEY="YOUR_PLAID_SECRET_KEY"
PLAID_ENV="development"
PHONE_NBR="+1 910 5541234"
PRODUCTS="transactions"

# Teller dot IO - for Teller Connect
TELLER_APP_ID="YOUR_TELLER_APP_ID"

# Optional dev tokens for Teller (to upload user ID / token pairs without running the teller connect process)
VARIABLE_ENV_TOKEN=""
VARIABLE_ENV_ID=""
```
4. Save your certificates from Teller.io to the certificates directory:

These certificates can be downloaded from the Teller.io account page when you register with their API.

```  
  pyNance/backend/app/certs/certificate.pem
  pyNance/backend/app/certs/private_key.pem
```

5. **Run the Flask Backend**

```bash
python run.py
```

The backend server should start on `http://localhost:5000`.

### Setup Frontend

1. **Configure Environment Variables**

Navigate to the frontend directory:

```bash
cd pyNance/frontend
```

Copy `example.env` to `.env` and update the values as needed:

```
VITE_APP_API_BASE_URL="http://localhost:5000/api"
VITE_TELLER_APP_ID="YOUR_TELLER_APP_ID"

PLAID_CLIENT_ID="YOUR_PLAID_CLIENT_ID"
PLAID_SECRET_KEY="YOUR_PLAID_SECRET_KEY"
PLAID_ENV="sandbox"

TELLER_APP_ID="YOUR_TELLER_APP_ID"

PHONE_NBR=""
PRODUCTS="transactions"
```

2. **Install Node Dependencies**

```bash
npm install
```

3. **Run the Frontend**

```bash
npm run dev
```

The frontend should now be available at `http://localhost:5173`.

## Usage

### Linking Accounts
Use the provided UI components on the Accounts page (e.g. `LinkAccount.vue`) to generate token/user ID pairs for linking accounts via Plaid or Teller.

### Refreshing Data
Use the refresh controls on the Accounts page (`RefreshTellerControls.vue` and `RefreshPlaidControls.vue`) to update account balances and transactions. The backend endpoints will query your SQL database for account details and call the respective APIs.

### Viewing Charts
Navigate through the dashboard to view various charts and graphs (e.g. Daily Net Income, Category Breakdown) based on your financial data.

## Environment File Locations

- **Backend:** `pyNance/backend/.env` (rename `example.env` to `.env`).
- **Frontend:** `pyNance/frontend/.env` (rename `example.env` to `.env`).

## Development Notes

- **Database Initialization:**
  - When the Flask app starts, it will automatically create the database tables if they do not exist using `db.create_all()` in your `create_app()` function.

- **Virtual Environment:**
  - The recommended setup is to keep your virtual environment (venv) in the project root.

- **Logging:**
  - Log files are configured in the `config.py` file and are stored in the designated logs directory.

## Troubleshooting

- **CORS Issues:**
  - Ensure that CORS is enabled in your Flask app (using `flask_cors`).

- **Environment Variables:**
  - Verify that the correct `.env` file is in place for both backend and frontend.

- **API Keys:**
  - Do not expose backend secrets in your frontend. Keep your Plaid and Teller secrets only in the `.env` files.

## License

This project is licensed under the MIT License.

