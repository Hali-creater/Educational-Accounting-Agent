import streamlit as st
import os
import pandas as pd
from datetime import datetime
from src.models import init_db, get_engine
from src.engine import AccountingEngine
from src.agent import AIAgent

# Page config
st.set_page_config(page_title="AI Accounting Agent", layout="wide")

# Initialize Session State
if "engine" not in st.session_state:
    db_engine = get_engine()
    session = init_db(db_engine)
    st.session_state.engine = AccountingEngine(session)
    st.session_state.agent = AIAgent(st.session_state.engine)
    st.session_state.session = session

st.title("🏫 AI Educational Accounting System")
st.markdown("### Zero-Liability Accounting for Schools and Colleges")

# Sidebar for settings and commands
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Groq API Key", type="password", value=os.environ.get("GROQ_API_KEY", ""))
    if api_key:
        st.session_state.agent.client.api_key = api_key

    st.divider()
    st.header("Commands")
    if st.button("Generate April 2026 Books"):
        st.session_state.current_command = "Generate April 2026 Books"

    command_input = st.text_input("Custom Command", placeholder="e.g., Generate May 2026 Books")
    if st.button("Run Command"):
        st.session_state.current_command = command_input

# Main Interface: Transaction Ingestion
st.header("Transaction Ingestion Sheet")
with st.form("add_transaction", clear_on_submit=True):
    raw_text = st.text_area("Add raw transaction text", placeholder="Collected $15,000 in April cash for tuition")
    submitted = st.form_submit_state = st.form_submit_button("Add Transaction")

    if submitted and raw_text:
        with st.spinner("Parsing transaction..."):
            parsed = st.session_state.agent.parse_transaction(raw_text)
            if parsed:
                st.write("**Parsed Data:**", parsed)
                try:
                    st.session_state.engine.add_raw_transaction(
                        date_str=parsed['date'],
                        description=parsed['description'],
                        amount=parsed['amount'],
                        transaction_type_str=parsed['type'],
                        account_dr_name=parsed['account_dr'],
                        account_cr_name=parsed['account_cr']
                    )
                    st.success("Transaction recorded successfully!")
                except Exception as e:
                    st.session_state.session.rollback()
                    st.error(f"Error recording transaction: {e}")
            else:
                st.error("Failed to parse transaction. Please check your API key and connection.")

# Report Generation Display
if "current_command" in st.session_state:
    st.divider()
    st.header("Financial Report")
    with st.spinner("Generating report..."):
        report_md = st.session_state.agent.process_command(st.session_state.current_command)
        st.markdown(report_md)

# Show Recent Transactions
st.divider()
st.header("Recent Transactions")
# In a real app, we'd query the DB and show a dataframe
# For now, we can show the last few transactions from the database
try:
    from src.models import Transaction
    transactions = st.session_state.session.query(Transaction).order_by(Transaction.date.desc()).limit(10).all()
    if transactions:
        data = []
        for t in transactions:
            data.append({
                "Date": t.date.strftime("%Y-%m-%d"),
                "Description": t.description,
                "Amount": f"${t.amount:,.2f}",
                "Type": t.transaction_type.value
            })
        st.table(pd.DataFrame(data))
    else:
        st.write("No transactions found.")
except Exception as e:
    st.write("Error loading transactions.")
