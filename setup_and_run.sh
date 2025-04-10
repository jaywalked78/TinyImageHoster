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

# Install dependencies (show output now)
log "Installing required packages..."
pip install --upgrade pip 2>&1 | tee -a "$LOG_FILE"
pip install requests Pillow fastapi uvicorn python-dotenv 2>&1 | tee -a "$LOG_FILE"

# Check if PIL was installed successfully
python -c "try:
    from PIL import Image
    print('PIL installed successfully.')
except ImportError:
    print('Warning: PIL not installed correctly. Image dimensions will not be shown.')
    exit(1)" 2>&1 | tee -a "$LOG_FILE"

# Pass all arguments to the load_folder.py script with verbose flag explicitly set
log "Running load_folder.py script with arguments: $@"

# Start tail in background to show log updates in real-time
log "Starting log tail in background. Press Ctrl+C to stop viewing the log (script will continue)."
tail -f "$LOG_FILE" &
TAIL_PID=$!

# Give tail a moment to start
sleep 1

# Run the script and capture its output to the log
python load_folder.py "$@" --verbose 2>&1 | tee -a "$LOG_FILE"
SCRIPT_STATUS=$?

# Kill the tail process
kill $TAIL_PID 2>/dev/null

# Deactivate virtual environment only if we activated it
if [[ -z "$ORIGINAL_VIRTUAL_ENV" ]]; then
    log "Deactivating virtual environment..."
    deactivate
fi

log "Script completed with status: $SCRIPT_STATUS"
log "Full log available at: $LOG_FILE" 