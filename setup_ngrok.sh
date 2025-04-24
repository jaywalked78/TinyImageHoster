#!/bin/bash
# Setup script for configuring ngrok with the image server

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
ENV_FILE=".env"
DEFAULT_PORT=7779

# Check if .env file exists
if [ -f "$ENV_FILE" ]; then
    echo -e "${BLUE}Loading environment variables from $ENV_FILE${NC}"
    export $(grep -v '^#' $ENV_FILE | xargs)
else
    echo -e "${YELLOW}No .env file found. Creating one from template...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example $ENV_FILE
        echo -e "${GREEN}Created $ENV_FILE from example template${NC}"
    else
        echo -e "${RED}Error: No .env.example file found to use as template${NC}"
        echo -e "PORT=${DEFAULT_PORT}" > $ENV_FILE
        echo -e "${YELLOW}Created minimal $ENV_FILE with default port ${DEFAULT_PORT}${NC}"
    fi
    export $(grep -v '^#' $ENV_FILE | xargs)
fi

# Get the port from environment or use default
PORT=${IMAGE_SERVER_PORT:-$DEFAULT_PORT}

# Ask user for ngrok domain
echo -e "${BLUE}Please enter your ngrok static domain (without .ngrok-free.app):${NC}"
read -p "Domain: " NGROK_DOMAIN

# Check if input is empty
if [ -z "$NGROK_DOMAIN" ]; then
    echo -e "${RED}No domain provided. Exiting setup.${NC}"
    exit 1
fi

# Update .env file with NGROK information
if grep -q "NGROK_DOMAIN" $ENV_FILE; then
    # Replace existing values
    sed -i "s/NGROK_DOMAIN=.*/NGROK_DOMAIN=$NGROK_DOMAIN/" $ENV_FILE
    sed -i "s|NGROK_URL=.*|NGROK_URL=https://$NGROK_DOMAIN.ngrok-free.app|" $ENV_FILE
else
    # Add new values
    echo "" >> $ENV_FILE
    echo "# Ngrok Configuration" >> $ENV_FILE
    echo "NGROK_DOMAIN=$NGROK_DOMAIN" >> $ENV_FILE
    echo "NGROK_URL=https://$NGROK_DOMAIN.ngrok-free.app" >> $ENV_FILE
fi

echo -e "${GREEN}Ngrok configured successfully!${NC}"
echo -e "${BLUE}Your public URL will be:${NC} https://$NGROK_DOMAIN.ngrok-free.app"
echo -e "${YELLOW}To start ngrok, run:${NC} ./simple_ngrok_for_n8n.sh"

# Make the ngrok script executable
chmod +x simple_ngrok_for_n8n.sh

echo -e "${GREEN}Setup complete!${NC}"