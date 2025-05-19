#!/bin/bash

# Default parameters
NODE_URL="http://localhost:8001"
if [ -n "$1" ]; then
    NODE_URL="http://localhost:$1"
fi

echo "Testing API connectivity to: $NODE_URL"
echo "======================================="

# Test root endpoint
echo "Testing / endpoint:"
curl -s $NODE_URL

echo -e "\n\nTesting /api/blockchain endpoint:"
curl -s $NODE_URL/api/blockchain

echo -e "\n\nAPI test completed."