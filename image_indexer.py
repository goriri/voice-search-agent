#!/usr/bin/env python3
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
from image_vectorizer import ImageVectorizer

def main():
    # Load environment variables
    load_dotenv()
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Index images using Ollama for vector search')
    parser.add_argument('--directory', '-d', type=str, help='Directory containing images to index', 
                       default=os.environ.get('IMAGES_DIR', Path(__file__).parent / "images"))
    parser.add_argument('--db-path', type=str, help='Path to store the vector database',
                       default=os.environ.get('IMAGE_VECTORS_DIR', (Path(__file__).parent / "image_vectors").absolute().as_posix()))
    
    args = parser.parse_args()
    
    print(f"DB Path: {args.db_path}")

    # Create images directory if it doesn't exist
    if not os.path.exists(args.directory):
        os.makedirs(args.directory)
        print(f"Created images directory at {args.directory}")
    
    try:
        # Initialize vectorizer
        image_vectorizer = ImageVectorizer(
            db_path=args.db_path
        )
        
        # Index images
        print(f"Indexing images in {args.directory}...")
        image_vectorizer.index_directory(args.directory)
        print("Indexing complete!")
        
    except Exception as e:
        print(f"Error during indexing: {str(e)}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())