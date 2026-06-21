import sys
from unittest.mock import MagicMock, AsyncMock

# ---------------------------------------------------------
# Mock the google.antigravity SDK before any imports
# ---------------------------------------------------------
class MockAgent:
    def __init__(self, config):
        self.config = config
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    chat = AsyncMock()

class MockLocalAgentConfig:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class MockImage:
    @staticmethod
    def from_file(path):
        m = MagicMock()
        m.path = path
        return m

mock_policy = MagicMock()
mock_policy.deny_all = MagicMock(return_value="deny_all")
mock_policy.allow = MagicMock(side_effect=lambda x: f"allow_{x}")

# Setup mock modules in sys.modules
mock_google = MagicMock()
mock_antigravity = MagicMock()
mock_antigravity.Agent = MockAgent
mock_antigravity.LocalAgentConfig = MockLocalAgentConfig

mock_types = MagicMock()
mock_types.Image = MockImage

mock_hooks = MagicMock()
mock_hooks.policy = mock_policy

# Register submodules
sys.modules['google'] = mock_google
sys.modules['google.antigravity'] = mock_antigravity
sys.modules['google.antigravity.types'] = mock_types
sys.modules['google.antigravity.hooks'] = mock_hooks

# ---------------------------------------------------------
# Now import the rest of the testing dependencies
# ---------------------------------------------------------
import unittest
from unittest.mock import patch
import sqlite3
import os
import asyncio

import ai_engine

class TestAIEngine(unittest.TestCase):

    def test_local_heuristic_route(self):
        """Test local regex routing with various inputs."""
        # Financial inputs
        self.assertEqual(ai_engine.local_heuristic_route("Spent 15.50 SGD on groceries at Fairprice"), "FINANCIAL")
        self.assertEqual(ai_engine.local_heuristic_route("buy coffee cost 5 SGD"), "FINANCIAL")
        self.assertEqual(ai_engine.local_heuristic_route("expense for gear is high"), "FINANCIAL")
        
        # Athletic inputs
        self.assertEqual(ai_engine.local_heuristic_route("Squats 120kg 3x5, RPE 8. feeling stiff in knee."), "ATHLETIC")
        self.assertEqual(ai_engine.local_heuristic_route("bench reps and sets at gym"), "ATHLETIC")
        self.assertEqual(ai_engine.local_heuristic_route("fatigue index is stiff and sore"), "ATHLETIC")

        # Unknown / ambiguous
        self.assertEqual(ai_engine.local_heuristic_route("Hello world this is some random talk"), "UNKNOWN")

    @patch('sqlite3.connect')
    def test_get_db_success(self, mock_connect):
        """Test get_db() context manager commits on success."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        with ai_engine.get_db() as cursor:
            self.assertEqual(cursor, mock_cursor)
        
        mock_connect.assert_called_once_with(ai_engine.DB_PATH)
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
        mock_conn.rollback.assert_not_called()

    @patch('sqlite3.connect')
    def test_get_db_failure(self, mock_connect):
        """Test get_db() context manager rolls back on SQLite errors."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        with self.assertRaises(sqlite3.Error):
            with ai_engine.get_db():
                raise sqlite3.Error("Mock SQL Error")

        mock_conn.commit.assert_not_called()
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('ai_engine.get_db')
    def test_log_expense(self, mock_get_db):
        """Test log_expense SQL statement formatting and return message."""
        mock_cursor = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_cursor

        # Set mock image blob
        token = ai_engine.current_image_blob.set(b"dummy_blob")
        try:
            res = ai_engine.log_expense("Fairprice", "Groceries", 15.50, "Weekly groceries")
            self.assertIn("Successfully logged expense", res)
            mock_cursor.execute.assert_called_once_with(
                "INSERT INTO transactions (merchant, category, amount_sgd, notes, image_blob) VALUES (?, ?, ?, ?, ?)",
                ("Fairprice", "Groceries", 15.50, "Weekly groceries", b"dummy_blob")
            )
        finally:
            ai_engine.current_image_blob.reset(token)

    @patch('ai_engine.get_db')
    def test_log_workout(self, mock_get_db):
        """Test log_workout SQL statement formatting and fatigue flag joining."""
        mock_cursor = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_cursor

        # Set mock image blob
        token = ai_engine.current_image_blob.set(None)
        try:
            res = ai_engine.log_workout("Squats", 3, 5, 120.0, 8, ["knee stiff", "sore back"])
            self.assertIn("Successfully logged workout", res)
            mock_cursor.execute.assert_called_once_with(
                "INSERT INTO workouts (exercise, sets, reps, weight_kg, rpe, fatigue_flags, image_blob) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("Squats", 3, 5, 120.0, 8, "knee stiff,sore back", None)
            )
        finally:
            ai_engine.current_image_blob.reset(token)

class TestAsyncAIEngine(unittest.IsolatedAsyncioTestCase):

    @patch('ollama.chat')
    async def test_process_input_financial_ollama(self, mock_ollama_chat):
        """Test process_input for financial route via Ollama response."""
        mock_ollama_chat.return_value = {
            'message': {'content': 'financial'}
        }
        
        mock_response = AsyncMock()
        mock_response.text.return_value = "Mock financial logged"
        
        with patch.object(MockAgent, 'chat', return_value=mock_response) as mock_agent_chat:
            res = await ai_engine.process_input("Spent some money at a store")
            self.assertEqual(res, "Mock financial logged")
            mock_ollama_chat.assert_called_once()
            mock_agent_chat.assert_called_once_with("Spent some money at a store")

    @patch('ollama.chat')
    async def test_process_input_athletic_fallback(self, mock_ollama_chat):
        """Test process_input athletic path with local heuristic fallback when Ollama fails."""
        mock_ollama_chat.side_effect = Exception("Ollama offline")
        
        mock_response = AsyncMock()
        mock_response.text.return_value = "Mock athletic logged"

        with patch.object(MockAgent, 'chat', return_value=mock_response) as mock_agent_chat:
            # Athletic input triggers local heuristic route to ATHLETIC
            res = await ai_engine.process_input("Squats 120kg 3x5, RPE 8")
            self.assertEqual(res, "Mock athletic logged")
            mock_ollama_chat.assert_called_once()
            mock_agent_chat.assert_called_once_with("Squats 120kg 3x5, RPE 8")

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=b"image_bytes")
    async def test_process_image(self, mock_open):
        """Test process_image sets ContextVar and runs agent with Image."""
        mock_response = AsyncMock()
        mock_response.text.return_value = "Mock image processed"

        with patch.object(MockAgent, 'chat', return_value=mock_response) as mock_agent_chat:
            res = await ai_engine.process_image("dummy.jpg")
            self.assertEqual(res, "Mock image processed")
            mock_agent_chat.assert_called_once()
            args, kwargs = mock_agent_chat.call_args
            self.assertEqual(args[0][0], "Please analyze this image and log the entry using the correct tool.")
            self.assertEqual(args[0][1].path, "dummy.jpg")

        # Verify open was called correctly
        mock_open.assert_called_once_with("dummy.jpg", "rb")

if __name__ == "__main__":
    unittest.main()
