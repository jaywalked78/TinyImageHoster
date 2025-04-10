#!/bin/bash

# Function to display help
show_help() {
    echo "Image Server Loader Script"
    echo "=========================="
    echo
    echo "This script loads images from a directory into the Lightweight Image Server"
    echo "and generates a JSON file with URLs for all images."
    echo
    echo "Features:"
    echo "  - Uses a persistent virtual environment (tinyHosterVenv)"
    echo "  - Installs all required dependencies (requests, Pillow, etc.)"
    echo "  - Shows verbose debugging with a progress bar during loading"
    echo "  - Displays detailed information for each image (size, dimensions)"
    echo "  - Generates a JSON file with a unique name based on folder name and timestamp"
    echo "  - Handles server startup automatically"
    echo
    echo "Usage: $0 <image_directory> [timeout_minutes]"
    echo
    echo "Arguments:"
    echo "  <image_directory>   Directory containing the images to load"
    echo "  [timeout_minutes]   Optional: How long to keep images loaded (default: 30 minutes)"
    echo
    echo "Examples:"
    echo "  $0 ~/Pictures/vacation"
    echo "  $0 /data/images/dataset1 60"
    echo
    echo "The JSON file will be saved in: ~/Documents/LightweightImageServer/output/json"
    echo "with a filename like: foldername_YYYYMMDD_HHMMSS.json"
    echo
}

# Show help if -h or --help is provided
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# Check if directory parameter is provided
if [ -z "$1" ]; then
    echo "Error: Missing directory parameter"
    echo
    show_help
    exit 1
fi

# Get the directory parameter
IMAGE_DIR="$1"

# Check if directory exists
if [ ! -d "$IMAGE_DIR" ]; then
    echo "Error: Directory '$IMAGE_DIR' does not exist"
    exit 1
fi

# Get timeout parameter or use default (30 minutes)
TIMEOUT="${2:-30}"

# Display banner
echo "========================================"
echo "   LIGHTWEIGHT IMAGE SERVER LOADER"
echo "========================================"
echo "Loading images from: $IMAGE_DIR"
echo "Timeout set to: $TIMEOUT minutes"
echo "Starting load process with detailed logging..."
echo "========================================"
echo

# Run the script with verbose debugging
./setup_and_run.sh --dir "$IMAGE_DIR" --timeout "$TIMEOUT" --unload-first --verbose

echo
echo "Process completed. Check the log file for details."
echo "Log file: $(pwd)/image_loader.log"
echo
echo "To follow the full log in real time:"
echo "tail -f $(pwd)/image_loader.log"

# The JSON file will be auto-generated with the folder name and timestamp 