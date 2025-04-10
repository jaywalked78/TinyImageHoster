#!/bin/bash

# Default directory and server URL
DIR="$1"
SERVER_URL="${2:-http://localhost:7779}"

if [ -z "$DIR" ]; then
    echo "Usage: $0 <directory_path> [server_url]"
    echo "Example: $0 ~/Videos/screenRecordings http://localhost:7779"
    exit 1
fi

# Make sure we're in the right directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Expand the directory path
DIR=$(eval echo "$DIR")

echo "Loading directory: $DIR to server at $SERVER_URL"

# Use curl to load the directory
curl -X POST "$SERVER_URL/load-directory" \
    -H "Content-Type: application/json" \
    -d "{\"path\": \"$DIR\"}"

echo -e "\nDirectory loaded successfully."
echo "Images can now be accessed at $SERVER_URL/images/<image_name>" 