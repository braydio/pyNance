"""Investment models: Security, InvestmentHolding, InvestmentTransaction."""

from app.extensions import db

from .mixins import TimestampMixin


class Security(db.Model, TimestampMixin):
    __tablename__ = "securities"

    security_id = db.Column(db.String(128), primary_key=True)
    name = db.Column(db.String(256), nullable=True)
    ticker_symbol = db.Column(db.String(64), nullable=True)
    cusip = db.Column(db.String(64), nullable=True)
    isin = db.Column(db.String(64), nullable=True)
    type = db.Column(db.String(64), nullable=True)
    is_cash_equivalent = db.Column(db.Boolean, default=False)
    institution_price = db.Column(db.Float, nullable=True)
    institution_price_as_of = db.Column(db.Date, nullable=True)
    market_identifier_code = db.Column(db.String(64), nullable=True)
    iso_currency_code = db.Column(db.String(8), nullable=True)
    # Full raw security payload (optional)
    raw = db.Column(db.JSON, nullable=True)


class InvestmentHolding(db.Model, TimestampMixin):
    __tablename__ = "investment_holdings"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(
        db.String(64), db.ForeignKey("accounts.account_id"), index=True, nullable=False
    )
    security_id = db.Column(
        db.String(128),
        db.ForeignKey("securities.security_id"),
        index=True,
        nullable=False,
    )
    quantity = db.Column(db.Float, nullable=True)
    cost_basis = db.Column(db.Float, nullable=True)
    institution_value = db.Column(db.Float, nullable=True)
    as_of = db.Column(db.Date, nullable=True)
    # Full raw holding payload (optional)
    raw = db.Column(db.JSON, nullable=True)

    __table_args__ = (
        db.UniqueConstraint(
            "account_id", "security_id", name="uq_holding_account_security"
        ),
    )


class InvestmentTransaction(db.Model, TimestampMixin):
    __tablename__ = "investment_transactions"

    investment_transaction_id = db.Column(db.String(128), primary_key=True)
    account_id = db.Column(
        db.String(64), db.ForeignKey("accounts.account_id"), index=True, nullable=False
    )
    security_id = db.Column(
        db.String(128),
        db.ForeignKey("securities.security_id"),
        index=True,
        nullable=True,
    )
    date = db.Column(db.Date, nullable=True)
    amount = db.Column(db.Float, nullable=True)
    price = db.Column(db.Float, nullable=True)
    quantity = db.Column(db.Float, nullable=True)
    subtype = db.Column(db.String(64), nullable=True)
    type = db.Column(db.String(64), nullable=True)
    name = db.Column(db.String(256), nullable=True)
    fees = db.Column(db.Float, nullable=True)
    iso_currency_code = db.Column(db.String(8), nullable=True)
    # Full raw investment transaction payload (optional)
    raw = db.Column(db.JSON, nullable=True)
