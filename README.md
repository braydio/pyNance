# pyNance-Dash

Before diving into the documentation, if anybody is *only* here for the quickstart and not the *true* nourishment of community and shared knowledge:

## Quickstart
just take your start and leave...
1. Clone [the Plaid Quickstart Repo on GitHub](https://github.com/plaid/quickstart) to your disk.
> [!Note]
> To get your access link tokens, you will build a Docker container with the required specs to run both the front- and back-ends of the server.

2. Download [this docker-compose.yml file](https://github.com/braydio/pyNance-Dash/blob/main/docker-compose.yml) to your main /quickstart/

  - This will be over-writing the docker-compose.yml file that was there initially.
  - The docker-compose.yml contains all the details needed for your machine to build out the required container.
  - The local docker container will host both front- and back-ends of the server and allow you to fetch your link token.
3. Create a .env from a copy of example.env and save your Client ID, Key, and redirect URI


**Setup / Building / Spin-Up:**

```
git clone -c core.symlinks=true https://github.com/plaid/quickstart
cd quickstart
cp .env.example .env
```
Fill out .env and save
Download docker-compose.yml and build
```
docker-compose up --build
docker-compose down
```
You now have a local Docker Container that is able to host your local server. 
- The **Python backend** will be available at `http://localhost:8000`.
- The **React frontend** will be available at `http://localhost:3000`.
Spin it back up with:
```docker-compose up```
Then navigate to `http://localhost:3000` and initiate the link to get your link token.

**pyNance-Dash** is a personal finance dashboard built using Python, leveraging the Plaid API to fetch and manage financial data, and integrating with Google Sheets and/or Excel for easy visualization and tracking.

## Prerequisites

- Docker: [Install Docker](https://docs.docker.com/get-docker/)
- Docker Compose: [Install Docker Compose](https://docs.docker.com/compose/install/)


# Project Overview (Slowstart)

The goal of pyNance-Dash is to provide a streamlined way to manage personal finances by:
- Using the **Plaid API** to connect with financial institutions and fetch data on **transactions**, **accounts**, and **balances**.
- Processing the fetched data using Python.
- Sending financial data to **Google Sheets and/or Excel** for visualization and analysis via the `gspread` library.

This project is designed to help individuals automate the management of their personal finances by providing easy access to real-time data.


## Getting Started
      - WIP
### Prerequisites
- **Python 3.8+**
- **Node.js** for frontend
- **npm** for frontend dependencies
- **Plaid Account**: Sign up at [Plaid](https://plaid.com) and obtain your API keys.

### Environment Variables
Create a `.env` file based on `.env.sandbox` or `.env.prod` and populate it with the required Plaid credentials:

```
PLAID_CLIENT_ID=your_production_client_id
PLAID_SECRET=your_production_secret
PLAID_ENV=production
PLAID_PRODUCTS=transactions,auth,enrich
PLAID_COUNTRY_CODES=US
PLAID_REDIRECT_URI=
```

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/braydio/pyNance-Dash.git
   cd quickstart
   ```

2. Use the .env.sandbox template to spin up a test server using your sandbox key

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


# Plaid Products Quick Reference for Personal Finance Dashboard

## Recommended Products

1. **`transactions`** (Key for Spending Insights)
   - Fetch categorized transaction data.
   - **Use Cases**:
     - Track expenses.
     - Categorize spending habits.
     - Visualize cash flow.

2. **`balances`** (Key for Current Finances)
   - Retrieve real-time account balances.
   - **Use Cases**:
     - Show available cash.
     - Monitor account balances.
     - Calculate net worth.

3. **`auth`** (Optional for Bank Transfers)
   - Provides routing and account numbers.
   - **Use Cases**:
     - Enable ACH payments.
     - Automate bill payments.

4. **`identity`** (Optional for Account Details)
   - Returns account holder information (e.g., name, email).
   - **Use Cases**:
     - Verify account ownership.
     - Improve security for linked accounts.

5. **`assets`** (Optional for Net Worth Analysis)
   - Provides detailed reports on balances, transactions, and income.
   - **Use Cases**:
     - Generate detailed financial reports.
     - Track long-term trends in accounts.

---

## Suggested Configuration for `.env`

Start with these essential products:
```plaintext
PLAID_PRODUCTS=transactions,balances
```

## Features
- **Account Linking**: Securely connect financial institutions using the Plaid API.
- **Transaction Syncing**: Fetch and track transactions, balances, and account details.
- **Google Sheets and/or Excel Integration**: Append financial data to Google Sheets and/or Excel for easy analysis and record-keeping.
- **React Frontend**: User-friendly interface to visualize and interact with your financial data.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing
Feel free to open issues or submit pull requests if you have suggestions for improvement or bug fixes.

## Acknowledgments
- **Plaid** for providing easy-to-use financial data APIs.
- **Google Sheets** for helping manage and visualize financial data.

## Reference
- https://github.com/williamlmao/plaid-to-gsheets
- https://dashboard.plaid.com/developers/keys
