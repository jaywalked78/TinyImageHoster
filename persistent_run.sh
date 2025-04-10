#!/bin/bash

# Make sure we're in the right directory
cd "$(dirname "$0")"

# Default port (can be overridden by command line argument)
PORT=7779
if [ "$1" != "" ]; then
    PORT="$1"
fi

# Default host
HOST="0.0.0.0"
if [ "$2" != "" ]; then
    HOST="$2"
fi

# Set the virtual environment name
VENV_DIR="tinyHosterVenv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment '$VENV_DIR' not found."
    echo "Please run ./setup.sh first or create it with: python3 -m venv $VENV_DIR"
    exit 1
fi

# Function to check if port is in use
check_port() {
    netstat -tuln | grep ":$PORT " > /dev/null
    return $?
}

# Function to find process using port
find_process_using_port() {
    local pid=$(lsof -t -i:"$PORT" -sTCP:LISTEN 2>/dev/null)
    echo "$pid"
}

# Check if port is already in use
if check_port; then
    echo "Port $PORT is already in use."
    pid=$(find_process_using_port)
    
    if [ -n "$pid" ]; then
        echo "Found process (PID: $pid) using port $PORT. Attempting to stop it gracefully..."
        
        # Try to gracefully terminate the process
        kill -15 "$pid"
        
        # Wait for process to terminate (max 10 seconds)
        for i in {1..10}; do
            if ! ps -p "$pid" > /dev/null; then
                echo "Process stopped successfully."
                break
            fi
            echo "Waiting for process to terminate... ($i/10)"
            sleep 1
        done
        
        # If process still running, force kill
        if ps -p "$pid" > /dev/null; then
            echo "Process did not terminate gracefully. Forcing termination..."
            kill -9 "$pid"
            sleep 2
        fi
    else
        echo "Could not find the process using port $PORT. It might be running in a container or by another user."
        echo "Please manually stop the service using this port and try again."
        exit 1
    fi
    
    # Verify port is free now
    if check_port; then
        echo "ERROR: Port $PORT is still in use after attempting to stop the process."
        echo "Please manually stop the service using this port and try again."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment $VENV_DIR..."
source "$VENV_DIR/bin/activate"

# Verify the environment has the necessary packages
if ! pip show requests &>/dev/null; then
    echo "Installing required packages in $VENV_DIR..."
    pip install requests fastapi uvicorn python-dotenv
fi

# Export environment variables
export IMAGE_SERVER_PORT="$PORT"
export IMAGE_SERVER_HOST="$HOST"
export IMAGE_SERVER_PERSIST="true"  # Enable directory persistence

echo "Starting image server on http://$HOST:$PORT (persistent mode)"
echo "Directories loaded in this server will remain loaded after shutdown"
echo "Press Ctrl+C to stop the server"

# Run the server in the background
python run.py &
SERVER_PID=$!

# Wait for server to start (max 5 seconds)
echo "Waiting for server to start..."
for i in {1..5}; do
    if check_port; then
        echo "Server started successfully in persistent mode!"
        break
    fi
    sleep 1
    
    # If we've waited 5 seconds and still no server, there may be a problem
    if [ $i -eq 5 ]; then
        echo "WARNING: Server did not appear to start within 5 seconds."
        echo "Check for errors in the output above."
    fi
done

# Bring the server process to the foreground
wait $SERVER_PID 