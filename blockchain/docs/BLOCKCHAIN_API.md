# GlobalCoyn Blockchain API Documentation

This document provides a comprehensive guide to the GlobalCoyn blockchain API endpoints, their parameters, and response formats.

## API Base URL

All API endpoints are relative to the base URL of your GlobalCoyn node:

```
http://localhost:8001/api
```

Replace `localhost:8001` with the hostname and port where your node is running.

## Authentication

Most endpoints do not require authentication. However, some administrative endpoints may require authentication in future versions.

## General Endpoints

### Get Blockchain Status

Retrieves current blockchain status, including height, latest block, and difficulty.

- **URL**: `/blockchain`
- **Method**: `GET`
- **URL Parameters**: None
- **Success Response**:
  - **Code**: 200
  - **Content**:
  ```json
  {
    "status": "online",
    "chain_length": 37049,
    "latest_block_hash": "000a2c7dcb4c65a83cb9e1c70b25d97b33eb1018ac56a7cd9db2f694b486cd2c",
    "latest_block_timestamp": 1714694389.2853241,
    "difficulty": 4096.0,
    "difficulty_bits": 536936448,
    "difficulty_target": 8796093008896,
    "transactions_in_mempool": 5,
    "node_count": 3,
    "network_mode": "decentralized"
  }
  ```
- **Error Response**:
  - **Code**: 500
  - **Content**: `{"error": "Error message"}`

### Get Full Blockchain

Retrieves the complete blockchain. Note that this can be a large amount of data.

- **URL**: `/chain`
- **Method**: `GET`
- **URL Parameters**: None
- **Success Response**:
  - **Code**: 200
  - **Content**:
  ```json
  {
    "chain": [
      {
        "index": 0,
        "hash": "000e4c98b532fc39d16cee4847299d45e973f2934e1ca4baf3f24fd27ac82ea3",
        "previous_hash": "0",
        "timestamp": 1714432597.1234567,
        "transactions": [],
        "nonce": 1567284,
        "difficulty_bits": 536936448
      },
      ...
    ]
  }
  ```
- **Error Response**:
  - **Code**: 500
  - **Content**: `{"error": "Error message"}`

### Get Mempool Transactions

Retrieves all pending transactions in the mempool.

- **URL**: `/mempool`
- **Method**: `GET`
- **URL Parameters**: None
- **Success Response**:
  - **Code**: 200
  - **Content**:
  ```json
  {
    "mempool": [
      {
        "sender": "1D8xJ6pXpToUY9etHPXvKCKiTsVZ5QTN6p",
        "recipient": "16eDU1qRxJ9ztGQC9v59VMJpQXZzHAqWxN",
        "amount": 5.25,
        "fee": 0.001,
        "signature": "3045022100a4c95...",
        "timestamp": 1714694435.7634866,
        "transaction_type": "TRANSFER"
      },
      ...
    ]
  }
  ```
- **Error Response**:
  - **Code**: 500
  - **Content**: `{"error": "Error message"}`

### Get Balance

Retrieves the balance for a specific wallet address.

- **URL**: `/balance/<address>`
- **Method**: `GET`
- **URL Parameters**:
  - `address`: The wallet address to check
- **Success Response**:
  - **Code**: 200
  - **Content**:
  ```json
  {
    "address": "1D8xJ6pXpToUY9etHPXvKCKiTsVZ5QTN6p",
    "balance": 142.75
  }
  ```
- **Error Response**:
  - **Code**: 500
  - **Content**: `{"error": "Error message"}`

## Transaction Endpoints

### Add Transaction

Adds a new transaction to the mempool.

