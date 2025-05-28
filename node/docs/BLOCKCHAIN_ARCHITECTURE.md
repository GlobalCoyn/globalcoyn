# GlobalCoyn Blockchain Architecture

This document provides an overview of the GlobalCoyn blockchain architecture, explaining its core components and how they interact.

## Overview

GlobalCoyn is a proof-of-work blockchain that implements a decentralized ledger for recording transactions. The architecture consists of several key components:

1. **Blockchain Core**: The foundation of the system that handles blocks, transactions, and consensus.
2. **Network Layer**: Responsible for peer-to-peer communication and node synchronization.
3. **API Layer**: Provides a RESTful interface for interacting with the blockchain.
4. **Wallet System**: Manages cryptographic keys and user balances.
5. **Price Oracle**: Provides pricing information for GlobalCoyn.

## Blockchain Core

The blockchain core is implemented in `blockchain.py` and consists of:

### Block Structure

Each block in the GlobalCoyn blockchain contains:

- Block header:
  - Index: Position of the block in the chain
  - Previous Hash: Hash of the previous block
  - Timestamp: When the block was created
  - Nonce: Value used for proof-of-work
  - Difficulty Bits: Current mining difficulty
- Block body:
  - Transactions: List of transactions in the block

### Transaction Structure

Each transaction contains:

- Sender: Address of the sender
- Recipient: Address of the recipient
- Amount: Amount of GlobalCoyn to transfer
- Fee: Transaction fee for miners
- Timestamp: When the transaction was created
- Signature: Cryptographic signature of the transaction
- Transaction Type: TRANSFER, PURCHASE, SELL, etc.

### Consensus Mechanism

GlobalCoyn uses a Bitcoin-inspired proof-of-work consensus mechanism:

1. Miners collect transactions from the mempool
2. Miners create a candidate block with these transactions
3. Miners attempt to find a valid nonce that produces a hash below the target difficulty
4. The first miner to find a valid hash broadcasts the block to the network
5. Other nodes verify the block and add it to their local chains
6. The difficulty is adjusted periodically to maintain consistent block times

## Network Layer

The network layer handles peer-to-peer communication between nodes:

### Node Discovery

Nodes connect to each other using:

1. Seed nodes: Predefined nodes used for bootstrapping
2. Peer exchange: Nodes share their known peers with each other

### Synchronization

When a node joins the network or after being offline, it synchronizes with other nodes by:

1. Comparing chain lengths
2. Requesting blocks from peers with longer chains
3. Validating received blocks
4. Replacing the local chain if a valid longer chain is found

The improved synchronization (`improved_node_sync.py`) optimizes this process for large chains.

## API Layer

The API layer provides RESTful endpoints for interacting with the blockchain:

### Endpoints

- `/api/blockchain`: Get blockchain status
- `/api/chain`: Get the full blockchain
- `/api/mempool`: Get pending transactions
- `/api/balance/<address>`: Get balance for a wallet address
- `/api/transaction`: Add a transaction to the mempool
- `/api/mine`: Mine a new block
- `/api/mine_async`: Asynchronous mining
- `/api/network/*`: Network status and management

## Wallet System

The wallet system (`wallet.py`) manages cryptographic keys and transactions:

1. Key generation: Creates public/private key pairs
2. Address generation: Converts public keys into addresses
3. Transaction signing: Signs transactions with private keys
4. Balance management: Tracks wallet balances
5. History tracking: Records transaction history

## Price Oracle

The price oracle (`price_oracle.py`) provides pricing information for GlobalCoyn:

1. External price data: Retrieves price data from external sources
2. Price aggregation: Combines data from multiple sources for accuracy
3. Price caching: Caches prices to reduce external API calls
4. Historical data: Maintains historical price records

## Data Flow

1. User creates a transaction using the wallet
2. Transaction is signed and broadcast to the network
3. Nodes validate the transaction and add it to their mempools
4. Miners select transactions from the mempool and create blocks
5. Successful miners broadcast new blocks to the network
6. Nodes validate and add the blocks to their chains
7. Wallets update balances based on the updated blockchain

## Optimization Techniques

GlobalCoyn implements several optimizations:

1. Indexed block storage for fast lookups
2. Mempool transaction sorting by fee for optimal mining rewards
3. Asynchronous mining to prevent UI lockups
4. Incremental chain downloading for efficient syncing
5. Merkle trees for efficient transaction verification

## Security Measures

1. Cryptographic signatures for transaction authentication
2. Proof-of-work for consensus security
3. Chain validation rules to prevent invalid blocks
4. Transaction validation to prevent double-spending
5. Difficulty adjustment to maintain security as network hash power changes

## Future Enhancements

1. Smart contract functionality
2. Lightning network for faster transactions
3. Enhanced privacy features
4. Improved scalability solutions
5. Cross-chain compatibility