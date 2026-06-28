from datetime import datetime, timezone
from sqlalchemy import extract, and_, or_, func
from src.models import Transaction, JournalEntry, Account, AccountCategory, TransactionType
import pandas as pd

class AccountingEngine:
    def __init__(self, session):
        self.session = session

    def add_raw_transaction(self, date_str, description, amount, transaction_type_str, account_dr_name, account_cr_name):
        date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        # Determine transaction type
        try:
            transaction_type = TransactionType(transaction_type_str)
        except ValueError:
            # Fallback if AI gives slightly different string
            if "Revenue" in transaction_type_str: transaction_type = TransactionType.REVENUE
            elif "Expense" in transaction_type_str: transaction_type = TransactionType.EXPENSE
            elif "Asset" in transaction_type_str: transaction_type = TransactionType.ASSET_ACQUISITION
            else: transaction_type = TransactionType.EQUITY_ADJUSTMENT

        # Ensure accounts exist and assign categories based on transaction type
        dr_account = self.get_or_create_account_from_transaction(account_dr_name, transaction_type, is_dr=True)
        cr_account = self.get_or_create_account_from_transaction(account_cr_name, transaction_type, is_dr=False)

        # Zero-Liability Enforcement
        if "liability" in account_dr_name.lower() or "liability" in account_cr_name.lower():
             raise ValueError("System configured for Zero-Liability Educational Model. Transaction rejected.")

        transaction = Transaction(
            date=date,
            description=description,
            amount=amount,
            transaction_type=transaction_type
        )
        self.session.add(transaction)
        self.session.flush()

        # Journalizing
        dr_entry = JournalEntry(transaction_id=transaction.id, account_id=dr_account.id, debit=amount, credit=0.0)
        cr_entry = JournalEntry(transaction_id=transaction.id, account_id=cr_account.id, debit=0.0, credit=amount)

        self.session.add(dr_entry)
        self.session.add(cr_entry)
        self.session.commit()
        return transaction

    def get_or_create_account_from_transaction(self, name, transaction_type, is_dr):
        account = self.session.query(Account).filter_by(name=name).first()
        if not account:
            category = self.infer_category_advanced(name, transaction_type, is_dr)
            account = Account(name=name, category=category)
            self.session.add(account)
            self.session.flush()
        return account

    def infer_category_advanced(self, name, transaction_type, is_dr):
        # Improved categorization logic
        name_lower = name.lower()
        if "cash" in name_lower or "bank" in name_lower or "receivable" in name_lower or "fixed asset" in name_lower or "inventory" in name_lower:
            return AccountCategory.ASSET

        if "revenue" in name_lower or "fees" in name_lower or "donation" in name_lower:
            return AccountCategory.REVENUE

        if "expense" in name_lower or "salary" in name_lower or "utility" in name_lower or "maintenance" in name_lower:
            return AccountCategory.EXPENSE

        if "equity" in name_lower or "fund balance" in name_lower or "retained earnings" in name_lower:
            return AccountCategory.EQUITY

        # Contextual inference
        if transaction_type == TransactionType.REVENUE:
            return AccountCategory.ASSET if is_dr else AccountCategory.REVENUE
        if transaction_type == TransactionType.EXPENSE:
            return AccountCategory.EXPENSE if is_dr else AccountCategory.ASSET
        if transaction_type == TransactionType.ASSET_ACQUISITION:
            return AccountCategory.ASSET
        if transaction_type == TransactionType.EQUITY_ADJUSTMENT:
            return AccountCategory.EQUITY if not is_dr else AccountCategory.ASSET

        return AccountCategory.ASSET # Default

    def generate_trial_balance(self, year, month, cumulative=False):
        # End date for the period
        if month == 12:
            end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc)

        query = self.session.query(JournalEntry).join(Transaction)
        if cumulative:
            query = query.filter(Transaction.date < end_date)
        else:
            query = query.filter(
                extract('year', Transaction.date) == year,
                extract('month', Transaction.date) == month
            )

        entries = query.all()

        ledger = {}
        for entry in entries:
            acc_name = entry.account.name
            if acc_name not in ledger:
                ledger[acc_name] = {'debit': 0.0, 'credit': 0.0, 'category': entry.account.category}
            ledger[acc_name]['debit'] += entry.debit
            ledger[acc_name]['credit'] += entry.credit

        trial_balance = []
        total_debits = 0.0
        total_credits = 0.0

        for acc_name, balances in ledger.items():
            if balances['category'] in [AccountCategory.ASSET, AccountCategory.EXPENSE]:
                balance = balances['debit'] - balances['credit']
                if balance > 0:
                    trial_balance.append({'Account': acc_name, 'Debit': balance, 'Credit': 0.0})
                    total_debits += balance
                elif balance < 0:
                    trial_balance.append({'Account': acc_name, 'Debit': 0.0, 'Credit': -balance})
                    total_credits += -balance
            else:
                balance = balances['credit'] - balances['debit']
                if balance > 0:
                    trial_balance.append({'Account': acc_name, 'Debit': 0.0, 'Credit': balance})
                    total_credits += balance
                elif balance < 0:
                    trial_balance.append({'Account': acc_name, 'Debit': -balance, 'Credit': 0.0})
                    total_debits += -balance

        if abs(total_debits - total_credits) > 0.001:
            raise ValueError(f"Trial Balance Error: Total Debits ({total_debits}) != Total Credits ({total_credits})")

        return pd.DataFrame(trial_balance), total_debits, total_credits

    def generate_financial_statements(self, year, month):
        # 1. Income Statement (Period specific)
        rev_entries = self.session.query(JournalEntry).join(Transaction).join(Account).filter(
            extract('year', Transaction.date) == year,
            extract('month', Transaction.date) == month,
            Account.category == AccountCategory.REVENUE
        ).all()

        exp_entries = self.session.query(JournalEntry).join(Transaction).join(Account).filter(
            extract('year', Transaction.date) == year,
            extract('month', Transaction.date) == month,
            Account.category == AccountCategory.EXPENSE
        ).all()

        total_revenue = sum(e.credit - e.debit for e in rev_entries)
        total_expense = sum(e.debit - e.credit for e in exp_entries)
        net_income = total_revenue - total_expense

        # 2. Balance Sheet (Cumulative)
        if month == 12:
            end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc)

        # Assets (Cumulative)
        asset_balances = self.session.query(
            Account.name,
            func.sum(JournalEntry.debit - JournalEntry.credit).label('balance')
        ).join(JournalEntry).join(Transaction).filter(
            Transaction.date < end_date,
            Account.category == AccountCategory.ASSET
        ).group_by(Account.name).all()

        assets_dict = {name: bal for name, bal in asset_balances if abs(bal) > 0.001}
        total_assets = sum(assets_dict.values())

        # Equity (Cumulative)
        # Including historical Net Income + Beginning balances
        equity_balances = self.session.query(
            Account.name,
            func.sum(JournalEntry.credit - JournalEntry.debit).label('balance')
        ).join(JournalEntry).join(Transaction).filter(
            Transaction.date < end_date,
            Account.category == AccountCategory.EQUITY
        ).group_by(Account.name).all()

        # We also need to include Net Income from ALL previous periods up to end_date
        total_historical_revenue = self.session.query(func.sum(JournalEntry.credit - JournalEntry.debit)).join(Transaction).join(Account).filter(
            Transaction.date < end_date,
            Account.category == AccountCategory.REVENUE
        ).scalar() or 0.0

        total_historical_expense = self.session.query(func.sum(JournalEntry.debit - JournalEntry.credit)).join(Transaction).join(Account).filter(
            Transaction.date < end_date,
            Account.category == AccountCategory.EXPENSE
        ).scalar() or 0.0

        total_retained_earnings = total_historical_revenue - total_historical_expense

        equity_dict = {name: bal for name, bal in equity_balances if abs(bal) > 0.001}
        total_equity = sum(equity_dict.values()) + total_retained_earnings

        income_statement = {
            'Total Revenue': total_revenue,
            'Total Expense': total_expense,
            'Net Income': net_income
        }

        balance_sheet = {
            'Assets': assets_dict,
            'Total Assets': total_assets,
            'Equity': {
                **equity_dict,
                'Retained Earnings (Total Net Income)': total_retained_earnings,
                'Total Equity': total_equity
            }
        }

        return income_statement, balance_sheet
