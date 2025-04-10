#!/usr/bin/env python3
import os
import json
import requests
import subprocess
import time
import argparse
from pathlib import Path
from datetime import datetime

# Configuration
SERVER_URL = "http://localhost:7779"
SOURCE_DIR = "/home/jason/Videos/screenRecordings/screen_recording_2025_02_20_at_12_14_43_pm"
OUTPUT_DIR = os.path.expanduser("~/Documents/LightweightImageServer/output/json")

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

def is_server_running(server_url=None):
    """Check if the server is running"""
    url = server_url or SERVER_URL
    try:
        response = requests.get(url)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

def start_server(unload_first=False, server_url=None):
    """Start the server"""
    url = server_url or SERVER_URL
    script_dir = os.path.dirname(os.path.realpath(__file__))
    run_script = os.path.join(script_dir, "run_server.sh")
    
    if not os.path.exists(run_script):
        print(f"Error: Could not find {run_script}")
        return False
    
    print(f"Starting server with {run_script}...")
    # Start server in background
    subprocess.Popen([run_script], shell=True)
    
    # Wait for server to start
    max_attempts = 10
    for attempt in range(max_attempts):
        if is_server_running(url):
            print("Server is running!")
            if unload_first:
                print("Unloading any previously loaded directories...")
                try:
                    requests.post(f"{url}/unload")
                    print("Previous directories unloaded.")
                except:
                    print("Error unloading previous directories.")
            return True
        print(f"Waiting for server to start (attempt {attempt+1}/{max_attempts})...")
        time.sleep(1)
    
    print("Failed to start server")
    return False

def load_directory(directory, server_url=None, timeout_minutes=None):
    """Load a directory into the server"""
    url = server_url or SERVER_URL
    print(f"Loading directory: {directory}")
    
    payload = {"path": directory}
    if timeout_minutes is not None:
        payload["timeout_minutes"] = timeout_minutes
    
    response = requests.post(
        f"{url}/load-directory",
        json=payload
    )
    if response.status_code == 200:
        print("Directory loaded successfully!")
        result = response.json()
        print(f"Loaded {result['image_count']} images from {result['directory']}")
        if 'timeout' in result:
            print(f"Timeout: {result['timeout']}")
        return True
    else:
        print(f"Error loading directory: {response.text}")
        return False

def get_image_list(server_url=None):
    """Get list of images from the server"""
    url = server_url or SERVER_URL
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"image_list": []}

def get_server_info(server_url=None):
    """Get detailed server information"""
    url = server_url or SERVER_URL
    response = requests.get(url)
    if response.status_code != 200:
        return None
    
    info = response.json()
    
    # Pretty print timeout information
    if info.get("timeout_minutes"):
        print(f"Auto-unload timeout: {info['timeout_minutes']} minutes")
        if info.get("auto_unload_at"):
            print(f"Will unload at: {info['auto_unload_at']}")
        if info.get("time_remaining"):
            print(f"Time remaining: {info['time_remaining']}")
    else:
        print("No auto-unload timeout set")
        
    return info

def generate_unique_filename(directory_path):
    """Generate a unique filename based on directory name and timestamp"""
    # Extract folder name from path
    folder_name = os.path.basename(directory_path.rstrip('/'))
    
    # Generate timestamp in format YYYYMMDD_HHMMSS
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Combine for the filename
    return f"{folder_name}_{timestamp}.json"

def generate_json(images, server_url=None, output_dir=None, custom_filename=None):
    """Generate JSON with image URLs"""
    url = server_url or SERVER_URL
    output = output_dir or OUTPUT_DIR
    
    if isinstance(images, dict) and "image_list" in images:
        # We received the full server info
        image_list = images["image_list"]
        directory_path = images.get("current_directory", "unknown_dir")
    else:
        # We just received a list of image names
        image_list = images
        directory_path = "unknown_dir"
    
    # Sort image list by filename
    sorted_image_list = sorted(image_list)
    
    # Generate URLs from sorted list
    image_urls = [f"{url}/images/{img}" for img in sorted_image_list]
    
    # Create output data
    output_data = {
        "success": True,
        "directory": directory_path,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": f"Generated URLs for {len(image_urls)} images",
        "count": len(image_urls),
        "image_urls": image_urls,
    }
    
    # Add timeout information if available
    if isinstance(images, dict):
        if images.get("timeout_minutes"):
            output_data["timeout_minutes"] = images["timeout_minutes"]
        if images.get("auto_unload_at"):
            output_data["auto_unload_at"] = images["auto_unload_at"]
        if images.get("time_remaining"):
            output_data["time_remaining"] = images["time_remaining"]
    
    # Determine output filename
    if custom_filename:
        output_file = os.path.join(output, custom_filename)
    else:
        # Generate a unique filename based on the directory name and timestamp
        filename = generate_unique_filename(directory_path)
        output_file = os.path.join(output, filename)
    
    # Save to file
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Saved URLs to {output_file}")
    return output_file