- **URL**: `/transaction`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "sender": "1D8xJ6pXpToUY9etHPXvKCKiTsVZ5QTN6p",
    "recipient": "16eDU1qRxJ9ztGQC9v59VMJpQXZzHAqWxN",
    "amount": 5.0,
    "signature": "3045022100a4c95...",
    "fee": 0.001,
    "transaction_type": "TRANSFER"
  }
  ```
- **Success Response**:
  - **Code**: 201
  - **Content**:
  ```json
  {
    "status": "success",
    "transaction": {
      "sender": "1D8xJ6pXpToUY9etHPXvKCKiTsVZ5QTN6p",
      "recipient": "16eDU1qRxJ9ztGQC9v59VMJpQXZzHAqWxN",
      "amount": 5.0,
      "fee": 0.001,
      "signature": "3045022100a4c95...",
      "timestamp": 1714694567.8945672,
      "transaction_type": "TRANSFER"
    }
  }
  ```
- **Error Response**:
  - **Code**: 400
  - **Content**: `{"status": "error", "message": "Transaction validation failed"}`
  - **Code**: 500
  - **Content**: `{"error": "Error message"}`

### Get Transaction History

Retrieves transaction history.

- **URL**: `/transactions/history`
- **Method**: `GET`
- **URL Parameters**: None
- **Success Response**:
  - **Code**: 200
  - **Content**:
  ```json
  {
    "message": "Blockchain transaction history endpoint",
    "transactions": []
  }
  ```
- **Error Response**:
  - **Code**: 500
  - **Content**: `{"error": "Error message"}`

## Mining Endpoints

### Mine Block

Mines a new block with proof-of-work.

- **URL**: `/mine`
- **Method**: `POST`
- **Request Body** (optional):
  ```json
  {
    "miner_address": "1D8xJ6pXpToUY9etHPXvKCKiTsVZ5QTN6p",
    "max_nonce_attempts": 100000
  }
  ```
- **Success Response**:
  - **Code**: 200
  - **Content**:
  ```json
  {
    "status": "success",
    "message": "Successfully mined a new block",
    "block": {
      "index": 37050,
      "hash": "000a2c7dcb4c65a83cb9e1c70b25d97b33eb1018ac56a7cd9db2f694b486cd2c",
      "previous_hash": "000e4c98b532fc39d16cee4847299d45e973f2934e1ca4baf3f24fd27ac82ea3",
      "timestamp": 1714694612.4567893,
      "transactions": [...],
      "nonce": 25684372,
      "difficulty_bits": 536936448,
      "mining_time_seconds": 45.23,
      "hash_attempts": 98742
    }
  }
  ```
  or:
  ```json
  {
    "status": "in_progress",
    "message": "No valid hash found after 100000 attempts",
    "current_nonce": 100000,
    "elapsed_time": 12.5
  }
  ```
- **Error Response**:
  - **Code**: 500
  - **Content**: `{"error": "Error message"}`

### Mine Asynchronously

Mines asynchronously with limited work per request.

- **URL**: `/mine_async`
- **Method**: `POST`
- **Request Body** (optional):
  ```json
  {
    "miner_address": "1D8xJ6pXpToUY9etHPXvKCKiTsVZ5QTN6p",
    "max_attempts": 50000
  }
  ```
- **Success Response**:
  - **Code**: 200
  - **Content** (successful mining):
  ```json
  {
    "status": "success",
    "message": "Successfully mined a new block",
    "block": {
      "index": 37050,
      "hash": "000a2c7dcb4c65a83cb9e1c70b25d97b33eb1018ac56a7cd9db2f694b486cd2c",
      "previous_hash": "000e4c98b532fc39d16cee4847299d45e973f2934e1ca4baf3f24fd27ac82ea3",
      "timestamp": 1714694612.4567893,
      "transactions": [...],
      "nonce": 25684372,
      "difficulty_bits": 536936448,
      "mining_time_seconds": 45.23,
      "hash_attempts": 50000
    }
  }
  ```
  or (no hash found yet):
  ```json
  {
    "status": "continue",
    "message": "No valid hash found after 50000 attempts",
    "target": "0x21000fff",
    "difficulty_bits": "0x2100ffff",
    "time_spent": 5.4,
    "starting_nonce": 567432
  }
  ```
- **Error Response**:
  - **Code**: 400
  - **Content**: `{"status": "error", "message": "Maximum coin supply reached"}`
  - **Code**: 500
  - **Content**: `{"error": "Error message"}`

## Network Endpoints

### Get Network Status

Retrieves current network status.

- **URL**: `/network/status`
- **Method**: `GET`
- **URL Parameters**: None
- **Success Response**:
  - **Code**: 200
  - **Content**:
  ```json
  {
    "status": "online",
    "network_mode": "decentralized",
    "this_node": {
      "address": "localhost",
      "port": 9000,
      "blockchain_height": 37050
    },
    "connected_peers": [
      {
        "node_id": "localhost:9001",
        "address": "localhost",
        "port": 9001,
        "last_seen": 12.5
      },
      ...
    ],
    "peer_count": 2,
    "uptime": 14567.8
  }
  ```
- **Error Response**:
  - **Code**: 500
  - **Content**: `{"error": "Error message"}`

### Get Peers

Retrieves list of connected peers.

- **URL**: `/network/peers`
- **Method**: `GET`
- **URL Parameters**: None
- **Success Response**:
  - **Code**: 200
  - **Content**:
  ```json
  {
    "peers": [
      {
        "node_id": "localhost:9001",
        "address": "localhost",
        "port": 9001,
        "last_seen": 12.5
      },
      ...
    ],
    "count": 2
  }
  ```
- **Error Response**:
  - **Code**: 500
  - **Content**: `{"error": "Error message"}`

### Discover Network

Process network discovery requests and trigger chain sync if needed.

- **URL**: `/network/discover`
- **Method**: `POST`
- **Request Body** (optional):
  ```json
  {
    "chain_length": 37050,
    "sender_port": "localhost:8001"
  }
  ```
- **Success Response**:
  - **Code**: 200
  - **Content**:
  ```json
  {
    "success": true,
    "local_chain_length": 37049,
    "discovered_peers": [
      {
        "node_id": "localhost:9001",
        "address": "localhost",
        "port": 9001
      },
      ...
    ],
    "peer_count": 2
  }
  ```
  or (triggering sync):
  ```json
  {
    "success": true,
    "action": "sync_triggered",
    "local_chain_length": 37049,
    "remote_chain_length": 37050
  }
  ```
- **Error Response**:
  - **Code**: 500
  - **Content**: `{"error": "Error message"}`

### Sync with Network

Synchronize blockchain with other nodes.

- **URL**: `/network/sync`
- **Method**: `POST`
- **URL Parameters**: None
- **Success Response**:
  - **Code**: 200
  - **Content**:
  ```json
  {
    "success": true,
    "local_chain_length_before": 37049,
    "local_chain_length_after": 37050,
    "peers_data": [...],
    "highest_chain_found": 37050,
    "synchronized": true,
    "sync_message": "Synchronized with peer at localhost:8001, chain length now 37050"
  }
  ```
- **Error Response**:
  - **Code**: 500
  - **Content**: `{"error": "Error message"}`

### Connect to Peer

Connect to a specific peer node.

- **URL**: `/network/connect`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "address": "localhost",
    "port": 9001
  }
  ```
