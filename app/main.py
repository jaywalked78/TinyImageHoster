import os
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, Request, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import shutil
import atexit
import time
import asyncio
import threading
from datetime import datetime
from dotenv import load_dotenv
from load_folder import is_server_running, start_server, load_directory, get_server_info, generate_json

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Lightweight Image Server",
    description="A simple API to serve images for embedding purposes",
    version="1.0.0"
)

# Default configuration
DEFAULT_PORT = 7779
DEFAULT_HOST = "0.0.0.0"  # Bind to all interfaces
DEFAULT_TIMEOUT = 0  # Default: no timeout (0 = disabled)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# Current loaded directory
current_dir = None
image_count = 0
load_time = None
timeout_task = None

# Storage for static files mount
static_files_app = None

class DirectoryModel(BaseModel):
    path: str
    timeout_minutes: Optional[int] = None

class ServerInfo(BaseModel):
    current_directory: Optional[str] = None
    image_count: int = 0
    image_list: List[str] = []
    load_time: Optional[str] = None
    timeout_minutes: Optional[int] = None
    auto_unload_at: Optional[str] = None
    time_remaining: Optional[str] = None

def get_timeout_minutes():
    """Get timeout minutes from environment or config"""
    timeout_str = os.environ.get("IMAGE_SERVER_TIMEOUT", str(DEFAULT_TIMEOUT))
    try:
        timeout = int(timeout_str)
        return timeout
    except ValueError:
        return DEFAULT_TIMEOUT

async def unload_after_timeout(timeout_minutes: int):
    """Background task to unload directory after timeout"""
    global current_dir, image_count, static_files_app, load_time, timeout_task
    
    if timeout_minutes <= 0:
        return
    
    print(f"Directory will be automatically unloaded after {timeout_minutes} minutes")
    
    # Sleep for the specified timeout (convert to seconds)
    await asyncio.sleep(timeout_minutes * 60)
    
    # Check if we still need to unload (could have been manually unloaded)
    if current_dir:
        print(f"Timeout reached after {timeout_minutes} minutes. Automatically unloading directory.")
        
        # Remove the static mount
        if hasattr(app, "static_mount"):
            app.router.routes = [route for route in app.router.routes if getattr(route, "path", "") != "/images/{path:path}"]
        
        # Reset globals
        current_dir = None
        image_count = 0
        static_files_app = None
        load_time = None
        timeout_task = None
        
        print("Directory unloaded successfully due to timeout.")

@app.get("/", response_model=ServerInfo)
async def get_server_info():
    """Get information about the currently loaded directory and images"""
    global current_dir, image_count, load_time, timeout_task
    
    image_list = []
    timeout_minutes = get_timeout_minutes()
    auto_unload_at = None
    time_remaining = None
    
    if current_dir and os.path.exists(current_dir):
        image_list = [
            f for f in os.listdir(current_dir) 
            if os.path.isfile(os.path.join(current_dir, f)) and 
            any(f.lower().endswith(ext) for ext in IMAGE_EXTENSIONS)
        ]
        
        # Calculate timeout information
        if load_time and timeout_minutes > 0:
            seconds_elapsed = (datetime.now() - load_time).total_seconds()
            timeout_seconds = timeout_minutes * 60
            
            if seconds_elapsed < timeout_seconds:
                seconds_remaining = timeout_seconds - seconds_elapsed
                minutes_remaining = int(seconds_remaining / 60)
                seconds_remainder = int(seconds_remaining % 60)
                time_remaining = f"{minutes_remaining}m {seconds_remainder}s"
                
                # Format unload time
                unload_time = load_time.timestamp() + timeout_seconds
                auto_unload_at = datetime.fromtimestamp(unload_time).strftime("%Y-%m-%d %H:%M:%S")
    
    return ServerInfo(
        current_directory=current_dir,
        image_count=len(image_list),
        image_list=image_list,
        load_time=load_time.strftime("%Y-%m-%d %H:%M:%S") if load_time else None,
        timeout_minutes=timeout_minutes if timeout_minutes > 0 else None,
        auto_unload_at=auto_unload_at,
        time_remaining=time_remaining
    )

