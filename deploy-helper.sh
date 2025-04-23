#!/bin/bash

# Script to check for WhatsApp authentication and guide users through re-authentication
# Add this to your repository for easier deployment

# Colors for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}WhatsApp MCP Free Tier Helper${NC}"
echo "This script helps manage your WhatsApp MCP deployment on Render free tier"
echo ""

echo -e "${YELLOW}Deployment Steps:${NC}"
echo "1. Push your code to GitHub"
echo "2. Create a new Web Service on Render using the Blueprint option"
echo "3. When Render deploys your app, immediately check the logs for the QR code"
echo "4. Scan the QR code quickly with your WhatsApp mobile app"
echo ""

echo -e "${YELLOW}Re-authentication Steps:${NC}"
echo "When your service restarts and requires re-authentication:"
echo "1. Go to your Render dashboard -> whatsapp-mcp service -> Logs"
echo "2. Look for the QR code between the ======== markers"
echo "3. Scan the QR code with your WhatsApp mobile app"
echo "4. The service should connect and be ready to use"
echo ""

echo -e "${YELLOW}Important Notes:${NC}"
echo "- Free tier services sleep after 15 minutes of inactivity"
echo "- You'll need to re-authenticate whenever the service wakes up"
echo "- Use your service within 15-minute intervals to prevent sleeping"
echo "- Consider upgrading to Standard tier (\$7/month) if you need continuous uptime"
echo ""

echo -e "${GREEN}Your WhatsApp MCP app is now ready for deployment!${NC}"