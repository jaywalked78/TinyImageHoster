#!/bin/bash

# Directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Create log file
LOG_FILE="${SCRIPT_DIR}/image_loader.log"
echo "Starting image loading process at $(date)" > "$LOG_FILE"

# Function to log messages to both console and log file
log() {
    echo "$1"
    echo "[$(date +"%H:%M:%S")] $1" >> "$LOG_FILE"
}

log "Working directory: $SCRIPT_DIR"

# Set virtual environment name
VENV_DIR="tinyHosterVenv"

# Check if we're already in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    log "No active virtual environment detected."
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        log "Creating virtual environment: $VENV_DIR"
        python3 -m venv "$VENV_DIR" 2>&1 | tee -a "$LOG_FILE"
        if [ $? -ne 0 ]; then
            log "Failed to create virtual environment. Make sure python3-venv is installed."
            log "On Ubuntu/Debian: sudo apt-get install python3-venv"
            exit 1
        fi
        log "Virtual environment created successfully!"
    else
        log "Using existing virtual environment: $VENV_DIR"
    fi
    
    # Activate virtual environment
    log "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    log "Virtual environment activated: $VIRTUAL_ENV"
else
    log "Already in a virtual environment: $VIRTUAL_ENV"
fi

# Install dependencies
log "Installing required packages..."
pip install --upgrade pip 2>&1 | tee -a "$LOG_FILE"
pip install requests Pillow fastapi uvicorn python-dotenv tqdm aiohttp aiofiles 2>&1 | tee -a "$LOG_FILE"

# Check if PIL was installed successfully
python -c "try:
    from PIL import Image
    print('PIL installed successfully.')
except ImportError:
    print('Warning: PIL not installed correctly. Image dimensions will not be shown.')
    exit(1)" 2>&1 | tee -a "$LOG_FILE"

# Check if optimization-related packages were installed successfully
python -c "try:
    import tqdm, aiohttp, aiofiles, concurrent.futures
    print('Optimization packages installed successfully.')
except ImportError as e:
    print(f'Warning: Some optimization packages not installed correctly: {e}')
    exit(1)" 2>&1 | tee -a "$LOG_FILE"

# Default workers and batch size for performance
WORKERS=10
BATCH_SIZE=20

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
    
    # Extract worker and batch size if specified
    if [[ $arg == --workers=* ]]; then
        WORKERS="${arg#*=}"
    elif [[ $arg == --batch-size=* ]]; then
        BATCH_SIZE="${arg#*=}"
    fi
    
    ARGS+=("$arg")
done

# If no directory was set, show usage information
if [ "$DIR_SET" = false ]; then
    log "Error: No directory specified. Please provide a directory path."
    log "Usage: $0 <directory_path> [options]"
    log "   or: $0 --dir=<directory_path> [options]"
    log ""
    log "Options:"
    log "  --server=URL          Server URL (default: http://localhost:7779)"
    log "  --workers=N           Number of concurrent workers (default: 10)"
    log "  --batch-size=N        Images per batch (default: 20)"
    log "  --timeout=N           Set timeout in minutes (default: 30)"
    log "  --unload              Unload directory when done"
    log "  --unload-first        Unload any previous directories first"
    log "  --verbose             Show detailed progress information"
    log "  --output=DIR          Output directory for JSON file"
    log "  --name=NAME           Custom name for output JSON file"
    exit 1
fi

# Log the final command
log "Running command: python load_folder_v2.py ${ARGS[@]} --verbose --workers $WORKERS --batch-size $BATCH_SIZE"

# Run the script directly to terminal to ensure progress bars display correctly
python load_folder_v2.py "${ARGS[@]}" --verbose --workers $WORKERS --batch-size $BATCH_SIZE 2>&1 | tee -a "$LOG_FILE"
SCRIPT_STATUS=$?

# Deactivate virtual environment only if we activated it
if [[ -z "$ORIGINAL_VIRTUAL_ENV" ]]; then
    log "Deactivating virtual environment..."
    deactivate
fi

log "Script completed with status: $SCRIPT_STATUS"
log "Full log available at: $LOG_FILE"