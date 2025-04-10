#!/bin/bash

# Default server URL
SERVER_URL="${1:-http://localhost:7779}"

# Make sure we're in the right directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo "Unloading directory from server at $SERVER_URL"

# Use curl to unload the directory
curl -X POST "$SERVER_URL/unload"

echo -e "\nDirectory unloaded successfully." 