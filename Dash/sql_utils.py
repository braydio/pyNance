from datetime import datetime

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

    institution = relationship("Institution", backref="accounts")

    def __repr__(self):
        return f"<Account(plaid_account_id={self.plaid_account_id}, name={self.name})>"


# ---------------------------------------------------------------------
# HISTORICAL BALANCES TABLE
# ---------------------------------------------------------------------
class AccountBalance(Base):
    __tablename__ = "account_balances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    date = Column(Date, nullable=False, default=datetime.utcnow)
    current_balance = Column(Float, nullable=False)
    available_balance = Column(Float, nullable=True)
    limit = Column(Float, nullable=True)
    raw_data = Column(JSON, nullable=True)

    account = relationship("Account", backref="balances")

    def __repr__(self):
        return f"<AccountBalance(account_id={self.account_id}, date={self.date}, balance={self.current_balance})>"


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
    name = Column(String, nullable=False)  # transaction description
    amount = Column(Float, nullable=False)  # negative for expense
    # New columns for primary and secondary category:
    primary_category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    secondary_category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    merchant_name = Column(String, nullable=True)
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships: associate each category field with its foreign key.
    primary_category = relationship(
        "Category", foreign_keys=[primary_category_id], backref="primary_transactions"
    )
    secondary_category = relationship(
        "Category",
        foreign_keys=[secondary_category_id],
        backref="secondary_transactions",
    )

    # Relationship back to Account
    account = relationship("Account", backref="transactions")

    def __repr__(self):
        return (
            f"<Transaction(transaction_id={self.transaction_id}, amount={self.amount})>"
        )


# Optionally create indexes for faster queries
Index("idx_transactions_date", Transaction.date)
Index("idx_transactions_account_id", Transaction.account_id)


# ---------------------------------------------------------------------
# RECENT REFRESH TABLE (SYNC LOG)
# ---------------------------------------------------------------------
class RecentRefresh(Base):
    __tablename__ = "recent_refresh"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String, unique=True, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_transactions = Column(Integer, nullable=False)
    raw_data = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<RecentRefresh(item_id={self.item_id}, total_transactions={self.total_transactions})>"


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
def save_transactions_to_db(session, transactions, linked_accounts):
    """
    Save Plaid transactions to the database.
      - Creates or finds Institution and Account records.
      - Looks up categories and saves transactions with both primary and secondary category.
    """
    # Ensure there is a default "Unknown" category.
    unknown_category = (
        session.query(Category).filter_by(name="Unknown", parent_id=None).first()
    )
    if not unknown_category:
        unknown_category = Category(name="Unknown")
        session.add(unknown_category)
        session.commit()

    for tx in transactions:
        try:
            # Convert date string to datetime.date.
            tx_date = datetime.strptime(tx["date"], "%Y-%m-%d").date()

            # 1) Determine or create the Institution row.
            inst_name = linked_accounts.get(tx["account_id"], {}).get(
                "institution_name", "Unknown"
            )
            institution = session.query(Institution).filter_by(name=inst_name).first()
            if not institution:
                institution = Institution(
                    plaid_institution_id="unknown_id",  # update if available
                    name=inst_name,
                )
                session.add(institution)
                session.commit()

            # 2) Determine or create the Account row.
            plaid_acct_id = tx["account_id"]
            account = (
                session.query(Account).filter_by(plaid_account_id=plaid_acct_id).first()
            )
            if not account:
                account = Account(
                    plaid_account_id=plaid_acct_id,
                    institution_id=institution.id,
                    name="Unknown",  # update if available
                    account_type="Unknown",  # update as needed
                )
                session.add(account)
                session.commit()

            # 3) Validate and lookup the Category.
            # Plaid's "category" field is a list (e.g., ["Food and Drink", "Restaurants", "Fast Food"])
            category_hierarchy = tx.get("category", ["Unknown"])

            # Get primary and secondary categories.
            primary_cat_name = (
                category_hierarchy[0] if len(category_hierarchy) > 0 else "Unknown"
            )
            secondary_cat_name = (
                category_hierarchy[1]
                if len(category_hierarchy) > 1
                else primary_cat_name
            )

            # Look up the primary category.
            primary_category = (
                session.query(Category)
                .filter_by(name=primary_cat_name, parent_id=None)
                .first()
            )
            if not primary_category:
                logger.warning(
                    f"Primary category '{primary_cat_name}' not found. Using Unknown."
                )
                primary_category = unknown_category

            # Look up the secondary category.
            secondary_category = (
                session.query(Category)
                .filter_by(name=secondary_cat_name, parent_id=primary_category.id)
                .first()
            )
            if not secondary_category:
                logger.warning(
                    f"Secondary category '{secondary_cat_name}' not found under '{primary_cat_name}'. Using Unknown."
                )
                secondary_category = unknown_category

            # 4) Create the Transaction row with both category IDs.
            new_transaction = Transaction(
                transaction_id=tx["transaction_id"],
                account_id=account.id,
                date=tx_date,
                name=tx["name"],
                amount=tx["amount"],
                primary_category_id=primary_category.id,
                secondary_category_id=secondary_category.id,
                merchant_name=tx.get("merchant_name", "Unknown"),
                raw_data=str(tx),  # or use json.dumps(tx)
            )
            session.add(new_transaction)
            session.commit()

        except IntegrityError:
            session.rollback()
            logger.warning(f"Duplicate transaction skipped: {tx['transaction_id']}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving transaction {tx['transaction_id']}: {str(e)}")


