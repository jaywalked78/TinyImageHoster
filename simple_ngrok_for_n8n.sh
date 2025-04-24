#!/bin/bash
# Simple Ngrok launcher for your free static domain

# Load environment variables if .env exists
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Configuration (use environment variables or defaults)
PORT=${IMAGE_SERVER_PORT:-7779}
DOMAIN=${NGROK_DOMAIN:-"your-subdomain"}
PERMANENT_URL=${NGROK_URL:-"https://your-subdomain.ngrok-free.app"}

# Kill any existing ngrok processes
pkill -f ngrok || true
echo "Stopped any running ngrok processes"

# Start ngrok directly without background mode
echo "Starting ngrok on port $PORT with your free domain..."
echo "URL: $PERMANENT_URL"
echo "Web interface will be available at: http://localhost:4040"

# Just run ngrok in the foreground
ngrok http $PORT --domain=$DOMAIN.ngrok-free.app