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
