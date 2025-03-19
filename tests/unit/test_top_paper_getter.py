"""
Unit tests for the top_paper_getter module.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from tools.top_paper_getter import _get_top_paper_by_date

# Sample test data
SAMPLE_PAPER = {
    "paper_id": "2503.14456",
    "arxiv_id": "2503.14456",
    "title": "Test Paper Title",
    "authors": ["Author 1", "Author 2"],
    "upvotes": 42,
    "date": datetime.now().strftime("%Y-%m-%d")
}

class TestTopPaperGetter(unittest.TestCase):
    """Test the top_paper_getter module functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.today = datetime.now().strftime("%Y-%m-%d")
    
    def tearDown(self):
        """Tear down test fixtures."""
        pass

    @patch('tools.top_paper_getter.load_dataset')
    @patch('tools.top_paper_getter._get_top_paper_from_legacy_dataset')
    def test_get_top_paper_by_date(self, mock_legacy_func, mock_load_dataset):
        """Test the _get_top_paper_by_date function."""
        # Setup the load_dataset call to raise an exception
        mock_load_dataset.side_effect = Exception("Dataset not found")
        
        # Setup the legacy function to return our sample paper
        mock_legacy_func.return_value = SAMPLE_PAPER
        
        # Call the function
        result = _get_top_paper_by_date(self.today)
        
        # Assert the result
        self.assertEqual(result, SAMPLE_PAPER)
        
        # Verify the load_dataset was called
        mock_load_dataset.assert_called_once()
        
        # Verify the legacy function was called
        mock_legacy_func.assert_called_once_with(self.today, 7)  # Default max_days_to_look_back is 7

if __name__ == '__main__':
    unittest.main() 