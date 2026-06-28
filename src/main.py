import sys
from src.models import init_db, get_engine
from src.engine import AccountingEngine
from src.agent import AIAgent

def main():
    engine_db = get_engine()
    session = init_db(engine_db)
    accounting_engine = AccountingEngine(session)
    agent = AIAgent(accounting_engine)

    print("Welcome to the AI Educational Accounting System")
    print("-----------------------------------------------")
    print("Available commands:")
    print("1. add [raw transaction text]")
    print("2. generate [Month] [Year] books")
    print("3. quit")
    print("")

    while True:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue

            if user_input.lower() == 'quit':
                break

            if user_input.lower().startswith("add "):
                raw_text = user_input[4:]
                print(f"Parsing: {raw_text}...")

                # In a real scenario, this calls Groq.
                # For demo if no API key, we can simulate or just fail gracefully.
                parsed = agent.parse_transaction(raw_text)
                if parsed:
                    print(f"Parsed JSON: {parsed}")
                    try:
                        accounting_engine.add_raw_transaction(
                            date_str=parsed['date'],
                            description=parsed['description'],
                            amount=parsed['amount'],
                            transaction_type_str=parsed['type'],
                            account_dr_name=parsed['account_dr'],
                            account_cr_name=parsed['account_cr']
                        )
                        print("Transaction recorded successfully.")
                    except Exception as e:
                        session.rollback()
                        print(f"Error recording transaction: {e}")
                else:
                    print("Failed to parse transaction. Check your GROQ_API_KEY.")

            elif "generate" in user_input.lower():
                report = agent.process_command(user_input)
                print("\n" + report + "\n")

            else:
                print("Unknown command.")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
