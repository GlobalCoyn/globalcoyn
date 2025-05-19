# GlobalCoyn Blockchain API Complete Rewrite Project Plan

## Goal
Completely rewrite and update the GlobalCoyn blockchain API layer to provide a comprehensive, consistent, and fully-functional API that supports all web application requirements and third-party integrations. This will include ensuring all core functionality is properly exposed through well-designed API endpoints while focusing on true blockchain functionality.

## Project Structure
```
blockchain/
├── core/                    # Core blockchain implementation
│   ├── blockchain.py        # Blockchain data structure and operations
│   ├── wallet.py            # Wallet functionality
│   └── coin.py              # Currency implementation
├── api/                     # API implementation
│   ├── server.py            # Main API server
│   └── routes/              # API routes
│       ├── __init__.py
│       ├── blockchain_routes.py  # Blockchain-related endpoints
│       ├── wallet_routes.py      # Wallet-related endpoints
│       ├── transaction_routes.py # Transaction-related endpoints
│       └── network_routes.py     # Network-related endpoints
├── nodes/                   # Bootstrap node implementation
│   ├── node_template/       # Template for node deployment
│   │   ├── app.py           # Node application
│   │   ├── requirements.txt # Dependencies
│   │   └── start_node.sh    # Startup script
│   ├── node1/               # Deployed node 1
│   └── node2/               # Deployed node 2
└── scripts/                 # Deployment and management scripts
    └── deploy_nodes.sh      # Node deployment script
```

## API Endpoints

### Blockchain Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/blockchain` | GET | Get blockchain info (height, latest block, difficulty) |
| `/api/blockchain/chain` | GET | Get the full blockchain |
| `/api/blockchain/blocks/latest` | GET | Get the latest block |
| `/api/blockchain/blocks/<hash>` | GET | Get a specific block by hash |
| `/api/blockchain/blocks/<height>` | GET | Get a specific block by height |
| `/api/blockchain/blocks/mine` | POST | Mine a new block |
| `/api/blockchain/stats` | GET | Get blockchain statistics (total supply, hash rate, etc.) |
| `/api/blockchain/difficulty` | GET | Get current mining difficulty |

### Wallet Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/wallet/create` | POST | Create a new wallet |
| `/api/wallet/generate-seed` | GET | Generate a new seed phrase |
| `/api/wallet/import/seed` | POST | Import wallet from seed phrase |
| `/api/wallet/import/key` | POST | Import wallet from private key |
| `/api/wallet/export-key` | POST | Export wallet private key |
| `/api/wallet/list` | GET | List all wallet addresses |
| `/api/wallet/balance/<address>` | GET | Get wallet balance |
| `/api/wallet/transactions/<address>` | GET | Get wallet transactions |
| `/api/wallet/fee-estimate` | GET | Get transaction fee estimate |
| `/api/wallet/sign-transaction` | POST | Sign a transaction |
| `/api/wallet/validate/<address>` | GET | Validate a wallet address |
| `/api/wallet/delete` | DELETE | Delete a wallet (securely) |
| `/api/wallet/mining-stats/<address>` | GET | Get mining statistics for a wallet |

### Transaction Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/transactions` | GET | Get all mempool transactions |
| `/api/transactions` | POST | Create and submit a new transaction |
| `/api/transactions/<tx_hash>` | GET | Get transaction details |
| `/api/transactions/mempool` | GET | Get current mempool state |
| `/api/transactions/verify/<tx_hash>` | GET | Verify a transaction's validity |
| `/api/transactions/fees` | GET | Get recommended transaction fees |

### Network Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/network/status` | GET | Get network status |
| `/api/network/peers` | GET | Get connected peers |
| `/api/network/sync` | POST | Synchronize with the network |
| `/api/network/connect` | POST | Connect to a specific peer |
| `/api/network/nodes` | GET | Get list of known nodes |
| `/api/network/stats` | GET | Get network statistics |

## Implementation Steps

### 1. Core Updates
- Update core blockchain.py to ensure all necessary functionality is available:
  - Remove price_oracle.py import and all references to PRICE_ORACLE
  - Remove market-related transaction types ("PURCHASE" and "SELL")
  - Remove price and total_cost fields from Transaction class
  - Remove market-specific validation in add_transaction_to_mempool
  - Simplify get_current_supply to focus only on mining rewards
  - Remove market price updates from mine_block method
  - Remove special handling for "MARKET" address
- Update wallet.py implementation for complete wallet functionality:
  - Focus on core wallet operations: creation, import/export, signing
  - Remove market-related balance caching
  - Add support for wallet deletion and validation
  - Add mining statistics tracking
- Ensure coin.py provides proper coin management functionality
- Remove price_oracle.py completely from the codebase

### 2. API Implementation
- Implement each API route blueprint following a consistent pattern:
  - Proper error handling
  - Consistent response format
  - Comprehensive documentation
  - Type hints and validation
- Ensure removal of all market-related functionality and endpoints

### 3. Server Implementation
- Create a unified server.py that correctly imports and registers all blueprints
- Ensure proper CORS configuration
- Add health check and error handlers
- Remove price oracle integration

### 4. Bootstrap Node Implementation
- Update node template to use the new API implementation
- Ensure proper initialization and configuration
- Add P2P networking functionality for node synchronization
- Add configuration for connecting to external exchanges (if needed)

### 5. Frontend Integration
- Update walletService.js to correctly use all the new API endpoints
- Implement proper error handling and fallbacks
- Ensure a consistent interface for the web application
- Update UI to remove internal market operations
- Add support for integrating with external exchanges if needed

### 6. Deployment
- Create deployment scripts for setting up bootstrap nodes
- Test deployment in a staging environment
- Deploy to production environment
- Provide documentation for third-party exchange integration

## Testing Strategy
- Implement unit tests for core functionality
- Create automated API tests for all endpoints
- Perform integration testing with the web frontend
- Conduct manual testing of key workflows
- Test integration capabilities with third-party exchange APIs

## Deployment Strategy
1. Develop and test all components locally
2. Create a comprehensive deployment package
3. Set up the bootstrap nodes on the server
4. Update the web application configuration
5. Verify connectivity and functionality
6. Switch over to the new implementation
7. Document third-party integration options

## Success Criteria
- All API endpoints are implemented and functioning
- Web application can interact with the blockchain using the API
- Transactions and wallet operations work correctly
- Blockchain synchronization maintains consistency
- System performance is acceptable under load
- No dependencies on internal market functionality or price oracle
- Clear documentation for third-party exchange integration