- **Success Response**:
  - **Code**: 200
  - **Content**:
  ```json
  {
    "success": true,
    "message": "Successfully connected to peer localhost:9001",
    "node_id": "localhost:9001"
  }
  ```
- **Error Response**:
  - **Code**: 400
  - **Content**: `{"success": false, "message": "Handshake failed"}`
  - **Code**: 500
  - **Content**: `{"error": "Error message"}`

## Block Endpoints

### Get Latest Block

Retrieves the latest block in the blockchain.

- **URL**: `/blocks/latest`
- **Method**: `GET`
- **URL Parameters**: None
- **Success Response**:
  - **Code**: 200
  - **Content**:
  ```json
  {
    "index": 37050,
    "hash": "000a2c7dcb4c65a83cb9e1c70b25d97b33eb1018ac56a7cd9db2f694b486cd2c",
    "previous_hash": "000e4c98b532fc39d16cee4847299d45e973f2934e1ca4baf3f24fd27ac82ea3",
    "timestamp": 1714694612.4567893,
    "transactions": [...],
    "nonce": 25684372,
    "difficulty_target": 536936448
  }
  ```
- **Error Response**:
  - **Code**: 404
  - **Content**: `{"error": "Blockchain is empty"}`
  - **Code**: 500
  - **Content**: `{"error": "Error message"}`

### Get Block by Hash

Retrieves a specific block by its hash.

- **URL**: `/blocks/<block_hash>`
- **Method**: `GET`
- **URL Parameters**:
  - `block_hash`: The hash of the block to retrieve
- **Success Response**:
  - **Code**: 200
  - **Content**:
  ```json
  {
    "index": 37000,
    "hash": "000a2c7dcb4c65a83cb9e1c70b25d97b33eb1018ac56a7cd9db2f694b486cd2c",
    "previous_hash": "000e4c98b532fc39d16cee4847299d45e973f2934e1ca4baf3f24fd27ac82ea3",
    "timestamp": 1714693612.4567893,
    "transactions": [...],
    "nonce": 25684372,
    "difficulty_target": 536936448
  }
  ```
- **Error Response**:
  - **Code**: 404
  - **Content**: `{"error": "Block not found"}`
  - **Code**: 500
  - **Content**: `{"error": "Error message"}`

## Error Handling

The API uses standard HTTP status codes:

- `200`: Success
- `201`: Successfully created resource
- `400`: Bad request (invalid parameters or validation failure)
- `404`: Resource not found
- `500`: Internal server error

All error responses include an `error` field with a description of the error.

## Rate Limiting

Currently, there are no rate limits implemented. However, future versions may include rate limiting to prevent abuse.

## Versioning

This documentation describes v1 of the GlobalCoyn API. Future versions will be available at `/api/v2/`, etc.

## Support

For API support, please create an issue on our GitHub repository or contact our development team directly.