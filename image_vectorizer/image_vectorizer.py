import os
from pathlib import Path
import json
from typing import List, Dict, Any, Optional
import uuid
import numpy as np
from PIL import Image
from chromadb import PersistentClient, Settings
import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader


class ImageVectorizer:
    def __init__(self, db_path: str = "image_vectors"):
        """Initialize the ImageVectorizer with ChromaDB and OpenCLIP embedding.
        
        Args:
            db_path: Path to store the vector database
        """
        # Initialize the OpenCLIP embedding function
        self.embedding_function = OpenCLIPEmbeddingFunction()
        
        # Initialize ChromaDB
        self.db_client = PersistentClient(
            path=db_path
        )
        data_loader = ImageLoader()

        self.collection = self.db_client.get_or_create_collection(
            name="image_embeddings",
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.embedding_function,
            data_loader=data_loader
        )

    # Removed _get_image_embedding and _get_text_embedding methods since ChromaDB will handle embeddings

    def index_directory(self, directory: str) -> None:
        """Index all images in a directory.
        
        Args:
            directory: Path to directory containing images
        """
        self.delete_all_images()
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        IMAGE_DIR = directory
        documents = [os.path.join(IMAGE_DIR, img) for img in os.listdir(IMAGE_DIR)]
        uris = [os.path.join(IMAGE_DIR, img) for img in os.listdir(IMAGE_DIR)]
        ids = [str(uuid.uuid4()) for _ in range(len(documents))]

        self.collection.add(
            uris=uris,
            ids=ids,
            metadatas=[{"file": file} for file in documents]
)

    def search_images(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for images similar to the query text.
        
        Args:
            query: Text description to search for
            n_results: Number of results to return
            
        Returns:
            List of dictionaries containing image paths and similarity scores
        """
        # Search in ChromaDB - it will handle the query embedding
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        print(f"Search results for '{query}': {results}")
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "image_path": results['metadatas'][0][i]["file"],
                "similarity_score": float(results['distances'][0][i]),
                "metadata": results['metadatas'][0][i]
            })
            
        return formatted_results
    
    def get_all_images(self) -> List[Dict[str, Any]]:
        """Retrieve images by their IDs.
        
        Args:
            ids: List of image IDs to retrieve. If None, retrieves all images.
            
        Returns:
            List of dictionaries containing image paths and metadata
        """

        
        results = self.collection.get()
        return [{
            "id": doc['id'],
            "image_path": doc['document'],
            "metadata": doc['metadata']
        } for doc in results['documents']]
    
    def delete_all_images(self) -> None:
        """Delete all images from the collection."""
        ids = [x.id for x in self.get_all_images()]
        if not ids:
            print("No images to delete.")
        else:
            print(f"Deleting {len(ids)} images.")
            self.collection.delete(ids=ids)
