# db_models.py
import os
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///pynance.db")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


class AccountDetails(Base):
    __tablename__ = "account_details"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(String, index=True)
    institution_name = Column(String, nullable=False)
    account_name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    subtype = Column(String)
    available_balance = Column(Float)
    current_balance = Column(Float)
    provider = Column(
        String, nullable=False
    )  # Provider indicates Plaid or Teller saved link
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="account")
    access_info = relationship("AccessTable", back_populates="account", uselist=False)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    tx_id = Column(String, unique=True, index=True, nullable=False)
    date = Column(DateTime, nullable=False)
    name = Column(String)
    amount = Column(Float, nullable=False)
    category = Column(String)
    merchant_name = Column(String)
    account_id = Column(Integer, ForeignKey("account_details.id"), nullable=False)

    account = relationship("AccountDetails", back_populates="transactions")


class AccessTable(Base):
    __tablename__ = "access_table"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(
        Integer, ForeignKey("account_details.id"), unique=True, nullable=False
    )
    access_token = Column(String, nullable=False)
    last_refreshed = Column(DateTime, default=datetime.utcnow)

    account = relationship("AccountDetails", back_populates="access_info")
    __table_args__ = (UniqueConstraint("account_id", name="uq_access_account"),)


class HistoricalBalance(Base):
    __tablename__ = "historical_balance"
    id = Column(Integer, primary_key=True, index=True)
    sync_date = Column(DateTime, default=datetime.utcnow, unique=True, index=True)
    net_balance = Column(Float, nullable=False)
    # Future plans to include additional fields such as:
    # total_assets = Column(Float)
    # total_liabilities = Column(Float)


def init_db():
    """Create all tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)
