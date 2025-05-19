#!/bin/bash
  # GlobalCoyn Production API Test

  # Configuration
  PROD_URL="https://globalcoyn.com"
  YELLOW='\033[1;33m'
  GREEN='\033[0;32m'
  RED='\033[0;31m'
  BLUE='\033[0;34m'
  NC='\033[0m'

  test_endpoint() {
      local endpoint="$1"
      local method="${2:-GET}"
      local data="$3"
      local expected_status="${4:-200}"
      local description="${5:-Testing endpoint}"

      echo -e "${BLUE}$description${NC}"
      echo -e "${YELLOW}Testing ${method} ${PROD_URL}${endpoint}${NC}"

      if [ "$method" = "GET" ]; then
          response=$(curl -s -o response.txt -w "%{http_code}" -X GET "${PROD_URL}${endpoint}")
      else
          if [ -n "$data" ]; then
              response=$(curl -s -o response.txt -w "%{http_code}" -X "${method}" -H "Content-Type: 
  application/json" -d "${data}" "${PROD_URL}${endpoint}")
          else
              response=$(curl -s -o response.txt -w "%{http_code}" -X "${method}"
  "${PROD_URL}${endpoint}")
          fi
      fi

      if [ "$response" -eq "$expected_status" ]; then
          echo -e "${GREEN}✓ Status: ${response} (Expected: ${expected_status})${NC}"
          echo "Response body:"
          cat response.txt | grep -v "^$" | sed 's/^/  /'
      else
          echo -e "${RED}✗ Status: ${response} (Expected: ${expected_status})${NC}"
          echo "Response body:"
          cat response.txt | grep -v "^$" | sed 's/^/  /'
      fi

      echo "----------------------------------------------------------------"
  }

  echo -e "${YELLOW}GlobalCoyn Production API Test Script${NC}"
  echo "Testing against: ${PROD_URL}"
  echo "================================================================"

  # Basic connectivity
  test_endpoint "/api/blockchain/" "GET" "" 200 "Testing blockchain info endpoint"

  # CORS test
  test_endpoint "/api/wallet/generate-seed" "OPTIONS" "" 204 "Testing CORS preflight request"

  # Critical API endpoints
  test_endpoint "/api/blockchain/blocks/latest" "GET" "" 200 "Getting latest block"
  test_endpoint "/api/blockchain/chain" "GET" "" 200 "Getting blockchain data"
  test_endpoint "/api/blockchain/mempool" "GET" "" 200 "Getting mempool"
  test_endpoint "/api/wallet/generate-seed" "GET" "" 200 "Testing wallet seed generation"
  test_endpoint "/api/wallet/fee-estimate" "GET" "" 200 "Getting fee estimate"

  # Optional - create a test wallet (will use resources)
  # test_endpoint "/api/wallet/create" "POST" "" 201 "Creating a test wallet"

  # Clean up
  rm -f response.txt

  echo -e "${GREEN}All tests completed!${NC}"