def save_recent_refresh_to_db(
    item_id, start_date, end_date, total_transactions, raw_data
):
    """
    Save recent refresh data to the database, or update if item_id already exists.
    """
    try:
        recent_refresh = RecentRefresh(
            item_id=item_id,
            start_date=start_date,
            end_date=end_date,
            total_transactions=total_transactions,
            raw_data=raw_data,
        )
        session.add(recent_refresh)
        session.commit()

    except IntegrityError:
        session.rollback()
        try:
            existing_refresh = (
                session.query(RecentRefresh).filter_by(item_id=item_id).one()
            )
            existing_refresh.start_date = start_date
            existing_refresh.end_date = end_date
            existing_refresh.total_transactions = total_transactions
            existing_refresh.raw_data = raw_data
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating recent refresh for item {item_id}: {str(e)}")

    except Exception as e:
        session.rollback()
        logger.error(f"Error saving recent refresh for item {item_id}: {str(e)}")


def save_accounts_to_db(accounts, item_id):
    """
    Saves newly linked accounts to the database, ensuring the associated institution is created first.
    """
    try:
        institution_name = accounts[0].get("institution_name", "Unknown Institution")
        institution = (
            session.query(Institution).filter_by(name=institution_name).first()
        )
        if not institution:
            institution = Institution(
                plaid_institution_id=item_id,
                name=institution_name,
            )
            session.add(institution)
            session.commit()
            logger.info(f"Created new institution: {institution_name}")

        for account in accounts:
            plaid_account_id = account["account_id"]
            existing_account = (
                session.query(Account)
                .filter_by(plaid_account_id=plaid_account_id)
                .first()
            )
            if not existing_account:
                new_account = Account(
                    plaid_account_id=plaid_account_id,
                    institution_id=institution.id,
                    name=account["name"],
                    account_type=account["type"],
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
        institution_name = accounts[0].get("institution_name", "Unknown Institution")
        institution = (
            session.query(Institution).filter_by(name=institution_name).first()
        )
        if not institution:
            institution = Institution(
                plaid_institution_id=item_id,
                name=institution_name,
            )
            session.add(institution)
            session.commit()
            logger.info(f"Created new institution: {institution_name}")

        for account in accounts:
            plaid_account_id = account["account_id"]
            existing_account = (
                session.query(Account)
                .filter_by(plaid_account_id=plaid_account_id)
                .first()
            )
            if not existing_account:
                new_account = Account(
                    plaid_account_id=plaid_account_id,
                    institution_id=institution.id,
                    name=account["name"],
                    account_type=account["type"],
                )
                session.add(new_account)
                logger.info(f"Added new account: {account['name']}")

        session.commit()
        logger.info(f"Saved {len(accounts)} accounts to the database.")

    except Exception as e:
        session.rollback()
        logger.error(f"Error saving accounts to database: {str(e)}")


def save_account_balances(accounts):
    """
    Saves historical account balances to the database.
    """
    try:
        for account in accounts:
            plaid_account_id = account["account_id"]
            account_record = (
                session.query(Account)
                .filter_by(plaid_account_id=plaid_account_id)
                .first()
            )
            if not account_record:
                logger.warning(
                    f"Skipping balance save for unknown account: {plaid_account_id}"
                )
                continue

            balance_entry = AccountBalance(
                account_id=account_record.id,
                date=datetime.utcnow().date(),
                current_balance=account["balances"].get("current"),
                available_balance=account["balances"].get("available"),
                limit=account["balances"].get("limit"),
                raw_data=account["balances"],
            )
            session.add(balance_entry)

        session.commit()
        logger.info(f"Saved historical balances for {len(accounts)} accounts.")

    except Exception as e:
        session.rollback()
        logger.error(f"Error saving account balances: {str(e)}")
