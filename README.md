# pyNance-Lab

Before diving into the documentation, if anybody is *only* here for the quickstart and not the *true* nourishment of community and shared knowledge:

**Quickstart** - just take your start and leave...
1. Clone this repo to your disk, navigate to /python/
2. Create a python virtual environment in the main python dir
3. Activate the venv and install dependencies from requirements.txt
4. Start the Python server at pyNance-Lab/python/dev-server.py
5. Then run `npm ci` to start the frontend

**Quickstart - Extended**
6. Build a production server using npm
7. All CLI commands so far:

```
git clone https://github.com/braydio/pyNance-Dash.git

cd python
python -m venv .venv
pip install -r requirements.txt
```
If using Windows, activate with the Windows command, otherwise use the Not-windows one.
```
.venv/Scripts/activate
source .venv/bin/activate

npm run build
```
This is about as far as I'm comfortable atm but will update when after below:
```
npm install -g server

server -s build
```
[Learn more about deployment here!](https://cra.link/deployment)


**pyNance-Dash** is a personal finance dashboard built using Python, leveraging the Plaid API to fetch and manage financial data, and integrating with Google Sheets and/or Excel for easy visualization and tracking.

## Project Overview

The goal of pyNance-Dash is to provide a streamlined way to manage personal finances by:
- Using the **Plaid API** to connect with financial institutions and fetch data on **transactions**, **accounts**, and **balances**.
- Processing the fetched data using Python.
- Sending financial data to **Google Sheets and/or Excel** for visualization and analysis via the `gspread` library.

This project is designed to help individuals automate the management of their personal finances by providing easy access to real-time data.

## Features
- **Account Linking**: Securely connect financial institutions using the Plaid API.
- **Transaction Syncing**: Fetch and track transactions, balances, and account details.
- **Google Sheets and/or Excel Integration**: Append financial data to Google Sheets and/or Excel for easy analysis and record-keeping.
- **React Frontend**: User-friendly interface to visualize and interact with your financial data.

## Technologies Used
- **Backend**: Python (Flask), Plaid API
- **Frontend**: React
- **Data Storage**: Google Sheets and/or Excel (via `gspread`)
- **Deployment**: Waitress (production WSGI server for Python)

## Getting Started

### Prerequisites
- **Python 3.8+**
- **Node.js** for frontend
- **npm** for frontend dependencies
- **Plaid Account**: Sign up at [Plaid](https://plaid.com) and obtain your API keys.

### Environment Variables
Create a `.env` file based on `.env.example` and populate it with the required Plaid credentials:

```
PLAID_CLIENT_ID=your_production_client_id
PLAID_SECRET=your_production_secret
PLAID_ENV=production
PLAID_PRODUCTS=transactions,auth,enrich
PLAID_COUNTRY_CODES=US
PLAID_REDIRECT_URI=http://localhost:3000
PORT=8000
```

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pyNance-Dash.git
   cd pyNance-Dash
   ```

2. Set up the backend:
   ```bash
   cd python
   pip install -r requirements.txt
   ./start.sh
   ```

3. Set up the frontend:
   ```bash
   cd ../frontend
   npm ci
   npm start
   ```

The backend should run on `http://localhost:8000` and the frontend on `http://localhost:3000`.

## Usage
- **Link Accounts**: Use the frontend to link your financial accounts via Plaid.
- **View Transactions**: Once linked, transactions and account information will be avaiDashle in the dashboard.
- **Export to Google Sheets and/or Excel**: Automatically append transactions to your Google Sheets and/or Excel for analysis.

## Deployment
For production, use the Waitress WSGI server for the backend:
```bash
python3 prod-server.py
```
Ensure the environment is set to `production` in your `.env` file.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing
Feel free to open issues or submit pull requests if you have suggestions for improvement or bug fixes.

## Acknowledgments
- **Plaid** for providing easy-to-use financial data APIs.
- **Google Sheets and/or Excel** for helping manage and visualize financial data.

