# pyNance

**pyNance** is a personal finance dashboard that integrates with **Plaid** and **Teller.io** to manage accounts, transactions, and financial insights.

## Features
- **Account Linking**: Connect bank accounts via **Plaid** and **Teller**.
- **Transaction Management**: Fetch, categorize, and process financial transactions.
- **Charts & Insights**: Generate financial charts such as net worth tracking, category breakdowns, and cash flow.
- **Historical Account Data**: Maintain balance history for trend analysis.
- **Secure API Handling**: Supports exponential backoff for rate-limited requests.

---

## Setup & Installation

### Prerequisites
- **Python 3.8+**
- **Node.js & npm**
- **Plaid API credentials**
- **Teller API credentials**

### Clone the Repository
```sh
git clone https://github.com/yourusername/pyNance.git
cd pyNance
```

### Virtual Environment Setup
Create a virtual environment **in the root directory**:
```sh
python -m venv venv
```
Activate it:
- On macOS/Linux:
  ```sh
  source venv/bin/activate
  ```
- On Windows:
  ```sh
  venv\Scripts\activate
  ```

---

## Backend (Flask API)
### Navigate to the backend:
```sh
cd backend
```
### Install Python Dependencies:
```sh
pip install -r requirements.txt
```
### Set Environment Variables
Create a `.env` file inside `/backend/` with your API credentials:
```ini
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret
PLAID_ENV=sandbox  # or "development" / "production"
TELLER_APP_ID=your_teller_app_id
```

### Run Flask Server
```sh
flask run
```
This will start the backend API.

---

## Frontend (Vue Dashboard)
### Navigate to the frontend:
```sh
cd ../frontend
```
### Install Dependencies:
```sh
npm install
```
### Run Development Server:
```sh
npm run dev
```
This will start the Vue dashboard.

---

## API Endpoints

### Plaid
- **Generate Link Token**: `/api/plaid/transactions/generate_link_token` (POST)
- **Exchange Public Token**: `/api/plaid/transactions/exchange_public_token` (POST)
- **Fetch Accounts**: `/api/plaid/transactions/get_accounts` (GET)
- **Refresh Transactions**: `/api/plaid/transactions/refresh_accounts` (POST)

### Teller
- **Generate Link Token**: `/api/teller/link/generate_link_token` (POST)
- **Exchange Public Token**: `/api/teller/exchange_public_token` (POST)
- **Fetch Accounts**: `/api/teller/get_accounts` (GET)
- **Refresh Transactions**: `/api/teller/refresh_accounts` (POST)

### Charts & Insights
- **Category Breakdown**: `/api/charts/category_breakdown` (GET)
- **Cash Flow Analysis**: `/api/charts/cash_flow` (GET)
- **Net Worth Tracking**: `/api/charts/net_assets` (GET)

---

## Configuration

### Database
By default, the application uses **SQLite**:
```
SQLALCHEMY_DATABASE_URI=sqlite:///data/dashroad.db
```
If needed, you can modify `config.py` to use a different database.

### Logging
Logs are stored in `logs/testing.log`. Modify `config.py` to change the logging level.

---

## Contribution & Development
1. Fork the repository
2. Create a feature branch (`git checkout -b feature-name`)
3. Commit changes (`git commit -m "Added feature X"`)
4. Push to your fork (`git push origin feature-name`)
5. Open a Pull Request

---

## License
This project is licensed under the MIT License.

---

## Notes
- Ensure **Plaid & Teller API credentials** are valid before running the server.
- Transactions update in **batches** (default batch size: 100).
- Exponential backoff is implemented for **rate-limited API requests**.

---

Happy tracking!

