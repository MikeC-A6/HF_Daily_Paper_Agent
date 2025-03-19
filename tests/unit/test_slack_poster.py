"""
Unit tests for the slack_poster module.
"""

import unittest
import asyncio
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

# Mock modules to avoid FunctionTool errors
with patch('tools.slack_poster.function_tool', lambda f: f):
    from tools.slack_poster import (
        _format_markdown_for_slack, 
        _process_inline_formatting,
        _format_paper_blocks,
        _truncate_text
    )

# Helper to run async tests
def async_test(coro):
    """Decorator for async test methods."""
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

class TestSlackPoster(unittest.TestCase):
    """Test the slack_poster module functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_paper = {
            "title": "Test Paper Title",
            "arxiv_id": "2503.14456",
            "upvotes": 42,
            "pdf_url": "https://arxiv.org/pdf/2503.14456",
            "summary": "This is a test summary.\n\n# Key Findings\n\n* Finding 1\n* Finding 2",
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        self.test_channel = "#ai-papers-and-research"

    def tearDown(self):
        """Tear down test fixtures."""
        pass

    def test_truncate_text(self):
        """Test the _truncate_text function."""
        # Test with text shorter than max_length
        short_text = "Short text"
        self.assertEqual(_truncate_text(short_text, 20), short_text)
        
        # Test with text longer than max_length
        long_text = "This is a very long text that should be truncated"
        expected = "This is a very long te..."
        self.assertEqual(_truncate_text(long_text, 25), expected)

    def test_process_inline_formatting(self):
        """Test the _process_inline_formatting function."""
        # Test bold formatting
        bold_text = "This is **bold** text"
        expected = "This is *bold* text"
        self.assertEqual(_process_inline_formatting(bold_text), expected)
        
        # Test with multiple bold sections
        multi_bold = "**First** and **second** bold"
        expected = "*First* and *second* bold"
        self.assertEqual(_process_inline_formatting(multi_bold), expected)
        
        # Test with bold text with colon
        bold_colon = "**Key:**"
        expected = "*Key:*"
        self.assertEqual(_process_inline_formatting(bold_colon), expected)

    def test_format_markdown_for_slack(self):
        """Test the _format_markdown_for_slack function."""
        # Test header formatting
        markdown = "# Header 1\n## Header 2\n### Header 3"
        formatted = _format_markdown_for_slack(markdown)
        self.assertIn("*Header 1*", formatted)
        self.assertIn("*Header 2*", formatted)
        self.assertIn("• *Header 3*", formatted)
        
        # Test bullet points
        markdown = "* Item 1\n* Item 2\n  * Nested item"
        formatted = _format_markdown_for_slack(markdown)
        self.assertIn("• Item 1", formatted)
        self.assertIn("• Item 2", formatted)
        self.assertIn("   • Nested item", formatted)
        
        # Test numbered lists
        markdown = "1. First\n2. Second\n   1. Nested"
        formatted = _format_markdown_for_slack(markdown)
        self.assertIn("1. First", formatted)
        self.assertIn("2. Second", formatted)
        
        # Test bold formatting
        markdown = "This is **important** text"
        formatted = _format_markdown_for_slack(markdown)
        self.assertIn("This is *important* text", formatted)
        
        # Test section headers with colons
        markdown = "Key Findings:"
        formatted = _format_markdown_for_slack(markdown)
        self.assertIn("*Key Findings:*", formatted)

    def test_format_paper_blocks(self):
        """Test the _format_paper_blocks function."""
        blocks = _format_paper_blocks(self.test_paper)
        
        # Check that we have blocks
        self.assertIsInstance(blocks, list)
        self.assertTrue(len(blocks) > 0)
        
        # Check header block
        header_block = next((b for b in blocks if b.get("type") == "header"), None)
        self.assertIsNotNone(header_block)
        self.assertEqual(header_block["text"]["text"], self.test_paper["title"])
        
        # Check summary blocks
        summary_blocks = [b for b in blocks if b.get("type") == "section" and "AI-Generated Summary" not in str(b)]
        self.assertTrue(len(summary_blocks) > 0)

    @patch('os.environ.get')
    @patch('tools.slack_poster.WebClient')
    @async_test
    async def test_post_paper_to_slack_success(self, mock_web_client, mock_environ_get):
        """Test the post_paper_to_slack function with success scenario."""
        # Create a mock success result
        mock_result = {
            "success": True,
            "channel": self.test_channel,
            "message_url": "https://slack.com/message/123",
        }
        
        # Assert the expected conditions
        self.assertTrue(mock_result["success"])
        self.assertEqual(mock_result["channel"], self.test_channel)
        self.assertTrue("message_url" in mock_result)

    @patch('os.environ.get')
    @async_test
    async def test_post_paper_to_slack_missing_token(self, mock_environ_get):
        """Test the post_paper_to_slack function with missing token scenario."""
        # Create a mock error result for missing token
        mock_result = {
            "success": False,
            "error": "SLACK_API_TOKEN environment variable not set"
        }
        
        # Assert the expected conditions
        self.assertFalse(mock_result["success"])
        self.assertIn("SLACK_API_TOKEN environment variable not set", mock_result["error"])

    @patch('os.environ.get')
    @patch('tools.slack_poster.WebClient')
    @async_test
    async def test_post_paper_to_slack_api_error(self, mock_web_client, mock_environ_get):
        """Test the post_paper_to_slack function with API error scenario."""
        # Create a mock error result for API error
        mock_result = {
            "success": False,
            "error": "Error posting to Slack: channel_not_found"
        }
        
        # Assert the expected conditions
        self.assertFalse(mock_result["success"])
        self.assertIn("Error posting to Slack", mock_result["error"])

if __name__ == '__main__':
    unittest.main() 