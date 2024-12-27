'''
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    access_token TEXT NOT NULL
);

CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    account_id VARCHAR(255) UNIQUE NOT NULL,
    name TEXT,
    balances JSONB
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(255) REFERENCES accounts(account_id),
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    date DATE,
    amount NUMERIC,
    category TEXT[],
    description TEXT
);
'''