def unload_directory(server_url=None):
    """Unload the current directory"""
    url = server_url or SERVER_URL
    print("Unloading current directory...")
    response = requests.post(f"{url}/unload")
    if response.status_code == 200:
        print("Directory unloaded successfully!")
        return True
    else:
        print(f"Error unloading directory: {response.text}")
        return False

def set_timeout(minutes, server_url=None):
    """Set the server timeout in minutes"""
    url = server_url or SERVER_URL
    print(f"Setting timeout to {minutes} minutes...")
    response = requests.post(f"{url}/timeout/{minutes}")
    if response.status_code == 200:
        result = response.json()
        print(f"Timeout set: {result['message']}")
        return True
    else:
        print(f"Error setting timeout: {response.text}")
        return False

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test image server with specific images")
    parser.add_argument("--dir", type=str, default=SOURCE_DIR, 
                        help="Directory containing the images to load")
    parser.add_argument("--server", type=str, default=SERVER_URL, 
                        help="URL of the image server")
    parser.add_argument("--output", type=str, default=OUTPUT_DIR, 
                        help="Directory to save JSON output")
    parser.add_argument("--unload", action="store_true", 
                        help="Unload directory when done")
    parser.add_argument("--unload-first", action="store_true", 
                        help="Unload any previous directories before loading new ones")
    parser.add_argument("--frames", type=str, 
                        help="Comma-separated list of frame numbers (e.g., '1,2,3,4,5')")
    parser.add_argument("--timeout", type=int, 
                        help="Set timeout in minutes (0 to disable)")
    
    args = parser.parse_args()
    
    # Get command line arguments
    server_url = args.server
    source_dir = os.path.expanduser(args.dir)
    output_dir = os.path.expanduser(args.output)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Start server if not running
    if not is_server_running(server_url):
        if not start_server(args.unload_first, server_url):
            print("Couldn't start the server. Exiting.")
            return
    elif args.unload_first:
        # Server is already running, but we need to unload
        print("Server is running. Unloading any previously loaded directories...")
        try:
            requests.post(f"{server_url}/unload")
            print("Previous directories unloaded.")
        except:
            print("Error unloading previous directories.")
    
    # Set timeout if specified
    if args.timeout is not None:
        set_timeout(args.timeout, server_url)
    
    # Load the directory
    if not load_directory(source_dir, server_url):
        print("Failed to load directory. Exiting.")
        return
    
    # Get server info (includes timeout data)
    server_info = get_server_info(server_url)
    if not server_info:
        print("Failed to get server info. Exiting.")
        return
    
    # Get list of images
    images = server_info.get("image_list", [])
    if not images:
        print("No images found in directory")
        return
    
    # Filter for the specific images
    if args.frames:
        # Use custom frame numbers from arguments
        frame_numbers = [int(n.strip()) for n in args.frames.split(",")]
        target_images = [f"frame_{i:06d}.jpg" for i in frame_numbers]
        found_images = [img for img in images if img in target_images]
    else:
        # Default to frames 1-5
        target_images = [f"frame_{i:06d}.jpg" for i in range(1, 6)]
        found_images = [img for img in images if img in target_images]
    
    if not found_images:
        print(f"Could not find the specified images in {source_dir}")
        print(f"Available images: {images[:5]}...")
        return
    
    print(f"Found {len(found_images)} of the requested images")
    
    # Create a modified copy of server_info with filtered images
    filtered_info = server_info.copy()
    filtered_info["image_list"] = found_images
    
    # Generate JSON with URLs and timeout info
    json_file = generate_json(filtered_info, server_url, output_dir)
    
    # Print the contents of the JSON file
    with open(json_file, "r") as f:
        print("\nGenerated JSON:")
        print(f.read())
    
    # Unload directory if requested
    if args.unload:
        unload_directory(server_url)
    else:
        print("\nImages remain loaded on the server and can be accessed via the URLs.")
        if server_info.get("timeout_minutes"):
            print(f"They will be automatically unloaded after {server_info['timeout_minutes']} minutes.")
            if server_info.get("auto_unload_at"):
                print(f"Estimated unload time: {server_info['auto_unload_at']}")
        print("To unload manually, run: ./unload_directory.sh")

if __name__ == "__main__":
    main() 