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
