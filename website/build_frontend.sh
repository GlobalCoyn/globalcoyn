#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== GlobalCoyn Frontend Build Script ===${NC}"
echo "This script builds the GlobalCoyn frontend for production deployment."

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
DOWNLOAD_DIR="$HOME/Downloads/globalcoyn-frontend"

# Create Downloads directory if it doesn't exist
mkdir -p "$DOWNLOAD_DIR"

echo -e "${YELLOW}Step 1: Copying frontend files to Downloads directory${NC}"
echo "From: $PROJECT_DIR"
echo "To: $DOWNLOAD_DIR"

# Copy the frontend files to the Downloads directory
rsync -av --exclude=node_modules --exclude=build "$PROJECT_DIR/" "$DOWNLOAD_DIR/"

# Navigate to the Downloads directory
cd "$DOWNLOAD_DIR"

echo -e "${YELLOW}Step 2: Installing dependencies${NC}"
# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: package.json not found.${NC}"
    echo "Please make sure you're in the correct directory."
    exit 1
fi

# Install dependencies
npm install

echo -e "${YELLOW}Step 3: Building the frontend${NC}"
# Build the frontend
npm run build

if [ $? -ne 0 ]; then
    echo -e "${RED}Build failed.${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 4: Creating deployment package${NC}"
# Create a zip file of the build directory
cd "$DOWNLOAD_DIR"
rm -f build.zip
zip -r build.zip build/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment package created successfully${NC}"
    echo -e "Location: ${YELLOW}$DOWNLOAD_DIR/build.zip${NC}"
    
    echo -e "\n${YELLOW}To deploy the frontend:${NC}"
    echo "1. Transfer the package to your server:"
    echo "   scp -i ~/Downloads/globalcoyn.pem $DOWNLOAD_DIR/build.zip ec2-user@13.61.79.186:~"
    echo ""
    echo "2. SSH into the server:"
    echo "   ssh -i ~/Downloads/globalcoyn.pem ec2-user@13.61.79.186"
    echo ""
    echo "3. Deploy the frontend:"
    echo "   unzip -o build.zip"
    echo "   sudo rm -rf /var/www/globalcoyn/frontend/build"
    echo "   sudo mv build /var/www/globalcoyn/frontend/"
    echo "   sudo chown -R deploy:deploy /var/www/globalcoyn/frontend/build"
    echo "   sudo systemctl restart nginx"
else
    echo -e "${RED}Failed to create deployment package.${NC}"
    exit 1
fi