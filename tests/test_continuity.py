import pytest
from datetime import datetime, timezone
from src.models import init_db, get_engine
from src.engine import AccountingEngine

@pytest.fixture
def engine():
    db_engine = get_engine("sqlite:///:memory:")
    session = init_db(db_engine)
    return AccountingEngine(session)

def test_cumulative_balance_sheet(engine):
    # Jan: Revenue $1000
    engine.add_raw_transaction("2026-01-15", "Jan Revenue", 1000, "Revenue", "Cash", "Tuition Revenue")

    # Feb: Expense $400
    engine.add_raw_transaction("2026-02-10", "Feb Expense", 400, "Expense", "Utilities", "Cash")

    # Generate Feb Books
    income_stmt, balance_sheet = engine.generate_financial_statements(2026, 2)

    # Income Stmt should only show Feb: $400 expense, $0 revenue
    assert income_stmt['Total Revenue'] == 0
    assert income_stmt['Total Expense'] == 400
    assert income_stmt['Net Income'] == -400

    # Balance Sheet should be cumulative
    # Assets: Cash = 1000 (Jan) - 400 (Feb) = 600
    assert balance_sheet['Total Assets'] == 600
    assert balance_sheet['Assets']['Cash'] == 600

    # Equity: Net Income Jan (1000) + Net Income Feb (-400) = 600
    assert balance_sheet['Equity']['Total Equity'] == 600
    assert balance_sheet['Equity']['Retained Earnings (Total Net Income)'] == 600

def test_multi_month_equity_carryover(engine):
    # Start with Equity
    engine.add_raw_transaction("2026-01-01", "Initial Fund", 5000, "Equity Adjustment", "Cash", "Beginning Fund Balance")

    # Jan Profit
    engine.add_raw_transaction("2026-01-20", "Jan Profit", 1000, "Revenue", "Cash", "Tuition Revenue")

    # Check Jan Balance Sheet
    _, bs_jan = engine.generate_financial_statements(2026, 1)
    assert bs_jan['Total Assets'] == 6000
    assert bs_jan['Equity']['Total Equity'] == 6000

    # Check Feb Balance Sheet (no transactions in Feb)
    _, bs_feb = engine.generate_financial_statements(2026, 2)
    assert bs_feb['Total Assets'] == 6000
    assert bs_feb['Equity']['Total Equity'] == 6000
