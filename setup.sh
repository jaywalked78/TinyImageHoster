#!/bin/bash

# Make sure we're in the right directory
cd "$(dirname "$0")"

# Check for required system utilities
echo "Checking required system utilities..."
MISSING_TOOLS=()

if ! command -v lsof &>/dev/null; then
    MISSING_TOOLS+=("lsof")
fi

if ! command -v netstat &>/dev/null; then
    MISSING_TOOLS+=("net-tools (provides netstat)")
fi

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    echo "Some required tools are missing. Please install them with:"
    echo "sudo apt install ${MISSING_TOOLS[*]}"
    read -p "Install missing packages now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo apt update
        sudo apt install -y ${MISSING_TOOLS[*]}
    else
        echo "Please install the missing packages and run this script again."
        exit 1
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setup complete! You can now run the server with ./run_server.sh" 