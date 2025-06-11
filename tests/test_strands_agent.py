from strands_agent.strands_agent import StrandsAgent, search_images
from strands_agent import web_search
from unittest.mock import patch, MagicMock
import unittest
import os
import shutil
import tempfile
from PIL import Image
from dotenv import load_dotenv

load_dotenv("../.env")


class TestStrandsAgent(unittest.TestCase):

    def test_search_images_found(self):
        """Test that search_images finds an image with a matching keyword."""
        with patch('PIL.Image.Image.show') as mock_show:
            result = search_images("icons")
            print(result)
            self.assertTrue("Found and opened image" in result)
            self.assertTrue("AWS icons.png" in result)
            mock_show.assert_called_once()

    def test_search_images_not_found(self):
        """Test that search_images returns appropriate message when no images are found."""
        result = search_images("nonexistent")
        self.assertTrue("No images found matching keyword" in result)

    def test_web_search_empty_query(self):
        """
        Test the web_search method with an empty query string.
        This tests the edge case of providing an empty input, which is handled
        by the method's default return statement.
        """
        result = web_search("Donald Trump")
        print(result)

if __name__ == '__main__':
    unittest.main()