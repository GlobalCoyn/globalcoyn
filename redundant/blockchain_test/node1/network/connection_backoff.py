"""
GlobalCoyn Connection Backoff Strategy
-----------------------------------
Implements connection retry logic with exponential backoff.
"""

import time
import random
import logging
from typing import Dict, Any, Tuple, Optional, Callable

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("connection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gcn_connection")

class ConnectionBackoff:
    """Manages connection retry with exponential backoff"""
    
    def __init__(self, max_retries: int = 5, 
                 initial_delay: float = 1.0, 
                 max_delay: float = 300.0,
                 jitter: float = 0.1):
        """
        Initialize connection backoff manager.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay between retries (seconds)
            max_delay: Maximum delay between retries (seconds)
            jitter: Random factor to add to delays (0.0-1.0)
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.jitter = jitter
        
        # Connection tracking
        self.connection_history: Dict[str, Dict[str, Any]] = {}
    
    def should_retry(self, connection_id: str) -> Tuple[bool, float]:
        """
        Determine if a connection should be retried and the delay.
        
        Args:
            connection_id: Unique identifier for the connection (e.g., "host:port")
            
        Returns:
            Tuple of (should_retry, delay)
        """
        # Get connection history or create new entry
        if connection_id not in self.connection_history:
            self.connection_history[connection_id] = {
                "attempts": 0,
                "last_attempt": 0,
                "last_success": 0,
                "consecutive_failures": 0
            }
        
        history = self.connection_history[connection_id]
        now = time.time()
        
        # Check if we've reached max retries
        if history["consecutive_failures"] >= self.max_retries:
            # Reset if it's been a long time since last attempt
            if now - history["last_attempt"] > self.max_delay * 2:
                history["consecutive_failures"] = 0
            else:
                return False, self.max_delay
        
        # Calculate backoff delay
        delay = min(
            self.initial_delay * (2 ** history["consecutive_failures"]),
            self.max_delay
        )
        
        # Add jitter to avoid thundering herd
        if self.jitter > 0:
            jitter_amount = delay * self.jitter
            delay = delay + random.uniform(-jitter_amount, jitter_amount)
        
        # Ensure minimum delay
        delay = max(delay, self.initial_delay)
        
        # Check if we've waited long enough
        time_since_last_attempt = now - history["last_attempt"]
        if time_since_last_attempt < delay:
            # Not enough time has passed
            return False, delay - time_since_last_attempt
        
        return True, 0
    
    def record_attempt(self, connection_id: str, success: bool) -> None:
        """
        Record a connection attempt.
        
        Args:
            connection_id: Unique identifier for the connection
            success: Whether the attempt succeeded
        """
        if connection_id not in self.connection_history:
            self.connection_history[connection_id] = {
                "attempts": 0,
                "last_attempt": 0,
                "last_success": 0,
                "consecutive_failures": 0
            }
        
        history = self.connection_history[connection_id]
        now = time.time()
        
        # Update history
        history["attempts"] += 1
        history["last_attempt"] = now
        
        if success:
            history["last_success"] = now
            history["consecutive_failures"] = 0
            logger.info(f"Connection to {connection_id} succeeded")
        else:
            history["consecutive_failures"] += 1
            failures = history["consecutive_failures"]
            logger.warning(f"Connection to {connection_id} failed (consecutive failures: {failures})")
    
    def with_retry(self, connection_id: str, 
                  connect_func: Callable[[], Any], 
                  on_success: Optional[Callable[[Any], None]] = None,
                  on_failure: Optional[Callable[[Exception], None]] = None,
                  on_max_retries: Optional[Callable[[], None]] = None) -> Any:
        """
        Execute a connection function with retry logic.
        
        Args:
            connection_id: Unique identifier for the connection
            connect_func: Function to execute (returns connection object)
            on_success: Called on successful connection
            on_failure: Called on failed attempt (with exception)
            on_max_retries: Called when max retries reached
            
        Returns:
            Result of connect_func or None if all attempts failed
        """
        # Check if we should retry
        should_retry, delay = self.should_retry(connection_id)
        if not should_retry:
            logger.info(f"Skipping connection to {connection_id}, retry in {delay:.1f}s")
            if on_max_retries:
                on_max_retries()
            return None
        
        # Attempt connection
        try:
            result = connect_func()
            self.record_attempt(connection_id, True)
            if on_success:
                on_success(result)
            return result
        except Exception as e:
            self.record_attempt(connection_id, False)
            logger.warning(f"Connection to {connection_id} failed: {str(e)}")
            if on_failure:
                on_failure(e)
            return None
    
    def get_connection_status(self, connection_id: str) -> Dict[str, Any]:
        """
        Get status information for a connection.
        
        Args:
            connection_id: Unique identifier for the connection
            
        Returns:
            Status information or empty dict if not found
        """
        return self.connection_history.get(connection_id, {})