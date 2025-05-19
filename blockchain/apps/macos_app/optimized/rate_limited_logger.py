"""
Rate-limited logger for GlobalCoyn
Reduces log spam by limiting repeated log messages
"""
import time
import logging
import threading
from typing import Dict, Any, Optional

class RateLimitedLogger:
    """
    A logging wrapper that throttles repeated messages
    to reduce log spam and improve readability
    """
    
    def __init__(self, name: str = "rate_limited", default_logger: Optional[logging.Logger] = None):
        """
        Initialize the rate-limited logger
        
        Args:
            name: Logger name
            default_logger: Optional existing logger to wrap
        """
        self.name = name
        self.logger = default_logger or logging.getLogger(name)
        self.message_history: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        
        # Configure summary reporting
        self.summary_interval = 300  # 5 minutes
        self.last_summary = time.time()
        
        # Start summary thread
        self.summary_thread = threading.Thread(target=self._periodic_summary, daemon=True)
        self.summary_thread.start()
    
    def _periodic_summary(self):
        """Periodically report summary of throttled messages"""
        while True:
            time.sleep(60)  # Check every minute
            
            now = time.time()
            if now - self.last_summary >= self.summary_interval:
                self._report_summary()
                self.last_summary = now
    
    def _report_summary(self):
        """Report summary of throttled messages"""
        with self.lock:
            # Find messages with suppressed log entries
            suppressed_messages = {
                key: info for key, info in self.message_history.items()
                if info["suppressed_count"] > 0
            }
            
            if suppressed_messages:
                self.logger.info(f"--- Log Summary (Throttled Messages) ---")
                for key, info in suppressed_messages.items():
                    self.logger.info(
                        f"[{info['level'].upper()}] {info['last_message']} "
                        f"(suppressed {info['suppressed_count']} similar logs in the last 5 minutes)"
                    )
                    # Reset suppression counter after reporting
                    info["suppressed_count"] = 0
    
    def _log_with_rate_limiting(self, level: str, message: str, key: Optional[str] = None, force: bool = False):
        """
        Log a message with rate limiting
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            message: The message to log
            key: Optional key to group similar messages (defaults to message itself)
            force: If True, bypass rate limiting and always log
        """
        if key is None:
            # Use message as the key if not specified
            key = message
        
        now = time.time()
        
        with self.lock:
            # Initialize tracking for this message if it doesn't exist
            if key not in self.message_history:
                self.message_history[key] = {
                    "last_time": 0,
                    "count": 0,
                    "suppressed_count": 0,
                    "level": level,
                    "last_message": message
                }
            
            info = self.message_history[key]
            info["last_message"] = message
            info["level"] = level
            info["count"] += 1
            
            # Determine if we should log this message
            too_frequent = (now - info["last_time"] < self._get_threshold(level))
            
            if force or not too_frequent:
                # Log the message with the specified level
                log_method = getattr(self.logger, level)
                log_method(message)
                
                # If we've suppressed messages since the last actual log, add a count
                if info["suppressed_count"] > 0:
                    log_method(f"(Suppressed {info['suppressed_count']} similar messages)")
                    info["suppressed_count"] = 0
                
                # Update the timestamp
                info["last_time"] = now
            else:
                # Message was suppressed, increment counter
                info["suppressed_count"] += 1
    
    def _get_threshold(self, level: str) -> float:
        """
        Get the throttling threshold based on log level
        
        Args:
            level: Log level
            
        Returns:
            float: Minimum seconds between logs of this level
        """
        # More severe logs have lower thresholds (less throttling)
        thresholds = {
            "debug": 30.0,      # 30 seconds between identical debug messages
            "info": 15.0,       # 15 seconds between identical info messages
            "warning": 10.0,    # 10 seconds between identical warning messages
            "error": 5.0,       # 5 seconds between identical error messages
            "critical": 0.0     # Never throttle critical messages
        }
        return thresholds.get(level, 15.0)
    
    def debug(self, message: str, key: Optional[str] = None, force: bool = False):
        """Log a debug message with rate limiting"""
        self._log_with_rate_limiting("debug", message, key, force)
    
    def info(self, message: str, key: Optional[str] = None, force: bool = False):
        """Log an info message with rate limiting"""
        self._log_with_rate_limiting("info", message, key, force)
    
    def warning(self, message: str, key: Optional[str] = None, force: bool = False):
        """Log a warning message with rate limiting"""
        self._log_with_rate_limiting("warning", message, key, force)
    
    def error(self, message: str, key: Optional[str] = None, force: bool = False):
        """Log an error message with rate limiting"""
        self._log_with_rate_limiting("error", message, key, force)
    
    def critical(self, message: str, key: Optional[str] = None, force: bool = False):
        """Log a critical message with rate limiting"""
        self._log_with_rate_limiting("critical", message, key, force)
    
    # Aliases for common method names
    warn = warning
    exception = error