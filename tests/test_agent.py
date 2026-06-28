import unittest
from unittest.mock import MagicMock, patch
from src.agent import AIAgent

class TestAIAgent(unittest.TestCase):
    def setUp(self):
        self.mock_engine = MagicMock()
        # Mocking Groq client to avoid actual API calls
        with patch('src.agent.Groq') as MockGroq:
            self.agent = AIAgent(self.mock_engine)

    def test_process_command_generate_books(self):
        self.mock_engine.generate_financial_statements.return_value = (
            {'Total Revenue': 1000, 'Total Expense': 500, 'Net Income': 500},
            {'Assets': {'Cash': 1500}, 'Total Assets': 1500, 'Equity': {'Retained Earnings (Total Net Income)': 500, 'Total Equity': 500}}
        )

        report = self.agent.process_command("Generate April 2026 Books")
        self.assertIn("# Financial Report - 4/2026", report)
        self.assertIn("**Net Income** | **$500.00**", report)
        self.assertIn("Retained Earnings (Total Net Income) | $500.00", report)
        self.mock_engine.generate_financial_statements.assert_called_with(2026, 4)

if __name__ == '__main__':
    unittest.main()
