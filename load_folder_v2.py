#!/usr/bin/env python3
import os
import json
import requests
import subprocess
import time
import argparse
import sys
from pathlib import Path
from datetime import datetime
import concurrent.futures
from tqdm import tqdm
import asyncio
import aiohttp
import aiofiles

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded environment variables from .env file")
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables may not be loaded.")

# Try to import PIL for image dimensions
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL not available. Image dimensions will not be shown.")

# Configuration
SERVER_URL = "http://localhost:7779"
DEFAULT_TIMEOUT = 30  # Default timeout in minutes
OUTPUT_DIR = os.path.expanduser("~/Documents/LightweightImageServer/output/json")
# Base directory for screen recordings from .env
FRAME_BASE_DIR = os.environ.get("FRAME_BASE_DIR", "/home/jason/Videos/screenRecordings")
# Number of concurrent workers
MAX_WORKERS = 10
# Batch size for image uploads
BATCH_SIZE = 20

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
    run_script = os.path.join(script_dir, "persistent_run.sh")  # Use persistent mode
    
    if not os.path.exists(run_script):
        # Fall back to regular run script if persistent mode not available
        run_script = os.path.join(script_dir, "run_server.sh")
        if not os.path.exists(run_script):
            print(f"Error: Could not find run scripts")
            return False
    
    print(f"Starting server with {run_script}...")
    
    # Make sure the script is executable
    os.chmod(run_script, 0o755)  # Set execute permission
    
    # Start server in background (using bash explicitly)
    subprocess.Popen(["bash", run_script], shell=False, env=os.environ.copy())
    
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

def load_directory(directory, server_url=None, timeout_minutes=None, verbose=True):
    """Load a directory into the server"""
    url = server_url or SERVER_URL
    print(f"Loading directory: {directory}")
    
    # First, get the list of image files to load
    image_files = []
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
            image_files.append(file)
    
    total_images = len(image_files)
    print(f"Found {total_images} images in directory")
    
    payload = {"path": directory}
    if timeout_minutes is not None:
        payload["timeout_minutes"] = timeout_minutes
    
    # Before making the server request, show what's about to happen
    if verbose:
        print(f"Sending request to {url}/load-directory with payload:")
        print(f"  path: {directory}")
        if timeout_minutes is not None:
            print(f"  timeout_minutes: {timeout_minutes}")
    
    # Make the actual request with timing information
    start_time = time.time()
    if verbose:
        print(f"Starting server request at {datetime.now().strftime('%H:%M:%S')}")
    
    response = requests.post(
        f"{url}/load-directory",
        json=payload
    )
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    if response.status_code == 200:
        result = response.json()
        
        # If verbose is enabled, load images in parallel with real progress tracking
        if verbose and total_images > 0:
            print(f"Server loaded {result['image_count']} images in {elapsed:.2f} seconds")
            print(f"Average time per image: {(elapsed / total_images):.4f} seconds")
            parallel_load_images(image_files, directory, url)
            
        print("\nDirectory loaded successfully!")
        print(f"Loaded {result['image_count']} images from {result['directory']}")
        if 'timeout' in result:
            print(f"Timeout: {result['timeout']}")
        return result
    else:
        print(f"Error loading directory: {response.text}")
        return None

def upload_image_batch(batch, directory, server_url):
    """Upload a batch of images and return results"""
    results = []
    
    for image in batch:
        image_path = os.path.join(directory, image)
        file_size = os.path.getsize(image_path) / 1024  # Size in KB
        
        # Get image dimensions if PIL is available
        dimensions = "Unknown"
        if PIL_AVAILABLE:
            try:
                with Image.open(image_path) as img:
                    dimensions = f"{img.width}x{img.height}"
            except Exception:
                pass
        
        # Make a request to ensure the image is loaded
        try:
            response = requests.get(f"{server_url}/images/{image}", stream=True)
            status = "Success" if response.status_code == 200 else f"Failed ({response.status_code})"
            
            # Just read headers to verify the image is available
            for _ in response.iter_content(chunk_size=8192, decode_unicode=False):
                break
                
            results.append({
                "image": image,
                "size": file_size,
                "dimensions": dimensions,
                "status": status
            })
        except Exception as e:
            results.append({
                "image": image,
                "size": file_size,
                "dimensions": dimensions,
                "status": f"Error: {str(e)}"
            })
    
    return results

