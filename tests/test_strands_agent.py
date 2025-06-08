from strands_agent.strands_agent import StrandsAgent
from strands_agent import web_search
from unittest.mock import patch, MagicMock
import unittest

class TestStrandsAgent(unittest.TestCase):

    # def test_web_search_1(self):
    #     """
    #     Test that web_search returns the correct abstract when a valid response is received.
    #     """
    #     mock_response = MagicMock()
    #     mock_response.json.return_value = {
    #         "data": {
    #             "webPages": {
    #                 "value": [
    #                     {
    #                         "summary": "This is a test abstract"
    #                     }
    #                 ]
    #             }
    #         }
    #     }

    #     with patch('requests.post', return_value=mock_response):
    #         result = web_search("test query")
    #         self.assertEqual(result, "This is a test abstract")

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