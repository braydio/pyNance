from config import logging
from sqlalchemy import JSON, Column, Date, Float, Integer, String, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


# Define the Transaction model
class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String, unique=True, nullable=False)
    account_id = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=True)
    merchant_name = Column(String, nullable=True)
    institution_name = Column(String, nullable=True)
    raw_data = Column(JSON, nullable=True)  # Optional raw API response


# Define the RecentRefresh model
class RecentRefresh(Base):
    __tablename__ = "recent_refresh"
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String, unique=True, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_transactions = Column(Integer, nullable=False)
    raw_data = Column(JSON, nullable=True)  # Optional raw API response


# Database setup
DATABASE_URL = "sqlite:///transactions.db"  # SQLite database
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
session = Session()


def init_db():
    """Initialize the database and create tables if they don't exist."""
    Base.metadata.create_all(engine)


# Save transactions to the database
def save_transactions_to_db(transactions, linked_accounts):
    """
    Save transactions to the database.

    Args:
        transactions (list): List of transaction dictionaries from the Plaid API.
        linked_accounts (dict): Dictionary of linked accounts for reference.
    """
    for transaction in transactions:
        try:
            # Create a new transaction object
            new_transaction = Transaction(
                transaction_id=transaction["transaction_id"],
                account_id=transaction["account_id"],
                date=transaction["date"],
                name=transaction["name"],
                amount=transaction["amount"],
                category=transaction.get("category", ["Unknown"])[-1],
                merchant_name=transaction.get("merchant_name", "Unknown"),
                institution_name=linked_accounts[transaction["account_id"]].get(
                    "institution_name", "Unknown"
                ),
                raw_data=transaction,  # Store raw data for debugging or extensibility
            )

            # Add to session
            session.add(new_transaction)
            session.commit()

        except IntegrityError:
            # If the transaction ID already exists, skip it
            session.rollback()
            logging.warning(
                f"Duplicate transaction skipped: {transaction['transaction_id']}"
            )

        except Exception as e:
            # Log unexpected errors
            session.rollback()
            logging.error(
                f"Error saving transaction {transaction['transaction_id']}: {str(e)}"
            )


# Save recent refresh data to the database
def save_recent_refresh_to_db(
    item_id, start_date, end_date, total_transactions, raw_data
):
    """
    Save recent refresh data to the database.

    Args:
        item_id (str): The Plaid item ID.
        start_date (str): The start date of the refresh.
        end_date (str): The end date of the refresh.
        total_transactions (int): Total number of transactions fetched.
        raw_data (dict): Raw API response data.
    """
    try:
        # Create a new RecentRefresh object
        recent_refresh = RecentRefresh(
            item_id=item_id,
            start_date=start_date,
            end_date=end_date,
            total_transactions=total_transactions,
            raw_data=raw_data,
        )

        # Add to session
        session.add(recent_refresh)
        session.commit()

    except IntegrityError:
        # If the item ID already exists, update the record
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
            logging.error(f"Error updating recent refresh for item {item_id}: {str(e)}")

    except Exception as e:
        # Log unexpected errors
        session.rollback()
        logging.error(f"Error saving recent refresh for item {item_id}: {str(e)}")
