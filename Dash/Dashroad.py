from flask import Flask, render_template, jsonify
import json
import os

from routes import process_transactions

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('landing.html')

@app.route('/process_transactions', methods=['POST'])
def process_transactions_route():
    transactions_file = os.path.join(os.path.dirname(__file__), '../Plaid/data/transactions.json')
    accounts_file = os.path.join(os.path.dirname(__file__), '../Plaid/data/LinkAccounts.json')  # Ensure this file exists
    output_file = os.path.join(os.path.dirname(__file__), './data/processed_transactions.json')
    
    result = process_transactions(transactions_file, accounts_file, output_file)
    return jsonify(result), 200 if result["status"] == "success" else 500

@app.route('/get_processed_transactions', methods=['GET'])
def get_processed_transactions():
    try:
        file_path = os.path.join(os.path.dirname(__file__), './data/processed_transactions.json')
        with open(file_path, 'r') as f:
            transactions = json.load(f)
        return jsonify({"status": "success", "data": transactions}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