async def async_upload_image(session, image, directory, server_url):
    """Asynchronously upload a single image"""
    image_path = os.path.join(directory, image)
    file_size = os.path.getsize(image_path) / 1024  # Size in KB
    
    # Get image dimensions if PIL is available
    dimensions = "Unknown"
    if PIL_AVAILABLE:
        try:
            with Image.open(image_path) as img:
                dimensions = f"{img.width}x{img.height}"
        except Exception:
            pass
    
    # Make a request to ensure the image is loaded
    try:
        async with session.get(f"{server_url}/images/{image}") as response:
            status = "Success" if response.status == 200 else f"Failed ({response.status})"
            # Just read headers to verify the image is available
            await response.read()
                
        return {
            "image": image,
            "size": file_size,
            "dimensions": dimensions,
            "status": status
        }
    except Exception as e:
        return {
            "image": image,
            "size": file_size,
            "dimensions": dimensions,
            "status": f"Error: {str(e)}"
        }

async def async_load_images(image_files, directory, server_url):
    """Load images asynchronously with real progress tracking"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for image in image_files:
            task = async_upload_image(session, image, directory, server_url)
            tasks.append(task)
        
        # Use tqdm to display progress
        results = []
        for f in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Loading images", 
                      unit="img", ncols=100, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"):
            result = await f
            results.append(result)
        
        return results

def parallel_load_images(image_files, directory, server_url):
    """Load images in parallel with real progress tracking using threading"""
    if asyncio.get_event_loop().is_running():
        # Use threading if we're already in an event loop
        return threading_load_images(image_files, directory, server_url)
    else:
        # Use asyncio for better performance
        return asyncio.run(async_load_images(image_files, directory, server_url))

def threading_load_images(image_files, directory, server_url):
    """Load images in parallel with real progress tracking using threading"""
    # Split files into batches
    batches = [image_files[i:i + BATCH_SIZE] for i in range(0, len(image_files), BATCH_SIZE)]
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all batch jobs
        future_to_batch = {
            executor.submit(upload_image_batch, batch, directory, server_url): batch 
            for batch in batches
        }
        
        # Process results as they complete with a progress bar
        completed = 0
        total_batches = len(batches)
        
        # Setup progress bar for batches
        with tqdm(total=total_batches, desc="Processing batches", unit="batch") as batch_pbar:
            for future in concurrent.futures.as_completed(future_to_batch):
                batch_results = future.result()
                results.extend(batch_results)
                batch_pbar.update(1)
                completed += 1
        
        # Print summary
        success_count = sum(1 for r in results if r["status"] == "Success")
        print(f"\nProcessed {len(results)} images: {success_count} successful, {len(results) - success_count} failed")
    
    return results

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
    
    return info

def generate_unique_filename(directory_path):
    """Generate a unique filename based on directory name and timestamp"""
    # Extract folder name from path
    folder_name = os.path.basename(directory_path.rstrip('/'))
    
    # Generate timestamp in format YYYYMMDD_HHMMSS
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Combine for the filename
    return f"{folder_name}_{timestamp}.json"

def generate_json(server_info, server_url=None, output_dir=None, custom_filename=None):
    """Generate JSON with image URLs"""
    url = server_url or SERVER_URL
    output = output_dir or OUTPUT_DIR
    
    # Get image list from server info
    image_list = server_info.get("image_list", [])
    
    # Sort image list by filename
    sorted_image_list = sorted(image_list)
    
    # Generate URLs from sorted list
    image_urls = [f"{url}/images/{img}" for img in sorted_image_list]
    
    # Create output data
    output_data = {
        "success": True,
        "directory": server_info.get("current_directory", ""),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": f"Generated URLs for {len(image_urls)} images",
        "count": len(image_urls),
        "image_urls": image_urls,
    }
    
    # Add timeout information if available
    if server_info.get("timeout_minutes"):
        output_data["timeout_minutes"] = server_info["timeout_minutes"]
    if server_info.get("auto_unload_at"):
        output_data["auto_unload_at"] = server_info["auto_unload_at"]
    if server_info.get("time_remaining"):
        output_data["time_remaining"] = server_info["time_remaining"]
    
    # Determine output filename
    if custom_filename:
        output_file = os.path.join(output, custom_filename)
    else:
        # Generate a unique filename based on the directory name and timestamp
        directory_path = server_info.get("current_directory", "unknown_dir")
        filename = generate_unique_filename(directory_path)
        output_file = os.path.join(output, filename)
    
    # Save to file
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Saved URLs to {output_file}")
    return output_file

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
    # Global variables that need to be modified
    global MAX_WORKERS, BATCH_SIZE
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Load an entire folder of images and generate a JSON file with URLs")
    parser.add_argument("--dir", type=str, required=True, 
                        help="Directory containing the images to load")
    parser.add_argument("--server", type=str, default=SERVER_URL, 
                        help="URL of the image server")
    parser.add_argument("--output", type=str, default=OUTPUT_DIR, 
                        help="Directory to save JSON output")
    parser.add_argument("--unload", action="store_true", 
                        help="Unload directory when done")
    parser.add_argument("--unload-first", action="store_true", 
                        help="Unload any previous directories before loading new ones")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help="Set timeout in minutes (0 to disable)")
    parser.add_argument("--name", type=str,
                        help="Custom name for the output JSON file (without extension)")
    parser.add_argument("--verbose", action="store_true",
                        help="Show detailed debugging information")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS,
                        help=f"Number of concurrent workers (default: {MAX_WORKERS})")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE,
                        help=f"Batch size for image uploads (default: {BATCH_SIZE})")
    
    args = parser.parse_args()
    
    # Update globals with command line arguments
    MAX_WORKERS = args.workers
    BATCH_SIZE = args.batch_size
    
    # Get command line arguments
    server_url = args.server
    
    # Handle directory path: if not absolute, try relative to FRAME_BASE_DIR
    source_dir = args.dir
    if not os.path.isabs(source_dir):
        # Check if it's relative to FRAME_BASE_DIR
        potential_path = os.path.join(FRAME_BASE_DIR, source_dir)
        if os.path.exists(potential_path):
            source_dir = potential_path
    
    # Expand user directory if needed
    source_dir = os.path.expanduser(source_dir)
    output_dir = os.path.expanduser(args.output)
    verbose = args.verbose
    
    if verbose:
        print("\n=== Image Server URL Configuration ===")
        print(f"Server URL:    {server_url}")
        print(f"Base dir:      {FRAME_BASE_DIR}")
        print(f"Source dir:    {source_dir}")
        print(f"Output dir:    {output_dir}")
        print(f"Timeout:       {args.timeout} minutes")
        print(f"Unload first:  {args.unload_first}")
        print(f"Unload after:  {args.unload}")
        print(f"Workers:       {MAX_WORKERS}")
        print(f"Batch size:    {BATCH_SIZE}")
        print("=====================================\n")
    
    # Check if directory exists
    if not os.path.exists(source_dir):
        print(f"Error: Directory '{source_dir}' does not exist")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Start server if not running
    if not is_server_running(server_url):
        if verbose:
            print("Server not running. Attempting to start...")
        
        if not start_server(args.unload_first, server_url):
            print("Couldn't start the server. Exiting.")
            return
        
        if verbose:
            print("Server started successfully.")
    elif args.unload_first:
        # Server is already running, but we need to unload
        if verbose:
            print("Server is running. Unloading any previously loaded directories...")
        
        try:
            requests.post(f"{server_url}/unload")
            print("Previous directories unloaded.")
        except Exception as e:
            print(f"Error unloading previous directories: {str(e)}")
    
    # Set timeout if specified
    if verbose:
        print(f"Setting timeout to {args.timeout} minutes...")
    
    set_timeout(args.timeout, server_url)
    
    # Load the directory with verbose parameter
    if verbose:
        print(f"\n=== Loading directory: {source_dir} ===")
    
    server_data = load_directory(source_dir, server_url, args.timeout, verbose)
    if not server_data:
        print("Failed to load directory. Exiting.")
        return
    
    # Get server info (includes timeout data and image list)
    if verbose:
        print("\n=== Getting server info ===")
    
    server_info = get_server_info(server_url)
    if not server_info:
        print("Failed to get server info. Exiting.")
        return
    
    # Get list of images from server info
    images = server_info.get("image_list", [])
    if not images:
        print("No images found in directory")
        return
    
    print(f"Found {len(images)} images in {source_dir}")
    
    # Define custom filename if provided
    custom_filename = None
    if args.name:
        custom_filename = f"{args.name}.json"
    
    # Generate JSON with URLs and timeout info
    if verbose:
        print("\n=== Generating JSON file ===")
    
    json_file = generate_json(server_info, server_url, output_dir, custom_filename)
    
    # Print the contents of the JSON file
    with open(json_file, "r") as f:
        print("\nGenerated JSON:")
        json_content = json.load(f)
        # Print summary without all image URLs to keep output manageable
        summary = json_content.copy()
        if len(summary["image_urls"]) > 5:
            summary["image_urls"] = summary["image_urls"][:5] + ["..."]
        print(json.dumps(summary, indent=2))
        print(f"\nTotal images: {json_content['count']}")
    
    # Unload directory if requested
    if args.unload:
        if verbose:
            print("\n=== Unloading directory ===")
        
        print("\nUnloading directory as requested...")
        requests.post(f"{server_url}/unload")
        print("Directory unloaded successfully!")
    else:
        print("\nImages remain loaded on the server and can be accessed via the URLs.")
        if server_info.get("timeout_minutes"):
            print(f"They will be automatically unloaded after {server_info['timeout_minutes']} minutes.")
            if server_info.get("auto_unload_at"):
                print(f"Estimated unload time: {server_info['auto_unload_at']}")
        print("To unload manually, run: ./unload_directory.sh")
    
    if verbose:
        print("\n=== Process completed successfully ===")
        print(f"JSON file saved to: {json_file}")
        print(f"Total images processed: {len(images)}")
        print("=======================================\n")

if __name__ == "__main__":
    main()