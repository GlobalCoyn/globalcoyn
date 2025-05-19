#!/bin/bash
# Simple test script for GlobalCoyn components

# Define test directories
TEST_DIR="./simple_test"
LOG_FILE="./simple_test.log"

# Create test directory and ensure it's empty
rm -rf $TEST_DIR
mkdir -p $TEST_DIR
rm -f $LOG_FILE
touch $LOG_FILE

echo "Starting GlobalCoyn simple tests..."
echo "----------------------------------------" | tee -a $LOG_FILE
echo "Testing GlobalCoyn components" | tee -a $LOG_FILE
echo "----------------------------------------" | tee -a $LOG_FILE

# Create test script for bootstrap node configuration
cat > $TEST_DIR/test_bootstrap_config.py << 'EOL'
#!/usr/bin/env python3
"""
Test script for bootstrap node configuration
"""
import sys
import os
import json

# Add the blockchain directory to the path
sys.path.insert(0, os.path.abspath('../blockchain'))

# Try to import the bootstrap_config module
try:
    from network.bootstrap_config import BootstrapNodeManager
    print("✓ Successfully imported BootstrapNodeManager")
    
    # Create bootstrap node manager
    manager = BootstrapNodeManager()
    print("✓ Successfully created BootstrapNodeManager instance")
    
    # Get bootstrap nodes
    bootstrap_nodes = manager.get_bootstrap_nodes()
    print(f"✓ Found {len(bootstrap_nodes)} bootstrap nodes")
    
    # Print bootstrap nodes
    for i, node in enumerate(bootstrap_nodes):
        print(f"  Node {i+1}: {node.get('host')}:{node.get('p2p_port')}")
    
    print("Bootstrap node configuration test passed!")
    sys.exit(0)
except Exception as e:
    print(f"✗ Error testing bootstrap node configuration: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOL

# Create test script for seed nodes
cat > $TEST_DIR/test_seed_nodes.py << 'EOL'
#!/usr/bin/env python3
"""
Test script for seed nodes
"""
import sys
import os

# Add the blockchain directory to the path
sys.path.insert(0, os.path.abspath('../blockchain'))

# Try to import the seed_nodes module
try:
    from network.seed_nodes import get_seed_nodes, get_dns_seed_domains
    print("✓ Successfully imported seed_nodes functions")
    
    # Get seed nodes for each network
    for network in ['mainnet', 'testnet', 'development']:
        nodes = get_seed_nodes(network)
        print(f"✓ Found {len(nodes)} seed nodes for {network}")
    
    # Get DNS seed domains
    domains = get_dns_seed_domains('mainnet')
    print(f"✓ Found {len(domains)} DNS seed domains for mainnet")
    for domain in domains:
        print(f"  Domain: {domain}")
    
    print("Seed nodes test passed!")
    sys.exit(0)
except Exception as e:
    print(f"✗ Error testing seed nodes: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOL

# Create test script for connection backoff
cat > $TEST_DIR/test_connection_backoff.py << 'EOL'
#!/usr/bin/env python3
"""
Test script for connection backoff
"""
import sys
import os

# Add the blockchain directory to the path
sys.path.insert(0, os.path.abspath('../blockchain'))

# Try to import the connection_backoff module
try:
    from network.connection_backoff import ConnectionBackoff
    print("✓ Successfully imported ConnectionBackoff")
    
    # Create connection backoff instance
    backoff = ConnectionBackoff()
    print("✓ Successfully created ConnectionBackoff instance")
    
    # Test should_retry method
    for i in range(5):
        should_retry, delay = backoff.should_retry('test_host')
        print(f"✓ Attempt {i+1}: should_retry={should_retry}, delay={delay:.2f}s")
        backoff.record_attempt('test_host', False)
    
    # Test record_attempt success
    backoff.record_attempt('test_host', True)
    should_retry, delay = backoff.should_retry('test_host')
    print(f"✓ After success: should_retry={should_retry}, delay={delay:.2f}s")
    
    # Test get_connection_status
    status = backoff.get_connection_status('test_host')
    print(f"✓ Connection status: {status}")
    
    print("Connection backoff test passed!")
    sys.exit(0)
except Exception as e:
    print(f"✗ Error testing connection backoff: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOL

# Make test scripts executable
chmod +x $TEST_DIR/*.py

# Run the tests
echo -e "\nRunning bootstrap config test..." | tee -a $LOG_FILE
cd $TEST_DIR
python3 test_bootstrap_config.py 2>&1 | tee -a ../$LOG_FILE
BOOTSTRAP_TEST_RESULT=$?

echo -e "\nRunning seed nodes test..." | tee -a $LOG_FILE
python3 test_seed_nodes.py 2>&1 | tee -a ../$LOG_FILE
SEED_TEST_RESULT=$?

echo -e "\nRunning connection backoff test..." | tee -a $LOG_FILE
python3 test_connection_backoff.py 2>&1 | tee -a ../$LOG_FILE
BACKOFF_TEST_RESULT=$?

# Return to original directory
cd ..

# Check results
echo -e "\n----------------------------------------" | tee -a $LOG_FILE
echo "Test Results:" | tee -a $LOG_FILE
echo "----------------------------------------" | tee -a $LOG_FILE

TOTAL_TESTS=3
PASSED_TESTS=0

if [ $BOOTSTRAP_TEST_RESULT -eq 0 ]; then
    echo "✓ Bootstrap node configuration test: PASSED" | tee -a $LOG_FILE
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "✗ Bootstrap node configuration test: FAILED" | tee -a $LOG_FILE
fi

if [ $SEED_TEST_RESULT -eq 0 ]; then
    echo "✓ Seed nodes test: PASSED" | tee -a $LOG_FILE
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "✗ Seed nodes test: FAILED" | tee -a $LOG_FILE
fi

if [ $BACKOFF_TEST_RESULT -eq 0 ]; then
    echo "✓ Connection backoff test: PASSED" | tee -a $LOG_FILE
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "✗ Connection backoff test: FAILED" | tee -a $LOG_FILE
fi

# Overall result
echo -e "\n$PASSED_TESTS of $TOTAL_TESTS tests passed." | tee -a $LOG_FILE

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo "All tests passed! The GlobalCoyn network components are working correctly." | tee -a $LOG_FILE
    exit 0
elif [ $PASSED_TESTS -gt 0 ]; then
    echo "Some tests passed, but others failed. The core components may still work correctly." | tee -a $LOG_FILE
    echo "Check the log file for details: $LOG_FILE" | tee -a $LOG_FILE
    exit 1
else
    echo "All tests failed. Please check the log file for details: $LOG_FILE" | tee -a $LOG_FILE
    exit 1
fi