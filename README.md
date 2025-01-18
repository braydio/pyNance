# pyNance-Dash

### Current Development State (1/18) 
- Developing Plaid Link in pyNance/Plaid/deploy

Currently the account link process happens in Plaid. So for the sake of file paths etc. cd into pyNance/Plaid before running link scripts.

    Actually immedate state is in pyNance/Plaid/deploy, but will copy deploy to Plaid.

## Quickstart

```
# Clone into project and duplicate example.env to .env
git clone https://github.com/braydio/pyNance.git
cd pyNance
cp example.env .env

-- Set up python environment
python -m venv .venv

.venv/Scripts/activate # Windows
source .venv/bin/activate # virgin-ized

pip install -r requirements.txt

-- Run the script to generate a link token:
python Plaid/pylinkPlaid.py
```

This starts a Flask server at localhost:5000

Use a web browser to navigate to the ip address listed in the terminal and finish linking your account in your web browser.

