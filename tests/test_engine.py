import pytest
from src.models import init_db, get_engine, AccountCategory
from src.engine import AccountingEngine

@pytest.fixture
def session():
    engine = get_engine("sqlite:///:memory:")
    return init_db(engine)

@pytest.fixture
def engine(session):
    return AccountingEngine(session)

def test_add_transaction(engine):
    # "Collected $15,000 in April cash for tuition"
    t = engine.add_raw_transaction(
        date_str="2026-04-01",
        description="Tuition collection",
        amount=15000.0,
        transaction_type_str="Revenue",
        account_dr_name="Cash",
        account_cr_name="Tuition Revenue"
    )
    assert t.amount == 15000.0
    assert len(t.journal_entries) == 2

def test_zero_liability_enforcement(engine):
    with pytest.raises(ValueError, match="System configured for Zero-Liability Educational Model"):
        engine.add_raw_transaction(
            date_str="2026-04-01",
            description="Bank Loan",
            amount=5000.0,
            transaction_type_str="Equity Adjustment",
            account_dr_name="Cash",
            account_cr_name="Bank Loan Liability"
        )

def test_financial_statements(engine):
    # 1. Beginning balance
    engine.add_raw_transaction(
        date_str="2026-04-01",
        description="Opening balance",
        amount=100000.0,
        transaction_type_str="Equity Adjustment",
        account_dr_name="Cash",
        account_cr_name="Beginning Fund Balance"
    )

    # 2. Revenue
    engine.add_raw_transaction(
        date_str="2026-04-05",
        description="Tuition fees",
        amount=20000.0,
        transaction_type_str="Revenue",
        account_dr_name="Cash",
        account_cr_name="Tuition Revenue"
    )

    # 3. Expense
    engine.add_raw_transaction(
        date_str="2026-04-10",
        description="Staff salaries",
        amount=15000.0,
        transaction_type_str="Expense",
        account_dr_name="Salaries & Benefits",
        account_cr_name="Cash"
    )

    income_stmt, balance_sheet = engine.generate_financial_statements(2026, 4)

    assert income_stmt['Net Income'] == 5000.0
    assert balance_sheet['Total Assets'] == 105000.0
    assert balance_sheet['Equity']['Total Equity'] == 105000.0
