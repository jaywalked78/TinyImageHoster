#!/usr/bin/env python3
import os
import sys
import json
import requests
from typing import List, Dict, Any, Optional

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

def unload_directory(server_url: str) -> Dict[str, Any]:
    """Unload the current directory from the server"""
    response = requests.post(f"{server_url}/unload")
    response.raise_for_status()
    return response.json()

def generate_image_urls(server_url: str, image_names: List[str]) -> List[str]:
    """Generate full URLs for each image"""
    return [f"{server_url}/images/{name}" for name in image_names]

def main():
    # Check args
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <directory_path> [server_url]")
        print(f"Example: {sys.argv[0]} ~/Videos/screenRecordings http://localhost:7779")
        sys.exit(1)
    
    # Get parameters
    directory_path = os.path.expanduser(sys.argv[1])
    server_url = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SERVER_URL
    
    try:
        # Load directory
        load_result = load_directory(server_url, directory_path)
        image_count = load_result["image_count"]
        
        if image_count == 0:
            print(json.dumps({
                "success": False,
                "message": "No images found in directory",
                "image_urls": []
            }))
            sys.exit(0)
        
        # Get image list
        images = get_image_list(server_url)
        
        # Generate URLs
        image_urls = generate_image_urls(server_url, images)
        
        # Output JSON result for n8n to parse
        result = {
            "success": True,
            "message": f"Loaded {image_count} images",
            "directory": directory_path,
            "image_count": image_count,
            "image_urls": image_urls
        }
        
        print(json.dumps(result))
        
    except Exception as e:
        error_result = {
            "success": False,
            "message": str(e),
            "image_urls": []
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    main() 