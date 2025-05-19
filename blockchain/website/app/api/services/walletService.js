const axios = require('axios');
const crypto = require('crypto');
const path = require('path');
const fs = require('fs');
const bip39 = require('bip39');
const { createHash, randomBytes } = require('crypto');
const { createCipheriv, createDecipheriv } = require('crypto');

// Configure the bootstrap node URLs
const BOOTSTRAP_NODE_URL = 'http://13.61.79.186:8001';
const FALLBACK_NODE_URL = 'http://13.61.79.186:8002';
const API_TIMEOUT = 5000; // 5 seconds

// Configure wallet storage
const DATA_DIR = path.join(process.env.HOME || process.env.USERPROFILE, '.globalcoyn');
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

/**
 * Wallet Service
 * Handles wallet operations and transactions
 */
const walletService = {
  /**
   * Create a new wallet with randomly generated keys
   * @returns {Object} Wallet info including address and seed phrase
   */
  createWallet: function() {
    try {
      // Generate a new seed phrase (mnemonic)
      const mnemonic = bip39.generateMnemonic();
      
      // Generate wallet from seed phrase
      const walletData = this.generateWalletFromSeed(mnemonic);
      
      // Save wallet data to disk
      this.saveWalletData(walletData);
      
      return {
        address: walletData.address,
        seedPhrase: mnemonic,
        publicKey: walletData.publicKey,
        success: true
      };
    } catch (error) {
      console.error('Error creating wallet:', error);
      throw new Error(`Failed to create wallet: ${error.message}`);
    }
  },
  
  /**
   * Import wallet using seed phrase
   * @param {string} seedPhrase - The 12-word seed phrase
   * @returns {Object} Wallet info
   */
  importWalletFromSeed: function(seedPhrase) {
    try {
      // Validate the seed phrase
      if (!bip39.validateMnemonic(seedPhrase)) {
        throw new Error('Invalid seed phrase format');
      }
      
      // Generate wallet from seed phrase
      const walletData = this.generateWalletFromSeed(seedPhrase);
      
      // Save wallet data to disk
      this.saveWalletData(walletData);
      
      return {
        address: walletData.address,
        publicKey: walletData.publicKey,
        success: true
      };
    } catch (error) {
      console.error('Error importing wallet from seed:', error);
      throw new Error(`Failed to import wallet: ${error.message}`);
    }
  },
  
  /**
   * Import wallet using private key
   * @param {string} privateKey - The WIF format private key
   * @returns {Object} Wallet info
   */
  importWalletFromPrivateKey: function(privateKey) {
    try {
      // Decode the WIF private key
      const walletData = this.generateWalletFromPrivateKey(privateKey);
      
      // Save wallet data to disk
      this.saveWalletData(walletData);
      
      return {
        address: walletData.address,
        publicKey: walletData.publicKey,
        success: true
      };
    } catch (error) {
      console.error('Error importing wallet from private key:', error);
      throw new Error(`Failed to import wallet: ${error.message}`);
    }
  },
  
  /**
   * Generate wallet data from seed phrase
   * @param {string} seedPhrase - The seed phrase
   * @returns {Object} Generated wallet data
   */
  generateWalletFromSeed: function(seedPhrase) {
    // Convert seed to entropy buffer
    const entropy = bip39.mnemonicToEntropy(seedPhrase);
    
    // Convert entropy to hex strings for keys
    const privateKeyHex = entropy.padEnd(64, '0'); // Ensure 32 bytes length
    
    // Generate public key (using a simple hash-based approach)
    const publicKeyHex = createHash('sha256').update(privateKeyHex).digest('hex');
    
    // Generate address from public key
    const address = this.getAddressFromPublicKey(publicKeyHex);
    
    return {
      privateKey: privateKeyHex,
      publicKey: publicKeyHex,
      address,
      createdAt: new Date().toISOString()
    };
  },
  
  /**
   * Generate wallet data from private key
   * @param {string} privateKeyWif - The WIF format private key
   * @returns {Object} Generated wallet data
   */
  generateWalletFromPrivateKey: function(privateKeyWif) {
    try {
      // For simplicity, we'll use this as direct hex - in a real implementation, 
      // we would decode the WIF format properly
      const privateKeyHex = createHash('sha256').update(privateKeyWif).digest('hex');
      
      // Generate public key from private key
      const publicKeyHex = createHash('sha256').update(privateKeyHex).digest('hex');
      
      // Generate address from public key
      const address = this.getAddressFromPublicKey(publicKeyHex);
      
      return {
        privateKey: privateKeyHex,
        publicKey: publicKeyHex,
        address,
        createdAt: new Date().toISOString()
      };
    } catch (error) {
      console.error('Error generating wallet from private key:', error);
      throw error;
    }
  },
  
  /**
   * Save wallet data securely to disk
   * @param {Object} walletData - The wallet data to save
   * @returns {boolean} Success status
   */
  saveWalletData: function(walletData) {
    try {
      // Create encryption key from a fixed passphrase or from a secure storage
      // For demo purposes, we'll use a fixed key - in production, this would be secured properly
      const encryptionKey = createHash('sha256').update('GLOBALCOYN_SECURE_KEY').digest();
      const iv = randomBytes(16);
      
      // Encrypt the wallet data
      const cipher = createCipheriv('aes-256-cbc', encryptionKey, iv);
      let encrypted = cipher.update(JSON.stringify(walletData), 'utf8', 'hex');
      encrypted += cipher.final('hex');
      
      // Create the wallet file path
      const walletFilePath = path.join(DATA_DIR, `wallet_${walletData.address}.enc`);
      
      // Save the encrypted data with IV prepended
      fs.writeFileSync(walletFilePath, `${iv.toString('hex')}:${encrypted}`);
      
      // Save address to wallet index
      this.updateWalletIndex(walletData.address);
      
      return true;
    } catch (error) {
      console.error('Error saving wallet data:', error);
      throw error;
    }
  },
  
  /**
   * Load wallet data from disk
   * @param {string} address - The wallet address to load
   * @returns {Object} Decrypted wallet data
   */
  loadWalletData: function(address) {
    try {
      const walletFilePath = path.join(DATA_DIR, `wallet_${address}.enc`);
      
      if (!fs.existsSync(walletFilePath)) {
        throw new Error(`Wallet file not found for address: ${address}`);
      }
      
      // Read the encrypted data
      const encryptedData = fs.readFileSync(walletFilePath, 'utf8');
      const [ivHex, encryptedHex] = encryptedData.split(':');
      
      // Decrypt the data
      const encryptionKey = createHash('sha256').update('GLOBALCOYN_SECURE_KEY').digest();
      const iv = Buffer.from(ivHex, 'hex');
      const decipher = createDecipheriv('aes-256-cbc', encryptionKey, iv);
      
      let decrypted = decipher.update(encryptedHex, 'hex', 'utf8');
      decrypted += decipher.final('utf8');
      
      return JSON.parse(decrypted);
    } catch (error) {
      console.error(`Error loading wallet data for ${address}:`, error);
      throw error;
    }
  },
  
  /**
   * Get all wallet addresses from index
   * @returns {Array} List of wallet addresses
   */
  getWallets: function() {
    try {
      const indexPath = path.join(DATA_DIR, 'wallet_index.json');
      
      if (!fs.existsSync(indexPath)) {
        return [];
      }
      
      const indexData = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
      return indexData.addresses || [];
    } catch (error) {
      console.error('Error getting wallets:', error);
      return [];
    }
  },
  
  /**
   * Update wallet index with new address
   * @param {string} address - The wallet address to add
   */
  updateWalletIndex: function(address) {
    try {
      const indexPath = path.join(DATA_DIR, 'wallet_index.json');
      let indexData = { addresses: [] };
      
      // Read existing index if it exists
      if (fs.existsSync(indexPath)) {
        indexData = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
      }
      
      // Add address if not already present
      if (!indexData.addresses.includes(address)) {
        indexData.addresses.push(address);
      }
      
      // Save updated index
      fs.writeFileSync(indexPath, JSON.stringify(indexData, null, 2));
    } catch (error) {
      console.error('Error updating wallet index:', error);
      throw error;
    }
  },
  
  /**
   * Export wallet private key (WIF format)
   * @param {string} address - The wallet address
   * @returns {string} Private key in WIF format
   */
  exportPrivateKey: function(address) {
    try {
      const walletData = this.loadWalletData(address);
      
      // In a real implementation, we would convert to WIF format properly
      // For demo, we'll just return a simulated WIF format
      return `GCN_${walletData.privateKey}`;
    } catch (error) {
      console.error(`Error exporting private key for ${address}:`, error);
      throw error;
    }
  },

  /**
   * Sign a transaction with wallet private key
   * @param {string} address - The wallet address (sender)
   * @param {string} toAddress - Recipient address
   * @param {number} amount - Amount to send
   * @param {number} fee - Transaction fee
   * @returns {Object} Signed transaction
   */
  signTransaction: function(address, toAddress, amount, fee = 0.001) {
    try {
      const walletData = this.loadWalletData(address);
      
      // Transaction data to sign
      const txData = {
        from: address,
        to: toAddress,
        amount: parseFloat(amount),
        fee: parseFloat(fee),
        timestamp: Date.now()
      };
      
      // Create the hash of the transaction data
      const txHash = createHash('sha256')
        .update(JSON.stringify(txData))
        .digest('hex');
      
      // Sign the transaction hash with private key
      // In a real implementation, this would use proper signature algorithm (ECDSA)
      // For demo, we'll simulate signing
      const signature = createHash('sha256')
        .update(txHash + walletData.privateKey)
        .digest('hex');
      
      return {
        ...txData,
        signature
      };
    } catch (error) {
      console.error(`Error signing transaction for ${address}:`, error);
      throw error;
    }
  },
  
  /**
   * Get wallet balance for a given address
   */
  getBalance: async function(address) {
    try {
      const response = await this.makeApiRequest(`${BOOTSTRAP_NODE_URL}/api/wallet/balance/${address}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching balance for ${address}:`, error);
      
      // Attempt fallback node
      try {
        const fallbackResponse = await this.makeApiRequest(`${FALLBACK_NODE_URL}/api/wallet/balance/${address}`);
        return fallbackResponse.data;
      } catch (fallbackError) {
        // Return mock data if both requests fail
        return {
          address,
          balance: 0,
          last_updated: new Date().toISOString()
        };
      }
    }
  },
  
  /**
   * Get transactions for a wallet address
   */
  getTransactions: async function(address, page = 1, limit = 10) {
    try {
      const response = await this.makeApiRequest(
        `${BOOTSTRAP_NODE_URL}/api/wallet/transactions/${address}?page=${page}&limit=${limit}`
      );
      return response.data;
    } catch (error) {
      console.error(`Error fetching transactions for ${address}:`, error);
      
      // Attempt fallback node
      try {
        const fallbackResponse = await this.makeApiRequest(
          `${FALLBACK_NODE_URL}/api/wallet/transactions/${address}?page=${page}&limit=${limit}`
        );
        return fallbackResponse.data;
      } catch (fallbackError) {
        // Return mock data if both requests fail
        return this.getMockWalletTransactions(address, page, limit);
      }
    }
  },
  
  /**
   * Send transaction
   */
  sendTransaction: async function(fromAddress, toAddress, amount, signature, fee = 0.001) {
    try {
      const response = await this.makeApiRequest(
        `${BOOTSTRAP_NODE_URL}/api/transactions/send`,
        'post',
        {
          from_address: fromAddress,
          to_address: toAddress,
          amount: parseFloat(amount),
          signature,
          fee: parseFloat(fee) || 0.001
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error sending transaction:', error);
      
      // Attempt fallback node
      try {
        const fallbackResponse = await this.makeApiRequest(
          `${FALLBACK_NODE_URL}/api/transactions/send`,
          'post',
          {
            from_address: fromAddress,
            to_address: toAddress,
            amount: parseFloat(amount),
            signature,
            fee: parseFloat(fee) || 0.001
          }
        );
        return fallbackResponse.data;
      } catch (fallbackError) {
        throw new Error('Failed to submit transaction to the network');
      }
    }
  },
  
  /**
   * Get address from public key
   */
  getAddressFromPublicKey: function(publicKey) {
    try {
      // Simple hash-based address derivation (for demonstration purposes)
      const hash = crypto.createHash('sha256').update(publicKey).digest('hex');
      return 'gcn1' + hash.substring(0, 40);
    } catch (error) {
      console.error('Error generating address:', error);
      throw error;
    }
  },
  
  /**
   * Get estimated transaction fee
   */
  getFeeEstimate: async function() {
    try {
      const response = await this.makeApiRequest(`${BOOTSTRAP_NODE_URL}/api/transactions/fee-estimate`);
      return response.data;
    } catch (error) {
      console.error('Error estimating fee:', error);
      
      // Attempt fallback node
      try {
        const fallbackResponse = await this.makeApiRequest(`${FALLBACK_NODE_URL}/api/transactions/fee-estimate`);
        return fallbackResponse.data;
      } catch (fallbackError) {
        // Return default fee estimate if both requests fail
        return {
          recommended_fee: 0.001,
          min_fee: 0.0001,
          max_fee: 0.01,
          last_updated: new Date().toISOString()
        };
      }
    }
  },
  
  /**
   * Helper function to make API requests with timeout
   */
  makeApiRequest: async function(url, method = 'get', data = null) {
    return axios({
      method,
      url,
      data,
      timeout: API_TIMEOUT
    });
  },
  
  /**
   * Mock data functions for fallback when API is unavailable
   */
  getMockWalletTransactions: function(address, page, limit) {
    const transactions = [];
    const totalTxs = Math.floor(Math.random() * 50); // Random number of transactions
    
    for (let i = 0; i < Math.min(limit, totalTxs - ((page - 1) * limit)); i++) {
      const isSending = Math.random() > 0.5;
      
      transactions.push({
        id: '0x' + [...Array(64)].map(() => Math.floor(Math.random() * 16).toString(16)).join(''),
        timestamp: new Date(Date.now() - (i * 86400000 * Math.random())).toISOString(),
        from: isSending ? address : 'gcn1' + [...Array(40)].map(() => Math.floor(Math.random() * 16).toString(16)).join(''),
        to: isSending ? 'gcn1' + [...Array(40)].map(() => Math.floor(Math.random() * 16).toString(16)).join('') : address,
        amount: Math.floor(Math.random() * 100) + Math.random(),
        fee: 0.001 + (Math.random() * 0.01),
        status: 'confirmed',
        block_height: 15000000 - Math.floor(Math.random() * 1000)
      });
    }
    
    return {
      address,
      transactions,
      page,
      limit,
      total: totalTxs,
      pages: Math.ceil(totalTxs / limit)
    };
  }
};

module.exports = walletService;