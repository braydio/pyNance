from datetime import datetime

from config import logging
from sqlalchemy import (
    JSON,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

from config import DIRECTORIES, FILES, logger

DATA_DIR = DIRECTORIES["DATA_DIR"]
TEMP_DIR = DIRECTORIES["TEMP_DIR"]
LOGS_DIR = DIRECTORIES["LOGS_DIR"]
THEMES_DIR = DIRECTORIES["THEMES_DIR"]
LINKED_ITEMS = FILES["LINKED_ITEMS"]
LINKED_ACCOUNTS = FILES["LINKED_ACCOUNTS"]
TRANSACTIONS_LIVE = FILES["TRANSACTIONS_LIVE"]
TRANSACTIONS_RAW = FILES["TRANSACTIONS_RAW"]
TRANSACTIONS_RAW_ENRICHED = FILES["TRANSACTIONS_RAW_ENRICHED"]
DEFAULT_THEME = FILES["DEFAULT_THEME"]
CURRENT_THEME = FILES["CURRENT_THEME"]


# ---------------------------------------------------------------------
# INSTITUTIONS TABLE
# ---------------------------------------------------------------------
class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plaid_institution_id = Column(String, unique=True, nullable=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Optional: Add a __repr__ for debugging
    def __repr__(self):
        return f"<Institution(name={self.name})>"


# ---------------------------------------------------------------------
# ACCOUNTS TABLE
# ---------------------------------------------------------------------
class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plaid_account_id = Column(String, unique=True, nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    name = Column(String, nullable=False)
    account_type = Column(String, nullable=True)  # e.g. checking, savings, credit, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to Institution
    institution = relationship("Institution", backref="accounts")

    def __repr__(self):
        return f"<Account(plaid_account_id={self.plaid_account_id}, name={self.name})>"


# ---------------------------------------------------------------------
# INVESTMENTS ACCOUNT TABLE
# ---------------------------------------------------------------------
class InvestmentAccount(Base):
    __tablename__ = "investment_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String, unique=True, nullable=False)
    institution_name = Column(String, nullable=False)
    access_token = Column(String, nullable=False)
    linked_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<InvestmentAccount(item_id={self.item_id}, institution_name={self.institution_name})>"


# ---------------------------------------------------------------------
# CATEGORIES TABLE
# ---------------------------------------------------------------------
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Self-referential relationship for hierarchical categories (optional)
    parent = relationship("Category", remote_side=[id], backref="subcategories")

    def __repr__(self):
        return f"<Category(name={self.name})>"


# ---------------------------------------------------------------------
# TRANSACTIONS TABLE
# ---------------------------------------------------------------------
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String, unique=True, nullable=False)  # from Plaid
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    date = Column(Date, nullable=False)
    name = Column(String, nullable=False)  # e.g. transaction description
    amount = Column(Float, nullable=False)  # could store negative for expense
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    merchant_name = Column(String, nullable=True)
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships back to Account and Category
    account = relationship("Account", backref="transactions")
    category = relationship("Category", backref="transactions")

    def __repr__(self):
        return (
            f"<Transaction(transaction_id={self.transaction_id}, amount={self.amount})>"
        )


# Optionally create some indexes for faster queries
Index("idx_transactions_date", Transaction.date)
Index("idx_transactions_account_id", Transaction.account_id)


# ---------------------------------------------------------------------
# HISTORICAL BALANCE SYNC
# ---------------------------------------------------------------------
# class DailyBalanceTrended


# ---------------------------------------------------------------------
# DATABASE SETUP
# ---------------------------------------------------------------------
DATABASE_URL = (
    "sqlite:///transactions.db"  # or 'postgresql://user:pass@localhost/dbname'
)
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
session = Session()


def init_db():
    """Initialize the database and create tables if they don't exist."""
    Base.metadata.create_all(engine)


# ---------------------------------------------------------------------
# SAVE/UPDATE FUNCTIONS
# ---------------------------------------------------------------------
def save_transactions_to_db(transactions, linked_accounts=LINKED_ACCOUNTS):
    """
    Save Plaid transactions to the database, creating or linking related records:
      - Institution
      - Account
      - Category
      - Transaction
    """
    for tx in transactions:
        try:
            # Convert date string to a datetime.date
            tx_date = datetime.strptime(tx["date"], "%Y-%m-%d").date()

            # 1) Determine or create the Institution row
            inst_name = linked_accounts.get(tx["account_id"], {}).get(
                "institution_name", "Unknown"
            )
            institution = session.query(Institution).filter_by(name=inst_name).first()
            if not institution:
                institution = Institution(
                    plaid_institution_id="unknown_id",  # or fetch from Plaid data if available
                    name=inst_name,
                )
                session.add(institution)
                session.commit()

            # 2) Determine or create the Account row
            plaid_acct_id = tx["account_id"]
            account = (
                session.query(Account).filter_by(plaid_account_id=plaid_acct_id).first()
            )
            if not account:
                account = Account(
                    plaid_account_id=plaid_acct_id,
                    institution_id=institution.id,
                    name="My Account",  # or parse from Plaid if available
                    account_type="checking",  # or parse from Plaid
                )
                session.add(account)
                session.commit()

            # 3) Determine or create the Category row
            #    Plaid's "category" might be a list, e.g. ["Food", "Groceries"]
            cat_name = tx.get("category", ["Unknown"])[-1]
            category_obj = session.query(Category).filter_by(name=cat_name).first()
            if not category_obj:
                category_obj = Category(name=cat_name)
                session.add(category_obj)
                session.commit()

            # 4) Create the Transaction
            new_transaction = Transaction(
                transaction_id=tx["transaction_id"],
                account_id=account.id,
                date=tx_date,
                name=tx["name"],
                amount=tx["amount"],
                category_id=category_obj.id,  # might be None if category is not found
                merchant_name=tx.get("merchant_name", "Unknown"),
                raw_data=tx,
            )
            session.add(new_transaction)
            session.commit()

        except IntegrityError:
            # If the transaction_id already exists, skip it
            session.rollback()
            logging.warning(f"Duplicate transaction skipped: {tx['transaction_id']}")

        except Exception as e:
            # Log unexpected errors
            session.rollback()
            logging.error(f"Error saving transaction {tx['transaction_id']}: {str(e)}")


def save_investment_account_to_db(
    session, item_id, institution_name, access_token, linked_at
):
    """
    Save an investments account record into a dedicated DB table.
    You should have an InvestmentAccount model defined in your models.

    For example:
      class InvestmentAccount(Base):
          __tablename__ = "investment_accounts"
          id = Column(Integer, primary_key=True, autoincrement=True)
          item_id = Column(String, unique=True, nullable=False)
          institution_name = Column(String, nullable=False)
          access_token = Column(String, nullable=False)
          linked_at = Column(DateTime, nullable=False)

    This function inserts a new record if one doesn't already exist.
    """
    # Example query: check if the investment account already exists.
    existing = session.query(InvestmentAccount).filter_by(item_id=item_id).first()
    if not existing:
        new_record = InvestmentAccount(
            item_id=item_id,
            institution_name=institution_name,
            access_token=access_token,
            linked_at=linked_at,  # You can parse the linked_at string if needed.
        )
        session.add(new_record)
    else:
        # Optionally update existing record.
        existing.institution_name = institution_name
        existing.access_token = access_token
        existing.linked_at = linked_at
    # Do not commit here; let the calling function handle commit.


def save_accounts_to_db(accounts, item_id):
    """
    Saves newly linked accounts to the database, ensuring the associated institution is created first.
    """
    try:
        # Get institution name from the first account
        institution_name = accounts[0].get("institution_name", "Unknown Institution")

        # 🔹 Step 1: Check if Institution exists, create if necessary
        institution = (
            session.query(Institution).filter_by(name=institution_name).first()
        )
        if not institution:
            institution = Institution(
                plaid_institution_id=item_id,  # Store Plaid's unique ID
                name=institution_name,
            )
            session.add(institution)
            session.commit()
            logger.info(f"Created new institution: {institution_name}")

        # 🔹 Step 2: Loop through all accounts and save them to the DB
        for account in accounts:
            plaid_account_id = account["account_id"]

            # Check if account already exists
            existing_account = (
                session.query(Account)
                .filter_by(plaid_account_id=plaid_account_id)
                .first()
            )
            if not existing_account:
                new_account = Account(
                    plaid_account_id=plaid_account_id,
                    institution_id=institution.id,  # Link to institution
                    name=account["name"],
                    account_type=account["type"],  # Checking, savings, etc.
                )
                session.add(new_account)
                logger.info(f"Added new account: {account['name']}")

        session.commit()
        logger.info(f"Saved {len(accounts)} accounts to the database.")

    except Exception as e:
        session.rollback()
        logger.error(f"Error saving accounts to database: {str(e)}")


def save_initial_db(accounts, item_id):
    """
    Saves newly linked accounts to the database, ensuring the associated institution is created first.
    """
    try:
        # Get institution name from the first account
        institution_name = accounts[0].get("institution_name", "Unknown Institution")

        # 🔹 Step 1: Check if Institution exists, if not, create it
        institution = (
            session.query(Institution).filter_by(name=institution_name).first()
        )
        if not institution:
            institution = Institution(
                plaid_institution_id=item_id,  # Store Plaid's unique ID
                name=institution_name,
            )
            session.add(institution)
            session.commit()
            logger.info(f"Created new institution: {institution_name}")

        # 🔹 Step 2: Loop through all accounts and save them to the DB
        for account in accounts:
            plaid_account_id = account["account_id"]

            # Check if account already exists
            existing_account = (
                session.query(Account)
                .filter_by(plaid_account_id=plaid_account_id)
                .first()
            )
            if not existing_account:
                new_account = Account(
                    plaid_account_id=plaid_account_id,
                    institution_id=institution.id,  # Link to institution
                    name=account["name"],
                    account_type=account["type"],  # Checking, savings, etc.
                )
                session.add(new_account)
                logger.info(f"Added new account: {account['name']}")

        session.commit()
        logger.info(f"Saved {len(accounts)} accounts to the database.")

    except Exception as e:
        session.rollback()
        logger.error(f"Error saving accounts to database: {str(e)}")
