"""
Unit tests for the agent_utils module.
"""

import unittest
from unittest.mock import patch, MagicMock
import asyncio
import json
from agent_utils import (
    check_slack_posting,
    initialize_agent,
    format_handoff_data,
    load_and_validate_env
)

# Helper to run async tests
def async_test(coro):
    """Decorator for async test methods."""
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper

class TestAgentUtils(unittest.TestCase):
    """Test the agent_utils module functions."""

    def test_check_slack_posting_success(self):
        """Test the check_slack_posting function with successful posting."""
        # Create a mock result with successful Slack posting
        mock_result = MagicMock()
        mock_result.new_items = [
            {
                "type": "tool_use",
                "id": "call_123",
                "tool_use": {
                    "name": "post_paper_to_slack",
                    "input": {
                        "title": "Test Paper",
                        "arxiv_id": "2503.14456",
                        "upvotes": 42,
                        "pdf_url": "https://arxiv.org/pdf/2503.14456",
                        "summary": "Test summary",
                        "channel": "#ai-papers-and-research"
                    }
                }
            },
            {
                "type": "tool_result",
                "id": "call_123_result",
                "tool_result": {
                    "success": True,
                    "message_url": "https://slack.com/message/123",
                    "channel": "#ai-papers-and-research"
                }
            }
        ]
        
        # Call the function
        result = check_slack_posting(mock_result)
        
        # Assert
        self.assertTrue(result["slack_post_successful"])
        self.assertEqual(result["message_url"], "https://slack.com/message/123")
        self.assertEqual(result["channel"], "#ai-papers-and-research")

    def test_check_slack_posting_failure(self):
        """Test the check_slack_posting function with failed posting."""
        # Create a mock result with failed Slack posting
        mock_result = MagicMock()
        mock_result.new_items = [
            {
                "type": "tool_use",
                "id": "call_123",
                "tool_use": {
                    "name": "post_paper_to_slack",
                    "input": {
                        "title": "Test Paper",
                        "arxiv_id": "2503.14456",
                        "upvotes": 42,
                        "pdf_url": "https://arxiv.org/pdf/2503.14456",
                        "summary": "Test summary",
                        "channel": "#ai-papers-and-research"
                    }
                }
            },
            {
                "type": "tool_result",
                "id": "call_123_result",
                "tool_result": {
                    "success": False,
                    "error": "API error"
                }
            }
        ]
        
        # Call the function
        result = check_slack_posting(mock_result)
        
        # Assert
        self.assertFalse(result["slack_post_successful"])
        self.assertEqual(result["error"], "API error")

    def test_check_slack_posting_no_call(self):
        """Test the check_slack_posting function with no Slack tool call."""
        # Create a mock result with no Slack posting
        mock_result = MagicMock()
        mock_result.new_items = [
            {
                "type": "tool_use",
                "id": "call_123",
                "tool_use": {
                    "name": "web_search",
                    "input": {
                        "query": "test query"
                    }
                }
            },
            {
                "type": "tool_result",
                "id": "call_123_result",
                "tool_result": {
                    "results": ["result1", "result2"]
                }
            }
        ]
        
        # Call the function
        result = check_slack_posting(mock_result)
        
        # Assert
        self.assertFalse(result["slack_post_successful"])
        self.assertEqual(result["error"], "No post_paper_to_slack tool call found")

    def test_format_handoff_data(self):
        """Test the format_handoff_data function."""
        # Create test data
        paper_data = {
            "title": "Test Paper",
            "arxiv_id": "2503.14456",
            "upvotes": 42,
            "pdf_url": "https://arxiv.org/pdf/2503.14456",
            "date": "2023-05-15"
        }
        
        # Call the function
        result = format_handoff_data(paper_data)
        
        # Assert
        self.assertIsInstance(result, dict)
        self.assertEqual(result["paper_title"], "Test Paper")
        self.assertEqual(result["arxiv_id"], "2503.14456")
        self.assertEqual(result["upvotes"], 42)
        self.assertEqual(result["pdf_url"], "https://arxiv.org/pdf/2503.14456")

    @patch('os.environ.get')
    def test_load_and_validate_env_success(self, mock_environ_get):
        """Test the load_and_validate_env function with all required variables set."""
        # Mock the environment variables
        mock_environ_get.side_effect = lambda key, default=None: {
            "OPENAI_API_KEY": "test-openai-key",
            "SLACK_API_TOKEN": "test-slack-token",
            "SLACK_CHANNEL": "#test-channel"
        }.get(key, default)
        
        # Call the function
        result = load_and_validate_env()
        
        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["slack_channel"], "#test-channel")

    @patch('os.environ.get')
    def test_load_and_validate_env_missing_openai_key(self, mock_environ_get):
        """Test the load_and_validate_env function with missing OpenAI API key."""
        # Mock the environment variables with missing OpenAI key
        mock_environ_get.side_effect = lambda key, default=None: {
            "OPENAI_API_KEY": None,
            "SLACK_API_TOKEN": "test-slack-token",
            "SLACK_CHANNEL": "#test-channel"
        }.get(key, default)
        
        # Call the function
        result = load_and_validate_env()
        
        # Assert
        self.assertFalse(result["success"])
        self.assertIn("OPENAI_API_KEY is required", result["error"])

    @patch('os.environ.get')
    def test_load_and_validate_env_missing_slack_token(self, mock_environ_get):
        """Test the load_and_validate_env function with missing Slack API token."""
        # Mock the environment variables with missing Slack token
        mock_environ_get.side_effect = lambda key, default=None: {
            "OPENAI_API_KEY": "test-openai-key",
            "SLACK_API_TOKEN": None,
            "SLACK_CHANNEL": "#test-channel"
        }.get(key, default)
        
        # Call the function
        result = load_and_validate_env()
        
        # Assert
        self.assertFalse(result["success"])
        self.assertIn("SLACK_API_TOKEN is required", result["error"])

    @patch('openai.OpenAI')
    @patch('agent_utils.load_and_validate_env')
    @async_test
    async def test_initialize_agent_success(self, mock_load_env, mock_openai):
        """Test the initialize_agent function with successful initialization."""
        # Mock the load_and_validate_env function
        mock_load_env.return_value = {
            "success": True,
            "openai_api_key": "test-openai-key",
            "slack_api_token": "test-slack-token",
            "slack_channel": "#test-channel"
        }
        
        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Create a mock agent and assistant
        mock_assistant = MagicMock()
        mock_agent = MagicMock()
        
        # Mock the create_assistant method
        mock_client.beta.assistants.create.return_value = mock_assistant
        
        # Mock the create_and_run method
        mock_client.beta.assistants.return_value = mock_agent
        
        # Call the function
        result = await initialize_agent("test_instructions", "test_name", [])
        
        # Assert
        self.assertIsNotNone(result)
        mock_client.beta.assistants.create.assert_called_once()

    @patch('agent_utils.load_and_validate_env')
    @async_test
    async def test_initialize_agent_env_failure(self, mock_load_env):
        """Test the initialize_agent function with environment validation failure."""
        # Mock the load_and_validate_env function to return failure
        mock_load_env.return_value = {
            "success": False,
            "error": "Missing required environment variables"
        }
        
        # Call the function and expect an exception
        with self.assertRaises(Exception) as context:
            await initialize_agent("test_instructions", "test_name", [])
        
        # Assert
        self.assertIn("Missing required environment variables", str(context.exception))

if __name__ == '__main__':
    unittest.main() 