"""
Blockchain API Server
--------------------
This server provides a RESTful API for interacting with the blockchain.
It does not store any data itself, but acts as an interface to the blockchain nodes.
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional
from functools import wraps

# Add the blockchain directory to the Python path
BLOCKCHAIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BLOCKCHAIN_DIR)

from flask import Flask, jsonify, request, abort, make_response
from flask_cors import CORS

# Create the Flask application
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Import route blueprints
from routes.blockchain_routes import blockchain_bp
from routes.transaction_routes import transaction_bp
from routes.network_routes import network_bp
from routes.wallet_routes import wallet_bp

# Register blueprints
app.register_blueprint(blockchain_bp, url_prefix='/api/blockchain')
app.register_blueprint(transaction_bp, url_prefix='/api/transactions')
app.register_blueprint(network_bp, url_prefix='/api/network')
app.register_blueprint(wallet_bp, url_prefix='/api/wallet')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "blockchain-api"
    }), 200

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "error": "Not Found",
        "message": "The requested resource was not found."
    }), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred on the server."
    }), 500

if __name__ == '__main__':
    # Get configuration from environment variables
    host = os.environ.get('API_HOST', '0.0.0.0')
    port = int(os.environ.get('API_PORT', 5000))
    debug = os.environ.get('API_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting Blockchain API server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)