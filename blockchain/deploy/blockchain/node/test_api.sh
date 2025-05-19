#!/bin/bash
# GlobalCoyn API Test Script
# This script runs automated tests against the GlobalCoyn blockchain API

# Configuration
NODE_URL="${1:-http://localhost:8001}"
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper function to display test results
test_endpoint() {
    local endpoint="$1"
    local method="${2:-GET}"
    local data="$3"
    local expected_status="${4:-200}"
    
    echo -e "${YELLOW}Testing ${method} ${endpoint}${NC}"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -o response.txt -w "%{http_code}" -X GET "${NODE_URL}${endpoint}")
    else
        if [ -n "$data" ]; then
            response=$(curl -s -o response.txt -w "%{http_code}" -X "${method}" -H "Content-Type: application/json" -d "${data}" "${NODE_URL}${endpoint}")
        else
            response=$(curl -s -o response.txt -w "%{http_code}" -X "${method}" "${NODE_URL}${endpoint}")
        fi
    fi
    
    if [ "$response" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ Status: ${response} (Expected: ${expected_status})${NC}"
        echo "Response body:"
        cat response.txt
        echo
    else
        echo -e "${RED}✗ Status: ${response} (Expected: ${expected_status})${NC}"
        echo "Response body:"
        cat response.txt
        echo
    fi
    
    echo "----------------------------------------------------------------"
}

echo -e "${YELLOW}GlobalCoyn API Test Script${NC}"
echo "Testing against node: ${NODE_URL}"
echo "================================================================"

# Test basic connectivity to the API
test_endpoint "/"

# Test blockchain endpoints
test_endpoint "/api/blockchain"
test_endpoint "/api/blockchain/difficulty"

# Test network endpoints
test_endpoint "/api/network/status"

echo -e "${GREEN}API Tests completed!${NC}"