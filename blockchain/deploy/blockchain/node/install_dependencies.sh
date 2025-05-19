#!/bin/bash

echo "Installing GlobalCoyn Node Dependencies"
echo "======================================="

# Check if pip3 is available
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
else
    echo "Error: pip or pip3 not found. Please install Python and pip first."
    exit 1
fi

# Install dependencies
echo "Installing dependencies from requirements.txt..."
$PIP_CMD install -r requirements.txt

echo "Dependencies installed successfully!"
echo "You can now run the start_node.sh script to start the node."