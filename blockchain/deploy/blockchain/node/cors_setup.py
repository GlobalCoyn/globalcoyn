"""
CORS configuration for the GlobalCoyn blockchain node
"""
from flask_cors import CORS
from config_loader import config

def setup_cors(app):
    """
    Configure CORS for the Flask application
    """
    # Get CORS settings from config
    origins = config.get("security", "cors_origins", ["*"])
    
    # In production, ensure we have specific origins rather than wildcard
    if config.is_production() and origins == ["*"]:
        # Default production origins
        origins = [
            "https://globalcoyn.com",
            "https://www.globalcoyn.com"
        ]
    
    # Apply CORS settings
    cors_config = {
        "origins": origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-API-Key", "Authorization"]
    }
    
    # Log CORS configuration
    print(f"Setting up CORS with origins: {origins}")
    
    # Apply CORS to the app
    CORS(app, resources={r"/api/*": cors_config})