#!/bin/bash

# Fix Bootstrap Contract Functionality
# This script restarts the correct bootstrap services to ensure contract functionality is loaded

echo "=== GlobalCoyn Bootstrap Contract Fix ==="
echo "Fixing contract functionality on bootstrap nodes..."

# Function to test contract endpoint
test_contract_endpoint() {
    local port=$1
    local node_name=$2
    
    echo "Testing contract functionality on $node_name (port $port)..."
    
    response=$(curl -s -w "%{http_code}" -o /tmp/contract_test_${port} "http://localhost:${port}/api/contracts/types" 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        echo "✅ $node_name contract functionality is working"
        return 0
    elif [ "$response" = "500" ]; then
        echo "❌ $node_name has contract functionality error"
        return 1
    else
        echo "⚠️  $node_name returned status code: $response"
        return 1
    fi
}

# Test both nodes first
echo "Step 1: Testing current contract functionality..."
bootstrap1_working=$(test_contract_endpoint 8001 "Bootstrap Node 1"; echo $?)
bootstrap2_working=$(test_contract_endpoint 8002 "Bootstrap Node 2"; echo $?)

if [ "$bootstrap1_working" = "0" ] && [ "$bootstrap2_working" = "0" ]; then
    echo "✅ Both bootstrap nodes have working contract functionality. No action needed."
    exit 0
fi

# Check if services exist
echo "Step 2: Checking service status..."
if ! systemctl is-active --quiet globalcoyn-bootstrap1; then
    echo "⚠️  globalcoyn-bootstrap1 service is not active"
fi

if ! systemctl is-active --quiet globalcoyn-bootstrap2; then
    echo "⚠️  globalcoyn-bootstrap2 service is not active"
fi

# Restart the bootstrap services
echo "Step 3: Restarting bootstrap services to reload contract functionality..."

echo "Stopping bootstrap services..."
sudo systemctl stop globalcoyn-bootstrap1.service globalcoyn-bootstrap2.service

echo "Waiting 5 seconds..."
sleep 5

echo "Starting bootstrap services..."
sudo systemctl start globalcoyn-bootstrap1.service globalcoyn-bootstrap2.service

echo "Waiting 15 seconds for services to fully start..."
sleep 15

# Test again
echo "Step 4: Testing contract functionality after restart..."
bootstrap1_working=$(test_contract_endpoint 8001 "Bootstrap Node 1"; echo $?)
bootstrap2_working=$(test_contract_endpoint 8002 "Bootstrap Node 2"; echo $?)

# Check results
if [ "$bootstrap1_working" = "0" ] && [ "$bootstrap2_working" = "0" ]; then
    echo "✅ SUCCESS: Both bootstrap nodes now have working contract functionality!"
    
    # Test with domain as well
    echo "Step 5: Testing via domain..."
    domain_response=$(curl -s -w "%{http_code}" -o /tmp/contract_test_domain "https://globalcoyn.com/api/contracts/types" 2>/dev/null)
    
    if [ "$domain_response" = "200" ]; then
        echo "✅ Domain contract functionality is also working"
    else
        echo "⚠️  Domain returned status code: $domain_response (may be nginx routing issue)"
    fi
    
    exit 0
else
    echo "❌ FAILED: Contract functionality still not working after restart"
    
    # Show service status for debugging
    echo "Service status:"
    systemctl status globalcoyn-bootstrap1.service --no-pager -l
    systemctl status globalcoyn-bootstrap2.service --no-pager -l
    
    echo "Recent logs:"
    journalctl -u globalcoyn-bootstrap1.service --since "2 minutes ago" --no-pager -l
    journalctl -u globalcoyn-bootstrap2.service --since "2 minutes ago" --no-pager -l
    
    exit 1
fi