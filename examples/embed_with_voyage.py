#!/usr/bin/env python3
import os
import json
import requests
import argparse
from typing import List, Dict, Any

# Configuration
DEFAULT_SERVER_URL = "http://localhost:7779"
DEFAULT_IMAGE_DIR = os.path.expanduser("~/Videos/screenRecordings")
VOYAGE_API_URL = "https://api.voyageai.com/v1/multimodalembeddings"

def get_voyage_api_key() -> str:
    """Get the Voyage API key from environment variable"""
    api_key = os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        raise ValueError("VOYAGE_API_KEY environment variable not set")
    return api_key

def load_directory(server_url: str, directory_path: str) -> Dict[str, Any]:
    """Load a directory of images into the image server"""
    response = requests.post(
        f"{server_url}/load-directory",
        json={"path": directory_path}
    )
    response.raise_for_status()
    return response.json()

def get_image_list(server_url: str) -> List[str]:
    """Get list of images from the server"""
    response = requests.get(server_url)
    response.raise_for_status()
    data = response.json()
    return data.get("image_list", [])

def embed_image_with_text(
    server_url: str, 
    image_name: str, 
    text: str,
    api_key: str
) -> Dict[str, Any]:
    """Create an embedding for an image + text using Voyage API"""
    image_url = f"{server_url}/images/{image_name}"
    
    # Verify image is accessible
    img_response = requests.head(image_url)
    img_response.raise_for_status()
    
    # Call Voyage API
    payload = {
        "inputs": [
            {
                "content": [
                    {
                        "type": "text",
                        "text": text
                    },
                    {
                        "type": "image_url",
                        "image_url": image_url
                    }
                ]
            }
        ],
        "model": "voyage-multimodal-3"
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        VOYAGE_API_URL,
        headers=headers,
        json=payload
    )
    
    response.raise_for_status()
    return response.json()

def unload_directory(server_url: str) -> Dict[str, Any]:
    """Unload the current directory from the server"""
    response = requests.post(f"{server_url}/unload")
    response.raise_for_status()
    return response.json()

def main():
    parser = argparse.ArgumentParser(description="Embed images with text using Voyage API")
    parser.add_argument("--server", default=DEFAULT_SERVER_URL, help="Image server URL")
    parser.add_argument("--dir", default=DEFAULT_IMAGE_DIR, help="Directory of images to load")
    parser.add_argument("--image", help="Specific image to embed (if omitted, first image is used)")
    parser.add_argument("--text", default="An image description", help="Text to embed with the image")
    
    args = parser.parse_args()
    
    try:
        # Get API key
        api_key = get_voyage_api_key()
        
        # Load directory
        print(f"Loading directory: {args.dir}")
        load_result = load_directory(args.server, args.dir)
        print(f"Loaded {load_result['image_count']} images")
        
        # Get image list
        images = get_image_list(args.server)
        if not images:
            print("No images found in directory")
            return
        
        # Select image
        image_name = args.image if args.image else images[0]
        print(f"Using image: {image_name}")
        
        # Create embedding
        print(f"Creating embedding with text: '{args.text}'")
        embedding_result = embed_image_with_text(args.server, image_name, args.text, api_key)
        
        # Print result
        print("\nEmbedding Result:")
        print(json.dumps(embedding_result, indent=2))
        
        # Unload directory
        print("\nUnloading directory")
        unload_result = unload_directory(args.server)
        print(unload_result["message"])
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 