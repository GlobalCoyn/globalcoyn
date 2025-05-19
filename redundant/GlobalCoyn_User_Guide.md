# GlobalCoyn Wallet - User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Wallet Features](#wallet-features)
5. [Mining GCN](#mining-gcn)
6. [Node Management](#node-management)
7. [Blockchain Explorer](#blockchain-explorer)
8. [Network Statistics](#network-statistics)
9. [Settings & Configuration](#settings--configuration)
10. [Troubleshooting](#troubleshooting)
11. [Frequently Asked Questions](#frequently-asked-questions)

## Introduction

GlobalCoyn (GCN) is a decentralized cryptocurrency designed to provide a secure, efficient, and user-friendly digital currency solution. This wallet application allows you to:

- Send and receive GCN
- Mine new GCN coins
- View detailed blockchain information
- Monitor network statistics
- Run a node to support the network

The GlobalCoyn Wallet for macOS provides a complete blockchain node and wallet interface in one easy-to-use application.

## Installation

### System Requirements

- macOS 10.14 (Mojave) or newer
- At least 500 MB of free disk space
- Internet connection for blockchain synchronization

### Installation Steps

1. **Download the Installer**
   - Download the GlobalCoyn DMG file from the official website (globalcoyn.com)

2. **Open the Installer**
   - Double-click the downloaded DMG file to mount it
   - A window will appear showing the GlobalCoyn application and Applications folder

3. **Install the Application**
   - Drag the GlobalCoyn app icon to the Applications folder
   - This will copy the application to your Applications directory

4. **Security Verification**
   - When you first launch the application, macOS may display a security warning
   - This happens because the app is downloaded from the internet
   - To allow the app to run, go to System Preferences > Security & Privacy and click "Open Anyway"

5. **First Launch Setup**
   - The first time you launch the application, it will set up your data directory at `~/Documents/GlobalCoyn/`
   - It will also check for and install any required dependencies

## Getting Started

### Creating a New Wallet

When you first launch GlobalCoyn, you can create a new wallet:

1. From the main screen, select "Wallet" in the sidebar
2. Click "Create New Wallet"
3. Choose a strong password to encrypt your wallet
4. Record your wallet recovery phrase in a secure location
5. Click "Create Wallet"

Your wallet will be created and stored in your GlobalCoyn data directory. A wallet backup will also be saved.

### Importing an Existing Wallet

If you already have a GlobalCoyn wallet:

1. From the main screen, select "Wallet" in the sidebar
2. Click "Import Wallet"
3. Choose either:
   - Import from recovery phrase
   - Import from wallet.key file
4. Follow the prompts to complete the import process

### Viewing Your Wallet

The Wallet screen shows:

- Your current balance
- Your wallet address
- Recent transactions
- A QR code for receiving payments

## Wallet Features

### Sending GCN

To send GCN to another address:

1. Go to the "Wallet" section
2. Click "Send"
3. Enter the recipient's wallet address
4. Enter the amount to send
5. Click "Review Transaction"
6. Confirm the details and click "Send"

### Receiving GCN

To receive GCN:

1. Go to the "Wallet" section
2. Click "Receive"
3. Your wallet address and QR code will be displayed
4. Share your address with the sender
5. You can also click "Copy Address" to copy your wallet address to the clipboard

### Transaction History

The wallet displays your transaction history, showing:

- Transaction type (send/receive)
- Date and time
- Amount
- Status (pending, confirmed)
- Transaction ID

Click on any transaction to view more details.

## Mining GCN

GlobalCoyn uses a proof-of-work consensus mechanism. You can mine GCN directly from the wallet:

1. Go to the "Mining" section in the sidebar
2. Click "Start Mining"
3. Choose mining settings:
   - Number of threads
   - Mining intensity (affects CPU usage)
4. Click "Start" to begin mining

The mining screen will show:

- Current hashrate
- Mining difficulty
- Estimated time to find a block
- Mining rewards history

Mining will continue in the background even if you navigate to other sections of the app.

## Node Management

The GlobalCoyn wallet includes a full blockchain node. You can manage it from the "Node" section:

### Node Status

The Node Status screen shows:

- Connection status
- Number of connected peers
- Blockchain height
- Synchronization status
- Node uptime

### Node Configuration

You can configure your node:

1. Go to "Node" > "Settings"
2. Adjust settings such as:
   - P2P port (default: 9000 + node number)
   - Web port (default: 8000 + node number)
   - Max connections
   - Sync frequency
3. Click "Save Changes" to apply

### Node Logs

To view the node logs:

1. Go to "Node" > "Logs"
2. The log viewer shows recent node activity
3. Use the filter options to find specific events
4. Click "Export Logs" to save logs to a file

## Blockchain Explorer

The built-in blockchain explorer allows you to browse the GlobalCoyn blockchain:

### Viewing Blocks

To view blocks:

1. Go to the "Explorer" section
2. Blocks are displayed in a paginated list, newest first
3. Click on any block to view its details:
   - Block hash
   - Previous block hash
   - Timestamp
   - Miner address
   - Transactions

### Searching

You can search for specific items:

1. Use the search bar at the top of the Explorer
2. You can search by:
   - Block hash
   - Transaction ID
   - Wallet address

### Transaction Details

When viewing a transaction, you'll see:

- Sender address
- Recipient address
- Amount
- Fee
- Timestamp
- Block confirmation details

## Network Statistics

The "Network" section provides statistics about the GlobalCoyn network:

- Total nodes online
- Network hashrate
- Current difficulty
- Block time (average time between blocks)
- Total GCN in circulation
- Network uptime

These statistics update automatically every few minutes.

## Settings & Configuration

### Application Settings

In the "Settings" section, you can configure:

- Application theme (light/dark)
- Currency display (GCN units)
- Update frequency
- Startup options
- Notification settings

### Wallet Settings

Wallet-specific settings include:

- Password change
- Wallet backup
- Recovery phrase viewing (requires password)
- Transaction fee settings

### Advanced Settings

Advanced options include:

- Blockchain data location
- Bootstrap node configuration
- Log verbosity
- Reset options

## Troubleshooting

### Common Issues

**Application Won't Start**

If the application won't start:

1. Check if Python is installed on your system
2. Make sure you have internet connectivity
3. Look for errors in the log file at `~/Library/Logs/GlobalCoyn/globalcoyn_app.log`
4. Try reinstalling the application

**Node Connection Issues**

If your node won't connect to the network:

1. Check your internet connection
2. Verify that your router allows the P2P port (default range: 9000-9999)
3. Try restarting the node from the Node menu
4. Check the node logs for specific error messages

**Wallet Not Syncing**

If your wallet balance is not updating:

1. Make sure your node is fully synchronized
2. Check that your wallet is properly unlocked
3. Try rebuilding the wallet index from Settings > Advanced > Rebuild Wallet Index

### Log Files

Log files are stored in `~/Library/Logs/GlobalCoyn/`:

- `globalcoyn_app.log` - Main application log
- `node_startup.log` - Node startup log
- `node_sync.log` - Blockchain synchronization log
- `blockchain.log` - Blockchain operation log

### Reporting Issues

If you encounter issues that you can't resolve:

1. Export your logs from the Help menu
2. Visit globalcoyn.com/support
3. Submit a detailed description of your issue along with the logs

## Frequently Asked Questions

**Q: How long does it take to sync the blockchain?**

A: Initial synchronization may take 15-30 minutes depending on your internet connection and the current blockchain size.

**Q: Is my wallet encrypted?**

A: Yes, your wallet file is encrypted with your password. Make sure to keep your password and recovery phrase secure.

**Q: How often should I back up my wallet?**

A: The application automatically backs up your wallet when significant changes occur. However, it's good practice to manually back up your wallet after receiving large amounts or creating new addresses.

**Q: Can I run multiple nodes on one computer?**

A: The application is designed to run one node per installation. For advanced users who want to run multiple nodes, separate installations in different directories are recommended.

**Q: How do I update the application?**

A: The application checks for updates automatically. When an update is available, you'll be notified within the app. Simply follow the prompts to download and install the update.

**Q: What if I forget my wallet password?**

A: If you forget your wallet password, you can recover your wallet using the recovery phrase you saved when creating the wallet. Without the recovery phrase, your funds may be inaccessible.

---

Thank you for using GlobalCoyn Wallet! For more information and resources, visit [globalcoyn.com](https://globalcoyn.com).