@app.post("/load-directory")
async def load_directory(directory: DirectoryModel, background_tasks: BackgroundTasks):
    """Load a new directory of images to serve"""
    global current_dir, image_count, static_files_app, load_time, timeout_task
    
    path = os.path.expanduser(directory.path)
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Directory not found: {path}")
    
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail=f"Not a directory: {path}")
    
    # Count images in the directory
    image_files = [
        f for f in os.listdir(path) 
        if os.path.isfile(os.path.join(path, f)) and 
        any(f.lower().endswith(ext) for ext in IMAGE_EXTENSIONS)
    ]
    
    # Cancel any existing timeout task
    if timeout_task:
        # We can't easily cancel the task, but we can ignore it
        # It will check if current_dir is None before taking action
        pass
    
    # Update global variables
    current_dir = path
    image_count = len(image_files)
    load_time = datetime.now()
    
    # Remove any existing mount 
    if hasattr(app, "static_mount"):
        app.router.routes = [route for route in app.router.routes if getattr(route, "path", "") != "/images/{path:path}"]
    
    # Create a new static files instance
    static_files_app = StaticFiles(directory=path)
    
    # Mount the new directory
    app.mount("/images", static_files_app, name="images")
    
    # Set timeout (use provided value or environment default)
    timeout_minutes = directory.timeout_minutes if directory.timeout_minutes is not None else get_timeout_minutes()
    
    # Start timeout task if timeout is enabled
    if timeout_minutes > 0:
        background_tasks.add_task(unload_after_timeout, timeout_minutes)
        auto_unload_at = (load_time.timestamp() + (timeout_minutes * 60))
        auto_unload_time = datetime.fromtimestamp(auto_unload_at).strftime("%Y-%m-%d %H:%M:%S")
        timeout_message = f"Directory will be automatically unloaded at {auto_unload_time} ({timeout_minutes} minutes)"
    else:
        timeout_message = "No auto-unload timeout set"
    
    return {
        "status": "success",
        "directory": path,
        "image_count": image_count,
        "message": f"Loaded {image_count} images from {path}",
        "timeout": timeout_message
    }

@app.get("/images/{image_name}")
async def get_image(image_name: str):
    """Get a specific image by name"""
    global current_dir
    
    if not current_dir:
        raise HTTPException(status_code=400, detail="No directory loaded")
    
    image_path = os.path.join(current_dir, image_name)
    
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail=f"Image not found: {image_name}")
    
    if not os.path.isfile(image_path):
        raise HTTPException(status_code=400, detail=f"Not a file: {image_name}")
    
    # Check if it's an image
    if not any(image_path.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
        raise HTTPException(status_code=400, detail=f"Not an image: {image_name}")
    
    return FileResponse(image_path)

@app.post("/unload")
async def unload_directory():
    """Unload the current directory"""
    global current_dir, image_count, static_files_app, load_time, timeout_task
    
    if not current_dir:
        return {"status": "info", "message": "No directory currently loaded"}
    
    # Remove the static mount
    if hasattr(app, "static_mount"):
        app.router.routes = [route for route in app.router.routes if getattr(route, "path", "") != "/images/{path:path}"]
    
    # Reset globals
    current_dir = None
    image_count = 0
    static_files_app = None
    load_time = None
    timeout_task = None
    
    return {"status": "success", "message": "Directory unloaded successfully"}

@app.get("/timeout")
async def get_timeout():
    """Get current timeout settings"""
    timeout_minutes = get_timeout_minutes()
    return {
        "timeout_minutes": timeout_minutes,
        "timeout_enabled": timeout_minutes > 0
    }

@app.post("/timeout/{minutes}")
async def set_timeout(minutes: int, background_tasks: BackgroundTasks):
    """Set a new timeout value and apply it to the currently loaded directory"""
    global load_time, timeout_task
    
    if minutes < 0:
        raise HTTPException(status_code=400, detail="Timeout minutes must be >= 0 (0 = disabled)")
    
    # Update environment variable
    os.environ["IMAGE_SERVER_TIMEOUT"] = str(minutes)
    
    # If a directory is loaded, reset the timeout
    if current_dir:
        # Cancel any existing timeout task
        if timeout_task:
            # We can't easily cancel the task, but we can ignore it
            # It will check if current_dir is None before taking action
            pass
        
        # Update load time to now
        load_time = datetime.now()
        
        # Start a new timeout task if minutes > 0
        if minutes > 0:
            background_tasks.add_task(unload_after_timeout, minutes)
            auto_unload_at = (load_time.timestamp() + (minutes * 60))
            auto_unload_time = datetime.fromtimestamp(auto_unload_at).strftime("%Y-%m-%d %H:%M:%S")
            message = f"Timeout set to {minutes} minutes. Directory will be unloaded at {auto_unload_time}"
        else:
            message = "Timeout disabled. Directory will remain loaded until manually unloaded or server is restarted."
    else:
        message = f"Timeout set to {minutes} minutes. Will apply to next loaded directory."
    
    return {
        "status": "success",
        "timeout_minutes": minutes,
        "timeout_enabled": minutes > 0,
        "message": message
    }

# Register shutdown handler to preserve state
@atexit.register
def on_shutdown():
    # We don't unload the directory on shutdown anymore
    # This allows the URLs to remain valid if the server is restarted
    pass

def start():
    """Start the server with the specified settings"""
    port = int(os.environ.get("IMAGE_SERVER_PORT", DEFAULT_PORT))
    host = os.environ.get("IMAGE_SERVER_HOST", DEFAULT_HOST)
    
    print(f"Starting image server on http://{host}:{port}")
    print(f"Auto-unload timeout: {get_timeout_minutes()} minutes (0 = disabled)")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)

if __name__ == "__main__":
    # Start server if needed
    if not is_server_running():
        start_server()

    # Load your directory
    directory_path = "/path/to/your/images"
    server_data = load_directory(directory_path, verbose=True)

    # Get server info with image list
    server_info = get_server_info()

    # Generate JSON with auto-named file
    json_file = generate_json(server_info)
    # json_file will contain the path to the saved JSON with auto-generated name

    start() 