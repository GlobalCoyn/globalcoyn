# GlobalCoyn Blockchain Test Plan

This document outlines the test plan for the enhanced GlobalCoyn blockchain implementation. The purpose is to ensure all components work correctly before deployment to the server.

## Prerequisites

- Python 3.8+
- Flask and other dependencies installed
- curl or Postman for API testing
- Multiple terminal sessions for running nodes

## Local Testing Setup

1. Start at least two node instances:
   ```bash
   # Terminal 1 - Start node 1
   cd /path/to/blockchain/nodes/node_template
   GCN_NODE_NUM=1 GCN_P2P_PORT=9000 GCN_WEB_PORT=8001 ./start_node.sh

   # Terminal 2 - Start node 2
   cd /path/to/blockchain/nodes/node_template
   GCN_NODE_NUM=2 GCN_P2P_PORT=9001 GCN_WEB_PORT=8002 ./start_node.sh
   ```

2. Allow nodes to connect and synchronize

## Test Cases

### 1. Blockchain Functionality Tests

| Test Description | Method | Endpoint | Expected Outcome |
|------------------|--------|----------|------------------|
| Get blockchain info | GET | `http://localhost:8001/api/blockchain` | Status 200, chain length, difficulty info |
| Get full chain | GET | `http://localhost:8001/api/blockchain/chain` | Status 200, array of blocks |
| Get latest block | GET | `http://localhost:8001/api/blockchain/blocks/latest` | Status 200, latest block details |
| Get block by height | GET | `http://localhost:8001/api/blockchain/blocks/0` | Status 200, genesis block details |
| Get blockchain stats | GET | `http://localhost:8001/api/blockchain/stats` | Status 200, statistics data |
| Get mining difficulty | GET | `http://localhost:8001/api/blockchain/difficulty` | Status 200, difficulty details |
| Mine a block | POST | `http://localhost:8001/api/blockchain/blocks/mine` with body `{"miner_address":"GCN_TEST_ADDRESS"}` | Status 201, new block details |
| Get mempool state | GET | `http://localhost:8001/api/blockchain/mempool` | Status 200, list of pending transactions |

### 2. Wallet Functionality Tests

| Test Description | Method | Endpoint | Expected Outcome |
|------------------|--------|----------|------------------|
| Create a wallet | POST | `http://localhost:8001/api/wallet/create` | Status 201, new address |
| Generate seed phrase | GET | `http://localhost:8001/api/wallet/generate-seed` | Status 200, seed phrase |
| Import wallet from seed | POST | `http://localhost:8001/api/wallet/import/seed` with body `{"seed_phrase":"..."}` | Status 200, imported address |
| Import wallet from key | POST | `http://localhost:8001/api/wallet/import/key` with body `{"private_key":"..."}` | Status 200, imported address |
| List all wallets | GET | `http://localhost:8001/api/wallet/list` | Status 200, list of addresses |
| Get wallet balance | GET | `http://localhost:8001/api/wallet/balance/{ADDRESS}` | Status 200, balance info |
| Get wallet transactions | GET | `http://localhost:8001/api/wallet/transactions/{ADDRESS}` | Status 200, list of transactions |
| Get transaction fee estimate | GET | `http://localhost:8001/api/wallet/fee-estimate` | Status 200, fee estimates |
| Sign a transaction | POST | `http://localhost:8001/api/wallet/sign-transaction` with transaction data | Status 200, signed transaction |
| Validate wallet address | GET | `http://localhost:8001/api/wallet/validate/{ADDRESS}` | Status 200, validation result |
| Get mining stats | GET | `http://localhost:8001/api/wallet/mining-stats/{ADDRESS}` | Status 200, mining statistics |
| Delete wallet | DELETE | `http://localhost:8001/api/wallet/delete` with body `{"address":"..."}` | Status 200, deletion confirmation |

### 3. Transaction Functionality Tests

