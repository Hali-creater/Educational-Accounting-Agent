from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import enum
from datetime import datetime, timezone

Base = declarative_base()

class TransactionType(enum.Enum):
    REVENUE = "Revenue"
    EXPENSE = "Expense"
    ASSET_ACQUISITION = "Asset Acquisition"
    EQUITY_ADJUSTMENT = "Equity Adjustment"

class AccountCategory(enum.Enum):
    ASSET = "Asset"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"

class Account(Base):
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    category = Column(Enum(AccountCategory), nullable=False)

    def __repr__(self):
        return f"<Account(name='{self.name}', category='{self.category}')>"

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    description = Column(String)
    amount = Column(Float, nullable=False)
    transaction_type = Column(Enum(TransactionType))

    # Raw JSON data as received from the interface
    raw_data = Column(String)

    journal_entries = relationship("JournalEntry", back_populates="transaction")

class JournalEntry(Base):
    __tablename__ = 'journal_entries'
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'))
    account_id = Column(Integer, ForeignKey('accounts.id'))
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)

    transaction = relationship("Transaction", back_populates="journal_entries")
    account = relationship("Account")

def get_engine(db_url="sqlite:///accounting.db"):
    return create_engine(db_url)

def init_db(engine):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
