# pyNance-Dash

Before diving into the documentation, if anybody is *only* here for the quickstart and not the *true* nourishment of community and shared knowledge:

## Quickstart
just take your start and leave...
1. Clone this repo to your disk:
> [!NOTE]  - This includes key files from [the Plaid Quickstart Repo on GitHub](https://github.com/plaid/quickstart)
```
git clone https://github.com/braydio/pyNance
```

 To get your access link tokens, you will build a Docker container with the required specs to run both the front- and back-ends of the server.

2. Save [this docker-compose.yml file](https://github.com/braydio/pyNance/blob/main/docker-compose.yml) to quickstart/

  - This will be over-writing the docker-compose.yml file that was there initially.
  - The docker-compose.yml contains all the details needed for your machine to build out the container.
  - The local docker container will host both front- and back-ends of the server and allow you to fetch your link token.
  
3. Create a .env from a copy of example.env and save your Client ID, Key, and redirect URI


**Setup / Building / Spin-Up:**

Clone this repo, copy in the new .env and docker-compose
```
git clone https://github.com/braydio/pyNance
cd pyNance
cp docker-compose.yml quickstart/docker-compose.yml
cp example_sandox.env quickstart/.env
cd quickstart
```
Fill out .env and save
Build the docker container from the new docker-compose.yml
```
docker-compose up --build
docker-compose down
```
You now have a local Docker Container that is able to host your local server. 
- The **Python backend** will be available at `http://localhost:8000`
- The **React frontend** will be available at `http://localhost:3000`

Spin it back up with:
```docker-compose up```
Then navigate to `http://localhost:3000` and initiate the link to get your link token.

>[!NOTE]
>Don't forget to set your allowed redirect URIs in the [Plaid Developer Dashboard](https://dashboard.plaid.com/developers/api)

### Work in Progress: 

The get-link.py script in the root directory will ideally be used to get link tokens based on user specifications. 

I haven't tried it out yet, if you do please let me know how it goes.

kthxbye

**pyNance-Dash** is a personal finance dashboard built using Python, leveraging the Plaid API to fetch and manage financial data, and integrating with Google Sheets and/or Excel for easy visualization and tracking.

## Prerequisites

- Docker: [Install Docker](https://docs.docker.com/get-docker/)
- Docker Compose: [Install Docker Compose](https://docs.docker.com/compose/install/)


# Project Overview (Slowstart)

The goal of pyNance-Dash is to provide a streamlined way to manage personal finances by:
- Using the **Plaid API** to connect with financial institutions and fetch data on **transactions**, **accounts**, and **balances**.
- Processing the fetched data using Python.
>[!WIP]
>Sending financial data to **Google Sheets and/or Excel** for visualization and analysis via the `gspread` library.


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