| Test Description | Method | Endpoint | Expected Outcome |
|------------------|--------|----------|------------------|
| Create and submit transaction | POST | `http://localhost:8001/api/transactions` with transaction data | Status 201, transaction details |
| Get transaction details | GET | `http://localhost:8001/api/transactions/{TX_HASH}` | Status 200, transaction details |
| Get mempool transactions | GET | `http://localhost:8001/api/transactions/mempool` | Status 200, mempool transactions |
| Verify transaction | GET | `http://localhost:8001/api/transactions/verify/{TX_HASH}` | Status 200, verification result |
| Get recommended fees | GET | `http://localhost:8001/api/transactions/fees` | Status 200, fee recommendations |
| Get transaction history | GET | `http://localhost:8001/api/transactions/history` | Status 200, transaction history |

### 4. Network Functionality Tests

| Test Description | Method | Endpoint | Expected Outcome |
|------------------|--------|----------|------------------|
| Get network status | GET | `http://localhost:8001/api/network/status` | Status 200, network status |
| Get connected peers | GET | `http://localhost:8001/api/network/peers` | Status 200, peer list |
| Synchronize with network | POST | `http://localhost:8001/api/network/sync` | Status 200, sync results |
| Connect to peer | POST | `http://localhost:8001/api/network/connect` with body `{"address":"localhost","port":9001}` | Status 200, connection result |
| Get known nodes | GET | `http://localhost:8001/api/network/nodes` | Status 200, node list |
| Get network stats | GET | `http://localhost:8001/api/network/stats` | Status 200, network statistics |

### 5. Mining Functionality Tests

| Test Description | Method | Endpoint | Expected Outcome |
|------------------|--------|----------|------------------|
| Start mining | POST | `http://localhost:8001/api/mining/start` with body `{"mining_address":"..."}` | Status 200, mining started |
| Stop mining | POST | `http://localhost:8001/api/mining/stop` | Status 200, mining stopped |
| Get mining status | GET | `http://localhost:8001/api/mining/status` | Status 200, mining status |
| Get hashrate | GET | `http://localhost:8001/api/mining/hashrate` | Status 200, hashrate info |
| Get mining rewards | GET | `http://localhost:8001/api/mining/rewards` | Status 200, reward info |

## Integration Tests

### Node Synchronization Test
1. Start two nodes
2. Mine several blocks on node 1
3. Verify node 2 synchronizes and has the same blockchain height

### Transaction Propagation Test
1. Start two nodes
2. Create a wallet on node 1
3. Mine some blocks to get coins
4. Send a transaction from node 1
5. Verify transaction appears in mempool of node 2

### Mining Reward Test
1. Start a node
2. Create a wallet
3. Start mining to that wallet address
4. Wait for a block to be mined
5. Verify wallet balance increases

## Performance Tests

1. Create a script to send multiple transactions simultaneously
2. Measure transaction processing time
3. Measure block creation time
4. Assess memory usage during operation

## Full End-to-End Workflow Test

1. Start multiple nodes
2. Create wallets on all nodes
3. Mine blocks to generate coins
4. Send transactions between nodes
5. Verify all transactions are processed and included in blocks
6. Verify all nodes have synchronized to the same blockchain state

## Deployment Readiness Checklist

- [ ] All API endpoints return expected responses
- [ ] Nodes successfully connect to each other
- [ ] Blockchain synchronization works correctly
- [ ] Transaction creation and propagation work as expected
- [ ] Mining process works correctly
- [ ] All database operations function properly
- [ ] No price oracle or market dependencies remain
- [ ] System performs acceptably under load
- [ ] Error handling is robust
- [ ] Logging is comprehensive

## Test Automation

Create test scripts for automated API testing using curl or Python requests:

```bash
#!/bin/bash
# Example automated test script

# Test blockchain info endpoint
echo "Testing blockchain info endpoint..."
curl -s http://localhost:8001/api/blockchain | jq

# Test wallet creation
echo "Testing wallet creation..."
WALLET_RESPONSE=$(curl -s -X POST http://localhost:8001/api/wallet/create)
ADDRESS=$(echo $WALLET_RESPONSE | jq -r '.address')
echo "Created wallet: $ADDRESS"

# Test transaction creation
echo "Testing transaction creation..."
# [Additional commands here]
```

## Test Reporting

Document test results including:
- Endpoint tested
- Request made
- Response received
- Pass/fail status
- Any errors or issues encountered