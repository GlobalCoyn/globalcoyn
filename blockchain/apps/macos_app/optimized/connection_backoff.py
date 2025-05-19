"""
Connection backoff mechanism for GlobalCoyn blockchain
This module provides connection retry logic with exponential backoff
"""
import time
import logging
import random
from typing import Dict, Any, Optional

class ConnectionManager:
    """
    Manages connection attempts with exponential backoff to prevent
    excessive retries and error logs
    """
    
    def __init__(self, max_retry_interval: int = 300):
        """
        Initialize the connection manager
        
        Args:
            max_retry_interval: Maximum seconds to wait between retries (default 5 minutes)
        """
        self.connection_failures: Dict[str, Dict[str, Any]] = {}
        self.max_retry_interval = max_retry_interval
        self.logger = logging.getLogger("connection_manager")
    
    def should_attempt_connection(self, endpoint: str) -> bool:
        """
        Determine if a connection attempt should be made based on backoff status
        
        Args:
            endpoint: The endpoint URL to check
            
        Returns:
            bool: True if connection should be attempted, False to skip
        """
        # Initialize tracking for this endpoint if it doesn't exist
        if endpoint not in self.connection_failures:
            self.connection_failures[endpoint] = {
                "count": 0,
                "last_attempt": 0,
                "last_success": 0,
                "error_logged": False
            }
        
        failures = self.connection_failures[endpoint]
        now = time.time()
        
        # If we've had failures, implement exponential backoff
        if failures["count"] > 0:
            # Calculate backoff time: 2^failures up to max_retry_interval
            # Add some jitter to prevent synchronized retries
            backoff_seconds = min(
                self.max_retry_interval,
                (2 ** min(failures["count"], 8)) * (0.8 + 0.4 * random.random())
            )
            
            # If we haven't waited long enough, skip this attempt
            if now - failures["last_attempt"] < backoff_seconds:
                return False
        
        # Update the last attempt time
        failures["last_attempt"] = now
        return True
    
    def record_failure(self, endpoint: str, error: Optional[Exception] = None) -> None:
        """
        Record a connection failure and determine if it should be logged
        
        Args:
            endpoint: The endpoint URL that failed
            error: Optional exception object
        """
        if endpoint not in self.connection_failures:
            self.connection_failures[endpoint] = {
                "count": 0,
                "last_attempt": time.time(),
                "last_success": 0,
                "error_logged": False
            }
        
        failures = self.connection_failures[endpoint]
        failures["count"] += 1
        
        # Determine if we should log this error
        # Log the 1st, 2nd, 3rd, 5th, 10th, 20th, etc. failures
        should_log = (
            failures["count"] <= 3 or
            failures["count"] == 5 or
            failures["count"] == 10 or
            failures["count"] % 20 == 0
        )
        
        if should_log:
            failures["error_logged"] = True
            if error:
                self.logger.warning(
                    f"Connection to {endpoint} failed ({failures['count']} failures): {str(error)}"
                )
            else:
                self.logger.warning(
                    f"Connection to {endpoint} failed ({failures['count']} failures)"
                )
    
    def record_success(self, endpoint: str) -> None:
        """
        Record a successful connection
        
        Args:
            endpoint: The endpoint URL that succeeded
        """
        if endpoint not in self.connection_failures:
            self.connection_failures[endpoint] = {
                "count": 0,
                "last_attempt": time.time(),
                "last_success": time.time(),
                "error_logged": False
            }
        
        failures = self.connection_failures[endpoint]
        
        # If this was previously failing, log the recovery
        if failures["count"] > 3:
            self.logger.info(f"Connection to {endpoint} restored after {failures['count']} failures")
        
        # Reset the failure count and update success time
        failures["count"] = 0
        failures["last_success"] = time.time()
        failures["error_logged"] = False