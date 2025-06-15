import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import os
import tempfile
from PIL import Image
from image_vectorizer import ImageVectorizer
from dotenv import load_dotenv
load_dotenv("../.env")
class TestImageVectorizer(unittest.TestCase):
    def setUp(self):
        self.vectorizer = ImageVectorizer()
    
    def test_search_image(self):
        result = self.vectorizer.search_images("white cat", n_results=1)
        print(result)
    #     # Create a temporary test image
    #     self.test_image_path = os.path.join(tempfile.mkdtemp(), "test_image.jpg")
    #     img = Image.new('RGB', (100, 100), color='red')
    #     img.save(self.test_image_path)

    # def test_init(self):
    #     """Test initialization of ImageVectorizer"""
    #     self.assertIsNotNone(self.vectorizer.embedding_function)
    #     self.assertIsNotNone(self.vectorizer.collection)

    # # Removed test_get_image_embedding and test_get_text_embedding since we now let ChromaDB handle embeddings directly

    # def test_index_directory(self):
    #     """Test indexing a directory of images"""
    #     # Create a temporary directory with test images
    #     test_dir = tempfile.mkdtemp()
    #     test_image_paths = []
        
    #     # Create a few test images
    #     for i in range(3):
    #         path = os.path.join(test_dir, f"test_{i}.jpg")
    #         img = Image.new('RGB', (100, 100), color='red')
    #         img.save(path)
    #         test_image_paths.append(path)

    #     # Test indexing
    #     with patch.object(self.vectorizer.collection, 'add') as mock_add:
    #         self.vectorizer.index_directory(test_dir)
            
    #         # Verify the number of calls matches number of test images
    #         self.assertEqual(mock_add.call_count, 3)
            
    #         # Verify the correct parameters were passed
    #         for i, call_args in enumerate(mock_add.call_args_list):
    #             args, kwargs = call_args
    #             self.assertEqual(kwargs['documents'], [test_image_paths[i]])
    #             self.assertEqual(kwargs['ids'], [test_image_paths[i]])
    #             self.assertEqual(kwargs['metadatas'][0]['filename'], f"test_{i}.jpg")

    # def test_search_images(self):
    #     """Test searching for images"""
    #     # Mock the collection's query method
    #     with patch.object(self.vectorizer.collection, 'query') as mock_query:
    #         mock_query.return_value = {
    #             'ids': [['test1']],
    #             'documents': [['/path/to/test.jpg']],
    #             'distances': [[0.5]],
    #             'metadatas': [[{'filename': 'test.jpg'}]]
    #         }

    #         # Test search
    #         results = self.vectorizer.search_images("test query", n_results=1)
            
    #         # Verify query was called with correct parameters
    #         mock_query.assert_called_once_with(
    #             query_texts=["test query"],
    #             n_results=1
    #         )
            
    #         # Verify results format
    #         self.assertEqual(len(results), 1)
    #         self.assertIn("image_path", results[0])
    #         self.assertIn("similarity_score", results[0])
    #         self.assertIn("metadata", results[0])

    # def tearDown(self):
    #     """Clean up test files"""
    #     if os.path.exists(self.test_image_path):
    #         os.remove(self.test_image_path)

if __name__ == '__main__':
    unittest.main()