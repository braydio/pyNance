from run_refactor import run_refactor
PYTHON_FILE = "backend/app/routes/plaid_transactions.py"
ROUTE = "generate_link_token_endpoint"
run_refactor(ROUTE, PYTHON_FILE)
