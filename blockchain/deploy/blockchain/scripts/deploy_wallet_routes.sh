#!/bin/bash
# Script to deploy wallet_routes.py to bootstrap nodes

# Set variables
ROUTES_FILE="wallet_routes.py"
NODE1_DIR="/home/ec2-user/bootstrap_node_1/node"
NODE2_DIR="/home/ec2-user/bootstrap_node_2/node"

# Create directory for routes if it doesn't exist
mkdir -p $NODE1_DIR/routes
mkdir -p $NODE2_DIR/routes

# Copy wallet_routes.py to the routes directory
cat > $NODE1_DIR/routes/$ROUTES_FILE << 'EOL'
from flask import Blueprint, request, jsonify
import os
import sys
import json
import traceback
from typing import Dict, Any, Optional, List

# Import wallet module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from wallet import Wallet
except ImportError:
    # Try alternative import path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from wallet import Wallet

# Create Flask Blueprint for wallet routes
wallet_bp = Blueprint("wallet", __name__)

# Create a global wallet instance
wallet = Wallet()

@wallet_bp.route("/create", methods=["POST"])
def create_wallet():
    """Create a new wallet address"""
    try:
        # Generate a new wallet address
        address = wallet.create_new_address()
        
        # Save wallet to file
        wallet.save_to_file()
        
        return jsonify({
            "success": True,
            "address": address,
            "message": "Wallet created successfully"
        }), 201
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@wallet_bp.route("/generate-seed", methods=["GET"])
def generate_seed_phrase():
    """Generate a new BIP-39 seed phrase"""
    try:
        # Generate a new seed phrase
        seed_phrase = wallet.generate_seed_phrase()
        
        return jsonify({
            "success": True,
            "seedPhrase": seed_phrase
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@wallet_bp.route("/import/seed", methods=["POST"])
def import_seed_phrase():
    """Import a wallet using a seed phrase"""
    try:
        data = request.get_json()
        
        if not data or "seedPhrase" not in data:
            return jsonify({
                "success": False,
                "error": "Seed phrase is required"
            }), 400
        
        seed_phrase = data["seedPhrase"]
        
        # Create wallet from seed phrase
        address = wallet.create_from_seed_phrase(seed_phrase)
        
        # Save wallet to file
        wallet.save_to_file()
        
        return jsonify({
            "success": True,
            "address": address,
            "message": "Wallet imported successfully"
        }), 200
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@wallet_bp.route("/import/key", methods=["POST"])
def import_private_key():
    """Import a wallet using a private key"""
    try:
        data = request.get_json()
        
        if not data or "privateKey" not in data:
            return jsonify({
                "success": False,
                "error": "Private key is required"
            }), 400
        
        private_key = data["privateKey"]
        
        # Import private key
        address = wallet.import_private_key(private_key)
        
        if not address:
            return jsonify({
                "success": False,
                "error": "Invalid private key"
            }), 400
        
        # Save wallet to file
        wallet.save_to_file()
        
        return jsonify({
            "success": True,
            "address": address,
            "message": "Wallet imported successfully"
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@wallet_bp.route("/export-key", methods=["POST"])
def export_private_key():
    """Export private key for a wallet address"""
    try:
        data = request.get_json()
        
        if not data or "address" not in data:
            return jsonify({
                "success": False,
                "error": "Wallet address is required"
            }), 400
        
        address = data["address"]
        
        # Export private key
        private_key = wallet.export_private_key(address)
        
        if not private_key:
            return jsonify({
                "success": False,
                "error": "Address not found in wallet"
            }), 404
        
        return jsonify({
            "success": True,
            "privateKey": private_key
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@wallet_bp.route("/list", methods=["GET"])
def list_addresses():
    """List all wallet addresses"""
    try:
        # Load wallet from file
        wallet.load_from_file()
        
        addresses = wallet.get_addresses()
        
        return jsonify({
            "success": True,
            "addresses": addresses
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@wallet_bp.route("/balance/<address>", methods=["GET"])
def get_balance(address):
    """Get balance for a specific wallet address"""
    try:
        # Load wallet for this address
        if not wallet.load_from_address(address):
            return jsonify({
                "success": False,
                "error": "Address not found in wallet"
            }), 404
        
        # Get balance
        balance = wallet.get_balance()
        
        return jsonify({
            "success": True,
            "address": address,
            "balance": balance
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@wallet_bp.route("/transactions/<address>", methods=["GET"])
def get_transactions(address):
    """Get transactions for a wallet address"""
    try:
        from blockchain import Blockchain
        
        # Create blockchain instance
        blockchain = Blockchain()
        
        # Load blockchain data
        blockchain.load_from_file()
        
        # Get transactions for address
        transactions = []
        for block in blockchain.chain:
            for tx in block.transactions:
                if tx.sender == address or tx.recipient == address:
                    transactions.append({
                        "sender": tx.sender,
                        "recipient": tx.recipient,
                        "amount": tx.amount,
                        "fee": tx.fee,
                        "timestamp": tx.timestamp,
                        "blockIndex": block.index,
                        "type": "outgoing" if tx.sender == address else "incoming"
                    })
        
        # Sort transactions by timestamp (newest first)
        transactions.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return jsonify({
            "success": True,
            "address": address,
            "transactions": transactions
        }), 200
    except Exception as e:
        print(f"Error getting transactions: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@wallet_bp.route("/fee-estimate", methods=["GET"])
def get_fee_estimate():
    """Get fee estimate for transactions"""
    try:
        # For now, return a fixed fee estimate
        # In the future, this could be based on network congestion, etc.
        return jsonify({
            "success": True,
            "feeEstimate": 0.001  # Fixed fee of 0.001 GCN
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@wallet_bp.route("/sign-transaction", methods=["POST"])
def sign_transaction_route():
    """Sign a transaction with the wallet's private key"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Transaction data is required"
            }), 400
        
        required_fields = ["sender", "recipient", "amount", "fee"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        sender = data["sender"]
        recipient = data["recipient"]
        amount = float(data["amount"])
        fee = float(data["fee"])
        
        # Ensure the wallet is loaded with the sender's address
        if not wallet.load_from_address(sender):
            return jsonify({
                "success": False,
                "error": "Sender address not found in wallet"
            }), 404
        
        # Sign the transaction
        transaction = wallet.sign_transaction(sender, recipient, amount, fee)
        
        if not transaction:
            return jsonify({
                "success": False,
                "error": "Failed to sign transaction"
            }), 500
        
        # Convert transaction to dict for JSON serialization
        tx_dict = {
            "sender": transaction.sender,
            "recipient": transaction.recipient,
            "amount": transaction.amount,
            "fee": transaction.fee,
            "timestamp": transaction.timestamp,
            "signature": transaction.signature
        }
        
        return jsonify({
            "success": True,
            "transaction": tx_dict
        }), 200
    except Exception as e:
        print(f"Error signing transaction: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
EOL

# Copy to node2 as well
cp $NODE1_DIR/routes/$ROUTES_FILE $NODE2_DIR/routes/

# Update app.py in both bootstrap nodes
# First, let's check if wallet_bp is already imported
if ! grep -q "from routes.wallet_routes import wallet_bp" $NODE1_DIR/app.py; then
    # Add the import statement
    sed -i '/from flask import/a from routes.wallet_routes import wallet_bp' $NODE1_DIR/app.py
    
    # Add the blueprint registration
    sed -i '/app = Flask/a app.register_blueprint(wallet_bp, url_prefix="/api/wallet")' $NODE1_DIR/app.py
fi

if ! grep -q "from routes.wallet_routes import wallet_bp" $NODE2_DIR/app.py; then
    # Add the import statement
    sed -i '/from flask import/a from routes.wallet_routes import wallet_bp' $NODE2_DIR/app.py
    
    # Add the blueprint registration
    sed -i '/app = Flask/a app.register_blueprint(wallet_bp, url_prefix="/api/wallet")' $NODE2_DIR/app.py
fi

# Create an __init__.py file in the routes directory to make it a proper package
touch $NODE1_DIR/routes/__init__.py
touch $NODE2_DIR/routes/__init__.py

# Restart the bootstrap nodes
systemctl restart globalcoyn-bootstrap1
systemctl restart globalcoyn-bootstrap2

echo "Wallet routes deployment completed. Bootstrap nodes restarted."