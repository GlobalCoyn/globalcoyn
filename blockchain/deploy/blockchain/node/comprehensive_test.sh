#!/bin/bash
# GlobalCoyn Comprehensive API Test Script
# This script runs tests against all major API endpoints of the GlobalCoyn blockchain

# Configuration
NODE_URL="${1:-http://localhost:8001}"
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables to store test data
WALLET_ADDRESS=""
TRANSACTION_HASH=""

# Helper function to display test results
test_endpoint() {
    local endpoint="$1"
    local method="${2:-GET}"
    local data="$3"
    local expected_status="${4:-200}"
    local description="${5:-Testing endpoint}"
    
    echo -e "${BLUE}$description${NC}"
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
        cat response.txt | grep -v "^$" | sed 's/^/  /'
        echo
    else
        echo -e "${RED}✗ Status: ${response} (Expected: ${expected_status})${NC}"
        echo "Response body:"
        cat response.txt | grep -v "^$" | sed 's/^/  /'
        echo
    fi
    
    # Extract values if needed
    if [[ "$endpoint" == "/api/wallet/create" && "$response" -eq 201 ]]; then
        WALLET_ADDRESS=$(grep -o '"address":"[^"]*"' response.txt | cut -d'"' -f4)
        echo -e "${YELLOW}Created wallet address: ${WALLET_ADDRESS}${NC}"
    fi
    
    if [[ "$endpoint" == "/api/transactions" && "$response" -eq 201 ]]; then
        TRANSACTION_HASH=$(grep -o '"tx_hash":"[^"]*"' response.txt | cut -d'"' -f4)
        echo -e "${YELLOW}Created transaction hash: ${TRANSACTION_HASH}${NC}"
    fi
    
    echo "----------------------------------------------------------------"
}

echo -e "${YELLOW}GlobalCoyn Comprehensive API Test Script${NC}"
echo "Testing against node: ${NODE_URL}"
echo "================================================================"

echo -e "${BLUE}PHASE 1: Basic Connectivity${NC}"
echo "================================================================"
test_endpoint "/" "GET" "" 200 "Testing root endpoint"
test_endpoint "/api/blockchain/" "GET" "" 200 "Testing blockchain info"
test_endpoint "/api/network/status" "GET" "" 200 "Testing network status"

echo -e "${BLUE}PHASE 2: Wallet Management${NC}"
echo "================================================================"
test_endpoint "/api/wallet/create" "POST" "" 201 "Creating a new wallet"

# Test wallet endpoints with the created address
if [ -n "$WALLET_ADDRESS" ]; then
    test_endpoint "/api/wallet/balance/${WALLET_ADDRESS}" "GET" "" 200 "Checking wallet balance"
    test_endpoint "/api/wallet/validate/${WALLET_ADDRESS}" "GET" "" 200 "Validating wallet address"
    test_endpoint "/api/wallet/mining-stats/${WALLET_ADDRESS}" "GET" "" 200 "Getting wallet mining stats"
fi

test_endpoint "/api/wallet/list" "GET" "" 200 "Listing all wallets"
test_endpoint "/api/wallet/generate-seed" "GET" "" 200 "Generating seed phrase"
test_endpoint "/api/wallet/fee-estimate" "GET" "" 200 "Getting fee estimate"

echo -e "${BLUE}PHASE 3: Blockchain Query${NC}"
echo "================================================================"
test_endpoint "/api/blockchain/chain" "GET" "" 200 "Getting full blockchain"
test_endpoint "/api/blockchain/blocks/latest" "GET" "" 200 "Getting latest block"
test_endpoint "/api/blockchain/blocks/0" "GET" "" 200 "Getting genesis block"
test_endpoint "/api/blockchain/stats" "GET" "" 200 "Getting blockchain stats"
test_endpoint "/api/blockchain/difficulty" "GET" "" 200 "Getting mining difficulty"
test_endpoint "/api/blockchain/mempool" "GET" "" 200 "Getting mempool"

echo -e "${BLUE}PHASE 4: Mining${NC}"
echo "================================================================"

if [ -n "$WALLET_ADDRESS" ]; then
    test_endpoint "/api/mining/start" "POST" "{\"mining_address\":\"${WALLET_ADDRESS}\"}" 200 "Starting mining"
    
    # Wait a bit for mining to start
    echo "Waiting 3 seconds for mining to start..."
    sleep 3
    
    test_endpoint "/api/mining/status" "GET" "" 200 "Checking mining status"
    test_endpoint "/api/mining/hashrate" "GET" "" 200 "Getting hashrate"
    test_endpoint "/api/mining/rewards" "GET" "" 200 "Getting mining rewards"
    
    # Mine a block directly
    test_endpoint "/api/blockchain/blocks/mine" "POST" "{\"miner_address\":\"${WALLET_ADDRESS}\"}" 201 "Mining a block"
    
    # Stop mining
    test_endpoint "/api/mining/stop" "POST" "" 200 "Stopping mining"
    
    # Check if balance increased after mining
    test_endpoint "/api/wallet/balance/${WALLET_ADDRESS}" "GET" "" 200 "Checking updated wallet balance after mining"
fi

echo -e "${BLUE}PHASE 5: Transactions${NC}"
echo "================================================================"
test_endpoint "/api/transactions/mempool" "GET" "" 200 "Getting mempool transactions"
test_endpoint "/api/transactions/fees" "GET" "" 200 "Getting recommended transaction fees"

if [ -n "$WALLET_ADDRESS" ]; then
    # To sign a transaction, we need the private key which we don't have
    # Instead, we'll demonstrate the endpoint
    echo -e "${YELLOW}Note: Actual transaction signing requires private key access${NC}"
    test_endpoint "/api/wallet/sign-transaction" "POST" "{\"sender\":\"${WALLET_ADDRESS}\",\"recipient\":\"GCN_RECIPIENT_ADDRESS\",\"amount\":1.0,\"fee\":0.001}" 404 "Signing a transaction (expected to fail without private key)"
    
    # We'll try a direct transaction submission (also expected to fail without a signature)
    test_endpoint "/api/transactions" "POST" "{\"sender\":\"${WALLET_ADDRESS}\",\"recipient\":\"GCN_RECIPIENT_ADDRESS\",\"amount\":1.0,\"fee\":0.001,\"signature\":\"dummy_signature\"}" 400 "Submitting a transaction (expected to fail without valid signature)"
fi

echo -e "${BLUE}PHASE 6: Network${NC}"
echo "================================================================"
test_endpoint "/api/network/peers" "GET" "" 200 "Getting connected peers"
test_endpoint "/api/network/nodes" "GET" "" 200 "Getting known nodes"
test_endpoint "/api/network/stats" "GET" "" 200 "Getting network statistics"
test_endpoint "/api/network/sync" "POST" "" 200 "Synchronizing with network"
test_endpoint "/api/network/connect" "POST" "{\"address\":\"localhost\",\"port\":9001}" 400 "Connecting to another peer (expected to fail without auth token)"

# Clean up
rm -f response.txt

echo -e "${GREEN}All tests completed!${NC}"
echo "Summary:"
echo "- Wallet address created: ${WALLET_ADDRESS:-None}"
echo "- Transaction hash: ${TRANSACTION_HASH:-None}"