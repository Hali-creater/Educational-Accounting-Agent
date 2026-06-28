# AI Educational Accounting System

This is an AI-powered RAG agent for school/college accounting with a zero-liability model.

## Features
- **Zero-Liability Enforcement**: Rejects any transaction involving liabilities.
- **Double-Entry Journalizing**: Automatically converts raw text to Dr./Cr. entries.
- **Financial Statement Generation**: Monthly Income Statements and Balance Sheets.
- **AI-Powered Parsing**: Uses Groq (LLama 3) to parse natural language transactions.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
Set your `GROQ_API_KEY` in a `.env` file.
```bash
python -m src.main
```

## Example Commands
- `add Collected $15,000 in April cash for tuition`
- `add Paid $5,000 for teacher salaries in April`
- `generate April 2026 books`
