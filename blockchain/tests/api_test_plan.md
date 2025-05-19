# API Test Plan for GlobalCoyn Blockchain

This document outlines a comprehensive test plan for the GlobalCoyn blockchain API, focusing on ensuring all endpoints function correctly before deployment.

## Test Environment Setup

1. Create a dedicated test directory with a clean blockchain instance
2. Initialize the blockchain with a genesis block
3. Create test wallets for transaction testing
4. Set up a local Flask server running the API

## Wallet API Tests

### 1. Wallet Creation Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_create_wallet` | Create a new wallet | Status 201, returns wallet address |
| `test_create_wallet_twice` | Create two wallets consecutively | Both operations succeed with different addresses |
| `test_generate_seed` | Generate a new seed phrase | Returns a valid 12-word BIP-39 seed phrase |

### 2. Wallet Import Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_import_seed_phrase` | Import a wallet using a valid seed phrase | Status 200, returns wallet address |
| `test_import_invalid_seed` | Import a wallet with invalid seed phrase | Status 400, error message |
| `test_import_private_key` | Import a wallet using a valid private key | Status 200, returns wallet address |
| `test_import_invalid_key` | Import a wallet with invalid private key | Status 400, error message |

### 3. Wallet Information Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_list_wallets` | List all wallets | Returns array of wallet addresses |
| `test_get_balance_existing` | Get balance for existing wallet | Status 200, returns correct balance |
| `test_get_balance_nonexistent` | Get balance for non-existent wallet | Status 404, error message |
| `test_export_private_key` | Export private key for a wallet | Status 200, returns WIF-formatted private key |
| `test_export_invalid_wallet` | Export key for invalid wallet | Status 404, error message |

### 4. Transaction Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_get_transactions_empty` | Get transactions for new wallet | Status 200, empty array |
| `test_sign_transaction` | Sign a transaction using wallet | Status 200, returns signed transaction |
| `test_sign_invalid_wallet` | Sign with non-existent wallet | Status 404, error message |
| `test_sign_insufficient_funds` | Sign with insufficient balance | Status 400, error message |
| `test_get_fee_estimate` | Get transaction fee estimate | Status 200, returns fee estimate |

## Blockchain API Tests

### 1. Blockchain Information Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_get_blockchain_info` | Get general blockchain info | Status 200, chain info including length |
| `test_get_chain` | Get the full blockchain | Status 200, array of blocks |
| `test_get_latest_block` | Get the most recent block | Status 200, block data |
| `test_get_block_by_hash` | Get block by valid hash | Status 200, block data |
| `test_get_block_invalid_hash` | Get block by invalid hash | Status 404, error message |

### 2. Mining Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_mine_block` | Mine a new block | Status 200, new block added |
| `test_mine_block_with_transactions` | Mine block with pending transactions | Status 200, transactions included in block |

## Transaction API Tests

### 1. Transaction Management Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_get_mempool` | Get current mempool transactions | Status 200, array of transactions |
| `test_create_transaction` | Create and add transaction to mempool | Status 201, transaction added |
| `test_create_invalid_transaction` | Create transaction with missing fields | Status 400, error message |
| `test_create_double_spend` | Create transaction spending same coins twice | Second transaction fails |

## Network API Tests

### 1. Network Information Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_get_network_status` | Get network status | Status 200, network information |
| `test_get_peers` | Get list of connected peers | Status 200, array of peers |

## Integration Tests

### 1. End-to-End Workflow Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_create_wallet_and_mine` | Create wallet, mine block, check balance | Wallet created, block mined, balance updated |
| `test_create_wallets_and_transfer` | Create two wallets, transfer between them | Transfer succeeds, balances updated correctly |
| `test_blockchain_persistence` | Restart server and check if blockchain persists | Blockchain state maintained after restart |

## Performance Tests

### 1. Load Testing

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_concurrent_requests` | Send multiple concurrent API requests | All requests handled successfully |
| `test_large_chain` | Test with a blockchain containing many blocks | API remains responsive |

## Test Implementation

For each test category, we'll create a separate Python test script that uses the `requests` library to interact with the API. Each test will:

1. Make the appropriate API call
2. Verify the response status code
3. Validate the response data structure
4. Check that the operation had the expected effect

Example test implementation:

```python
import requests
import unittest

class WalletAPITests(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://localhost:5000/api"
        
    def test_create_wallet(self):
        response = requests.post(f"{self.base_url}/wallet/create")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("address", data)
        # Additional validation of address format
```

## Test Execution

1. Start the API server in test mode
2. Run the test suite
3. Record any failures and fix implementation issues
4. Re-run tests until all pass
5. Perform manual verification of key workflows

## Deployment Readiness Checklist

- [ ] All API endpoint tests pass
- [ ] Integration tests pass
- [ ] Performance tests show acceptable response times
- [ ] Error handling verified for all endpoints
- [ ] Data persistence verified across server restarts
- [ ] CORS headers properly configured for web access
- [ ] API documentation matches implementation