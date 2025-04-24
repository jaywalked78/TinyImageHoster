# Ngrok Integration Guide

This guide explains how to set up and use Ngrok with TinyImageHoster to expose your local image server to the internet with a permanent URL.

## Prerequisites

1. A free Ngrok account (sign up at [https://ngrok.com](https://ngrok.com))
2. Ngrok CLI installed on your system
3. TinyImageHoster running locally

## Setup Instructions

### 1. Create a Free Ngrok Account

- Sign up at [https://ngrok.com](https://ngrok.com)
- Verify your email address
- Log in to your Ngrok dashboard

### 2. Get Your Authtoken

- In your Ngrok dashboard, navigate to the "Auth" section
- Copy your authtoken

### 3. Install Ngrok CLI

#### On Linux:
```bash
# Download and install
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update
sudo apt install ngrok

# Authenticate
ngrok config add-authtoken YOUR_AUTHTOKEN
```

#### On macOS:
```bash
brew install ngrok/ngrok/ngrok
ngrok config add-authtoken YOUR_AUTHTOKEN
```

#### On Windows:
- Download the installer from [https://ngrok.com/download](https://ngrok.com/download)
- Run the installer
- Open Command Prompt and run:
```
ngrok config add-authtoken YOUR_AUTHTOKEN
```

### 4. Reserve a Static Domain (Free Tier)

- In your Ngrok dashboard, navigate to "Domains"
- Click "New Domain"
- Choose a subdomain name (e.g., your-image-server)
- Select "Free static domain (.ngrok-free.app)"
- Click "Create"

### 5. Configure TinyImageHoster with Ngrok

Run the setup script:
```bash
./setup_ngrok.sh
```

This script will:
- Ask for your Ngrok domain name (without the .ngrok-free.app suffix)
- Update your .env file with the Ngrok settings
- Make the simple_ngrok_for_n8n.sh script executable

## Usage

### Starting the Image Server with Ngrok

1. Start your image server:
```bash
./run_with_progress.sh /path/to/your/images
```

2. In another terminal window, start Ngrok:
```bash
./simple_ngrok_for_n8n.sh
```

Your image server will now be accessible at:
```
https://your-domain.ngrok-free.app
```

### Integration with n8n or Other Workflow Tools

When setting up webhooks in n8n or other workflow tools, use your Ngrok URL:
```
https://your-domain.ngrok-free.app/images/your-image.jpg
```

## Troubleshooting

### Connection Issues
- Make sure your image server is running locally before starting Ngrok
- Verify your authtoken is correctly configured

### Rate Limiting
- The free tier of Ngrok has rate limits. If you exceed them, consider upgrading.

### Port Already in Use
- If you see an error that the port is already in use, run:
```bash
pkill -f ngrok
```
Then try starting Ngrok again.

## Additional Resources

- [Ngrok Documentation](https://ngrok.com/docs)
- [Ngrok API Reference](https://ngrok.com/docs/api)