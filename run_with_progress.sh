#!/bin/bash

# Directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment is already active
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "No virtual environment detected, activating tinyHosterVenv..."
    
    # Check if the virtual environment exists
    if [[ ! -d "tinyHosterVenv" ]]; then
        echo "Error: Virtual environment 'tinyHosterVenv' not found!"
        echo "Please create it first with: python3 -m venv tinyHosterVenv"
        exit 1
    fi
    
    # Activate the virtual environment with error checking
    source tinyHosterVenv/bin/activate
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to activate virtual environment!"
        exit 1
    fi
    
    echo "Virtual environment activated: $VIRTUAL_ENV"
else
    echo "Already using virtual environment: $VIRTUAL_ENV"
fi

# Make sure we have the required packages
echo "Installing required packages..."
pip install tqdm aiohttp aiofiles python-dotenv > /dev/null

# Load base directory from .env file if it exists
FRAME_BASE_DIR=""
if [ -f ".env" ]; then
    echo "Found .env file. Loading environment variables..."
    export $(grep -v '^#' .env | xargs)
    echo "Base directory for screen recordings: $FRAME_BASE_DIR"
fi

# Process arguments - convert first argument to --dir if it doesn't start with --
ARGS=()
DIR_SET=false

# Check if first argument is just a directory name (not starting with --)
if [[ $# -gt 0 && ! "$1" == --* ]]; then
    ARGS+=("--dir=$1")
    DIR_SET=true
    shift 1  # Remove the first argument as we've processed it
fi

# Process remaining arguments
for arg in "$@"; do
    # Check if this argument sets the directory
    if [[ "$arg" == --dir=* || "$arg" == "--dir" ]]; then
        DIR_SET=true
    fi
    ARGS+=("$arg")
done

# If no directory was set, show usage information
if [ "$DIR_SET" = false ]; then
    echo "Error: No directory specified. Please provide a directory path."
    echo "Usage: $0 <directory_path> [options]"
    echo "   or: $0 --dir=<directory_path> [options]"
    exit 1
fi

# Extract directory from arguments
DIR_PATH="${ARGS[0]#--dir=}"

# Run with progress visible (no tee)
echo "Running optimized image loader with progress bars..."
echo "Directory: $DIR_PATH"
echo "Starting process..."
echo "---------------------------------------"

# Run the optimized script with progress directly to terminal
python load_folder_v2.py "${ARGS[@]}" --verbose --workers=10 --batch-size=20

echo "---------------------------------------"
echo "Process complete!"

# Deactivate virtual environment is commented out to keep it activated
# deactivate