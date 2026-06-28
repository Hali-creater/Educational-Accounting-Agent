import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class AIAgent:
    def __init__(self, engine):
        self.engine = engine
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY", "dummy_key"))
        self.model = "llama-3.3-70b-versatile" # High speed inference as requested

    def parse_transaction(self, raw_text):
        """Uses Groq to parse raw text into structured JSON."""
        prompt = f"""
        You are an expert AI Accounting System. Parse the following raw transaction text into a structured JSON format.

        Rules:
        1. Categorize into one of: Revenue, Expense, Asset Acquisition, Equity Adjustment.
        2. Identify the Debit account and Credit account based on:
           - Assets and Expenses increase via Debits (Dr.).
           - Revenues and Equity increase via Credits (Cr.).
        3. Zero-Liability Model: Never use liability accounts.

        Raw text: "{raw_text}"

        Expected JSON format:
        {{
            "date": "YYYY-MM-DD",
            "description": "Short description",
            "amount": 0.0,
            "type": "Revenue/Expense/Asset Acquisition/Equity Adjustment",
            "account_dr": "Account Name",
            "account_cr": "Account Name"
        }}

        Respond ONLY with the JSON.
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise accounting parser that outputs only JSON.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
                response_format={"type": "json_object"}
            )

            result = json.loads(chat_completion.choices[0].message.content)
            return result
        except Exception as e:
            # Fallback or error handling
            print(f"Error parsing with AI: {e}")
            return None

    def process_command(self, command):
        """Processes user commands like 'Generate April 2026 Books'."""
        if "generate" in command.lower() and "books" in command.lower():
            # Extract month and year - simple extraction for demo
            # In a real system, use the LLM to extract parameters
            import re
            match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})", command, re.IGNORECASE)
            if match:
                month_str = match.group(1)
                year = int(match.group(2))

                months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
                month = months.index(month_str.lower()) + 1

                return self.generate_report(year, month)

        return "Command not recognized. Try 'Generate [Month] [Year] Books'."

    def generate_report(self, year, month):
        try:
            income_stmt, balance_sheet = self.engine.generate_financial_statements(year, month)

            report = f"# Financial Report - {month}/{year}\n\n"

            report += "## Income Statement\n"
            report += f"| Category | Amount |\n| --- | --- |\n"
            report += f"| Total Revenue | ${income_stmt['Total Revenue']:,.2f} |\n"
            report += f"| Total Expense | ${income_stmt['Total Expense']:,.2f} |\n"
            report += f"| **Net Income** | **${income_stmt['Net Income']:,.2f}** |\n\n"

            report += "## Balance Sheet\n"
            report += "### Assets\n"
            report += "| Account | Balance |\n| --- | --- |\n"
            for acc, bal in balance_sheet['Assets'].items():
                report += f"| {acc} | ${bal:,.2f} |\n"
            report += f"| **Total Assets** | **${balance_sheet['Total Assets']:,.2f}** |\n\n"

            report += "### Equity\n"
            report += "| Account | Balance |\n| --- | --- |\n"
            for acc, bal in balance_sheet['Equity'].items():
                if acc != 'Total Equity':
                    report += f"| {acc} | ${bal:,.2f} |\n"
            report += f"| **Total Equity** | **${balance_sheet['Equity']['Total Equity']:,.2f}** |\n"

            return report
        except Exception as e:
            return f"Error generating report: {str(e)}"
