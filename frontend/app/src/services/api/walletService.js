import axios from 'axios';

// Production or dev API URLs
const PROD_API_URL = 'https://globalcoyn.com/api';
const DEV_API_URL = 'http://localhost:8001/api';

// Environment detection
// 1. Check for explicit environment setting in localStorage (useful for testing)
// 2. Check for REACT_APP_ENV environment variable
// 3. Check domain name
const ENV_OVERRIDE = localStorage.getItem('gcn_environment');
const isProduction = ENV_OVERRIDE === 'production' || 
                    process.env.REACT_APP_ENV === 'production' || 
                    window.location.hostname === 'globalcoyn.com';

// Logging environment
console.log('GlobalCoyn API Environment:', isProduction ? 'PRODUCTION' : 'DEVELOPMENT');

// Primary API URL
// - Use environment override if set
// - Otherwise use environment variable if set
// - Otherwise use detected environment
const API_BASE_URL = ENV_OVERRIDE === 'development' ? DEV_API_URL :
                    ENV_OVERRIDE === 'production' ? PROD_API_URL :
                    process.env.REACT_APP_API_URL || 
                    (isProduction ? PROD_API_URL : DEV_API_URL);

// Fallback URLs - use the opposite environment for maximum availability
// If primary is production, fallback to dev, and vice versa
const PRIMARY_FALLBACK_URL = isProduction ? 'http://localhost:8001/api' : 'https://globalcoyn.com/api';
const SECONDARY_FALLBACK_URL = isProduction ? 'http://localhost:8002/api' : 'https://globalcoyn.com/api';

// The fallback URL to use when primary fails
const FALLBACK_API_URL = PRIMARY_FALLBACK_URL;

// Add CORS headers option to axios
const axiosConfig = {
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  withCredentials: false  // Important for CORS
};

// Log the configuration
console.log('API Configuration:', {
  primaryUrl: API_BASE_URL,
  fallbackUrl: FALLBACK_API_URL,
  environment: isProduction ? 'production' : 'development',
  override: ENV_OVERRIDE || 'none'
});

// Clear any existing local wallet data to avoid using outdated cached wallets
// This ensures we only use wallets created through the bootstrap node API
(function clearOutdatedWalletData() {
  try {
    // Find all wallet-related keys in localStorage
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && (
        key.startsWith('gcn_wallet_') || 
        key === 'gcn_wallets' || 
        key === 'gcn_current_wallet' || 
        key.startsWith('gcn_transactions_')
      )) {
        keysToRemove.push(key);
      }
    }
    
    // Remove the keys
    keysToRemove.forEach(key => localStorage.removeItem(key));
    
    console.log(`Cleared ${keysToRemove.length} outdated wallet cache items`);
  } catch (error) {
    console.warn('Error clearing outdated wallet data:', error);
  }
})();

/**
 * Wallet Service for Frontend
 * Handles interaction with the wallet API
 */
const walletService = {
  /**
   * Create a new wallet
   * @returns {Promise<Object>} Wallet info
   */
  createWallet: async function() {
    try {
      // Increase timeout for the bootstrap node which might be slower to respond
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timeout')), 10000)
      );
      
      try {
        // First generate a seed phrase
        const seedPromise = axios.get(`${API_BASE_URL}/wallet/generate-seed`);
        const seedResponse = await Promise.race([seedPromise, timeoutPromise]);
        
        console.log('API seed response:', seedResponse.data);
        
        let seedPhrase = "";
        // Updated to match the actual API response format
        if (seedResponse.data && seedResponse.data.seed_phrase) {
          seedPhrase = seedResponse.data.seed_phrase;
          console.log('Using seed_phrase format:', seedPhrase);
        } else if (seedResponse.data && seedResponse.data.seedPhrase) {
          // Fallback for older API format
          seedPhrase = seedResponse.data.seedPhrase;
          console.log('Using seedPhrase format:', seedPhrase);
        } else if (typeof seedResponse.data === 'string') {
          // Handle raw string response
          seedPhrase = seedResponse.data;
          console.log('Using raw string format:', seedPhrase);
        } else {
          console.error('Unexpected seed phrase response format:', seedResponse.data);
          throw new Error('Failed to generate seed phrase');
        }
        
        // Create a wallet using the wallet API
        // Use the correct parameter name: seed_phrase instead of seedPhrase
        const requestData = {
          seed_phrase: seedPhrase
        };
        
        // Create wallet with the seed phrase
        const responsePromise = axios.post(`${API_BASE_URL}/wallet/import/seed`, requestData);
        const response = await Promise.race([responsePromise, timeoutPromise]);
        
        // Handle both API response formats:
        // - New format: {"address":"18e5...", "message":"Wallet imported successfully", "status":"success"}
        // - Old format: {"success":true, "address":"..."}
        if (response.data) {
          let isValid = false;
          let address = null;
          
          // Check for new API format (status: success)
          if (response.data.status === "success" && response.data.address) {
            isValid = true;
            address = response.data.address;
          }
          // Check for old API format (success: true)
          else if (response.data.success === true && response.data.address) {
            isValid = true;
            address = response.data.address;
          }
          
          if (isValid && address) {
            // Store wallet address in local storage for tracking purposes only
            this.storeWalletAddress(address);
            
            console.log('Created wallet through bootstrap node:', address);
            
            return {
              address: address,
              seedPhrase: seedPhrase, // Return seedPhrase in standard format
              publicKey: response.data.publicKey || "Unknown",
              success: true
            };
          }
        }
        
        throw new Error('Invalid wallet data from API: ' + JSON.stringify(response.data));
      } catch (apiError) {
        console.error('Bootstrap node wallet creation failed:', apiError);
        
        // Try the fallback bootstrap node
        try {
          // First try to generate a seed phrase from the fallback node
          const fallbackSeedPromise = axios.get(`${FALLBACK_API_URL}/wallet/generate-seed`);
          const fallbackSeedResponse = await Promise.race([fallbackSeedPromise, timeoutPromise]);
          
          let seedPhrase = "";
          // Updated to match actual API response format
          if (fallbackSeedResponse.data && fallbackSeedResponse.data.seed_phrase) {
            seedPhrase = fallbackSeedResponse.data.seed_phrase;
          } else if (fallbackSeedResponse.data && fallbackSeedResponse.data.seedPhrase) {
            // Fallback for older API format
            seedPhrase = fallbackSeedResponse.data.seedPhrase;
          } else {
            throw new Error('Failed to generate seed phrase from fallback node');
          }
          
          // Create wallet with the seed phrase on the fallback node
          // Use the correct parameter name: seed_phrase instead of seedPhrase
          const requestData = {
            seed_phrase: seedPhrase
          };
          
          const fallbackPromise = axios.post(`${FALLBACK_API_URL}/wallet/import/seed`, requestData);
          const fallbackResponse = await Promise.race([fallbackPromise, timeoutPromise]);
          
          // Handle both API response formats for the fallback API
          if (fallbackResponse.data) {
            let isValid = false;
            let address = null;
            
            // Check for new API format (status: success)
            if (fallbackResponse.data.status === "success" && fallbackResponse.data.address) {
              isValid = true;
              address = fallbackResponse.data.address;
            }
            // Check for old API format (success: true)
            else if (fallbackResponse.data.success === true && fallbackResponse.data.address) {
              isValid = true;
              address = fallbackResponse.data.address;
            }
            
            if (isValid && address) {
              this.storeWalletAddress(address);
              
              console.log('Created wallet through fallback bootstrap node:', address);
              
              return {
                address: address,
                seedPhrase: seedPhrase,
                publicKey: fallbackResponse.data.publicKey || "Unknown",
                success: true
              };
            }
          }
          
          throw new Error('Invalid wallet data from fallback API');
        } catch (fallbackError) {
          console.error('Fallback bootstrap node wallet creation also failed:', fallbackError);
          throw new Error('Unable to create wallet on the blockchain. Please try again later.');
        }
      }
    } catch (error) {
      console.error('Complete wallet creation failure:', error);
      throw error;
    }
  },
  
  /**
   * Create a wallet locally in the browser 
   * This method is no longer used as we require wallets to be created on the blockchain
   * @private
   * @deprecated Use the blockchain API to create wallets
   */
  _createLocalWallet: function() {
    console.error('Local wallet creation is no longer supported. All wallets must be created via the blockchain API.');
    throw new Error('Local wallet creation is disabled. All wallets must be created via the blockchain API.');
  },
  
  /**
   * Import wallet using seed phrase
   * @param {string} seedPhrase - The 12-word seed phrase
   * @returns {Promise<Object>} Wallet info
   */
  importWalletFromSeed: async function(seedPhrase) {
    try {
      // Increase timeout for blockchain API
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timeout')), 10000)
      );
      
      try {
        // Validate seed phrase (basic check)
        const words = seedPhrase.split(' ');
        if (words.length !== 12) {
          throw new Error('Seed phrase must contain exactly 12 words');
        }
        
        // Use the wallet API to import the wallet
        // Use the correct parameter name: seed_phrase instead of seedPhrase
        const requestData = {
          seed_phrase: seedPhrase
        };
        
        // Make request to import the wallet
        const responsePromise = axios.post(`${API_BASE_URL}/wallet/import/seed`, requestData);
        const response = await Promise.race([responsePromise, timeoutPromise]);
        
        // Handle both API response formats
        if (response.data) {
          let isValid = false;
          let address = null;
          
          // Check for new API format (status: success)
          if (response.data.status === "success" && response.data.address) {
            isValid = true;
            address = response.data.address;
          }
          // Check for old API format (success: true)
          else if (response.data.success === true && response.data.address) {
            isValid = true;
            address = response.data.address;
          }
          
          if (isValid && address) {
            // Store reference to the address
            this.storeWalletAddress(address);
            
            console.log('Imported wallet from seed phrase:', address);
            
            return {
              address: address,
              publicKey: response.data.publicKey || "Unknown",
              success: true
            };
          }
        }
        
        throw new Error('Invalid wallet data from API: ' + JSON.stringify(response.data));
      } catch (apiError) {
        console.error('Bootstrap node seed import failed:', apiError);
        
        // Try the fallback bootstrap node
        try {
          // Use the correct parameter name: seed_phrase instead of seedPhrase
          const requestData = {
            seed_phrase: seedPhrase
          };
          
          const fallbackPromise = axios.post(`${FALLBACK_API_URL}/wallet/import/seed`, requestData);
          const fallbackResponse = await Promise.race([fallbackPromise, timeoutPromise]);
          
          // Handle both API response formats for the fallback API
          if (fallbackResponse.data) {
            let isValid = false;
            let address = null;
            
            // Check for new API format (status: success)
            if (fallbackResponse.data.status === "success" && fallbackResponse.data.address) {
              isValid = true;
              address = fallbackResponse.data.address;
            }
            // Check for old API format (success: true)
            else if (fallbackResponse.data.success === true && fallbackResponse.data.address) {
              isValid = true;
              address = fallbackResponse.data.address;
            }
            
            if (isValid && address) {
              this.storeWalletAddress(address);
              
              console.log('Imported wallet through fallback bootstrap node:', address);
              
              return {
                address: address,
                publicKey: fallbackResponse.data.publicKey || "Unknown",
                success: true
              };
            }
          }
          
          throw new Error('Invalid wallet data from fallback API');
        } catch (fallbackError) {
          console.error('Fallback bootstrap node seed import also failed:', fallbackError);
          throw new Error('Unable to import wallet on the blockchain. Please check your seed phrase and try again.');
        }
      }
    } catch (error) {
      console.error('Complete wallet import failure:', error);
      throw error;
    }
  },
  
  /**
   * Import from seed phrase locally in the browser
   * @private
   * @deprecated Use the blockchain API to import wallets
   */
  _importFromSeedPhrase: async function(seedPhrase) {
    console.error('Local wallet import is no longer supported. All wallets must be imported via the blockchain API.');
    throw new Error('Local wallet import is disabled. All wallets must be imported via the blockchain API.');
  },
  
  /**
   * Import wallet using private key
   * @param {string} privateKey - The WIF format private key
   * @returns {Promise<Object>} Wallet info
   */
  importWalletFromPrivateKey: async function(privateKey) {
    try {
      // Increase timeout for blockchain API
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timeout')), 10000)
      );
      
      try {
        // Validate the private key - basic validation for WIF format
        if (!privateKey || privateKey.length < 10) {
          throw new Error('Invalid private key format');
        }
        
        // Log debugging information
        console.log('Attempting to import wallet with private key, length:', privateKey.length);
        
        // Use the wallet API to import the wallet
        // Try different parameter names as the API might expect different formats
        // First try 'privateKey' as that's what's used in the exportPrivateKey response
        const requestData = {
          privateKey: privateKey,
          // Include alternative keys as fallbacks
          private_key: privateKey
        };
        
        // Set proper headers for the request
        const config = {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        };
        
        console.log('Sending import request to:', `${API_BASE_URL}/wallet/import/key`);
        console.log('Request data:', JSON.stringify(requestData));
        
        // Make request to import the wallet
        const responsePromise = axios.post(`${API_BASE_URL}/wallet/import/key`, requestData, config);
        const response = await Promise.race([responsePromise, timeoutPromise]);
        
        console.log('Import wallet API response:', response.data);
        
        // Check for different success response formats
        if (response.data && response.data.address) {
          // The API response matches {"address":"xyz", "message":"success", "status":"success"}
          this.storeWalletAddress(response.data.address);
          console.log('Imported wallet from private key:', response.data.address);
          
          return {
            address: response.data.address,
            publicKey: response.data.publicKey || "Unknown",
            success: true
          };
        } else if (response.data && response.data.success && response.data.address) {
          // Standard success format with 'success' field
          this.storeWalletAddress(response.data.address);
          console.log('Imported wallet from private key (success format):', response.data.address);
          
          return {
            address: response.data.address,
            publicKey: response.data.publicKey || "Unknown",
            success: true
          };
        } else if (response.data && response.data.status === "success" && response.data.address) {
          // Status-based success format
          this.storeWalletAddress(response.data.address);
          console.log('Imported wallet from private key (status format):', response.data.address);
          
          return {
            address: response.data.address,
            publicKey: response.data.publicKey || "Unknown",
            success: true
          };
        }
        
        // If we get here, the response has data but not in a format we recognized
        // Log the actual response for debugging
        console.error('API response did not match expected formats:', response.data);
        throw new Error('Invalid wallet data format from API');
      } catch (apiError) {
        console.error('Bootstrap node private key import failed:', apiError);
        
        // Try the fallback bootstrap node
        try {
          // Try with both parameter names
          const requestData = {
            privateKey: privateKey,
            private_key: privateKey
          };
          
          const config = {
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json'
            }
          };
          
          console.log('Trying fallback API:', `${FALLBACK_API_URL}/wallet/import/key`);
          const fallbackPromise = axios.post(`${FALLBACK_API_URL}/wallet/import/key`, requestData, config);
          const fallbackResponse = await Promise.race([fallbackPromise, timeoutPromise]);
          
          console.log('Fallback API response:', fallbackResponse.data);
          
          // Check all possible formats again
          if (fallbackResponse.data && fallbackResponse.data.address) {
            this.storeWalletAddress(fallbackResponse.data.address);
            console.log('Imported wallet from fallback API:', fallbackResponse.data.address);
            
            return {
              address: fallbackResponse.data.address,
              publicKey: fallbackResponse.data.publicKey || "Unknown",
              success: true
            };
          } else if (fallbackResponse.data && fallbackResponse.data.success && fallbackResponse.data.address) {
            this.storeWalletAddress(fallbackResponse.data.address);
            console.log('Imported wallet from fallback API (success format):', fallbackResponse.data.address);
            
            return {
              address: fallbackResponse.data.address,
              publicKey: fallbackResponse.data.publicKey || "Unknown",
              success: true
            };
          } else if (fallbackResponse.data && fallbackResponse.data.status === "success" && fallbackResponse.data.address) {
            this.storeWalletAddress(fallbackResponse.data.address);
            console.log('Imported wallet from fallback API (status format):', fallbackResponse.data.address);
            
            return {
              address: fallbackResponse.data.address,
              publicKey: fallbackResponse.data.publicKey || "Unknown",
              success: true
            };
          }
          
          console.error('Fallback API response did not match expected formats:', fallbackResponse.data);
          throw new Error('Invalid wallet data from fallback API');
        } catch (fallbackError) {
          console.error('Fallback bootstrap node private key import also failed:', fallbackError);
          throw new Error('Unable to import wallet on the blockchain. Please check your private key and try again.');
        }
      }
    } catch (error) {
      console.error('Complete wallet import failure:', error);
      throw error;
    }
  },
  
  /**
   * Import from private key locally in the browser
   * @private
   * @deprecated Use the blockchain API to import wallets
   */
  _importFromPrivateKey: async function(privateKey) {
    console.error('Local wallet import is no longer supported. All wallets must be imported via the blockchain API.');
    throw new Error('Local wallet import is disabled. All wallets must be imported via the blockchain API.');
  },
  
  /**
   * Helper function to compute SHA-256 hash
   * @param {string} message - The message to hash
   * @returns {Promise<string>} The hex-encoded hash
   */
  sha256: async function(message) {
    const encoder = new TextEncoder();
    const data = encoder.encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  },
  
  /**
   * Get all wallet addresses
   * @returns {Promise<Array>} List of wallet addresses
   */
  getWallets: async function() {
    try {
      // Try to use the blockchain API to get wallet list
      try {
        // First check our local tracking of wallets since the blockchain API
        // doesn't actually store wallet records centrally - it's decentralized
        const storedWallets = this.getStoredWallets();
        
        if (storedWallets && storedWallets.length > 0) {
          console.log('Using local tracking for wallet list:', storedWallets);
          return storedWallets;
        }
        
        // If no wallets were tracked locally, we likely don't have any
        console.log('No wallet addresses found in local tracking');
        return [];
      } catch (error) {
        console.error('Error getting wallets:', error);
        return [];
      }
    } catch (error) {
      console.error('Error getting wallets:', error);
      return [];
    }
  },
  
  /**
   * Get wallet balance
   * @param {string} address - The wallet address
   * @returns {Promise<Object>} Balance info
   */
  getBalance: async function(address) {
    try {
      // Use a timeout promise to prevent long-hanging requests
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timeout')), 5000)
      );
      
      try {
        // Try to use the Bootstrap Node API first
        const responsePromise = axios.get(`${API_BASE_URL}/wallet/balance/${address}`);
        const response = await Promise.race([responsePromise, timeoutPromise]);
        
        // Handle different API response formats:
        // - New format: {"address": "19qDv...", "balance": 0.0}
        // - Old format: {"success": true, "balance": 0.0}
        if (response.data) {
          let isValid = false;
          let balance = null;
          
          // Check for new API format (direct balance field)
          if (response.data.address === address && typeof response.data.balance === 'number') {
            isValid = true;
            balance = response.data.balance;
          }
          // Check for old API format (success field)
          else if (response.data.success === true && typeof response.data.balance === 'number') {
            isValid = true;
            balance = response.data.balance;
          }
          
          if (isValid && balance !== null) {
            // Cache the balance in localStorage for offline use
            try {
              const walletData = localStorage.getItem(`gcn_wallet_${address}`);
              let data = walletData ? JSON.parse(walletData) : { address };
              data.balance = balance;
              data.last_updated = new Date().toISOString();
              localStorage.setItem(`gcn_wallet_${address}`, JSON.stringify(data));
            } catch (cacheError) {
              console.warn('Error caching balance in localStorage:', cacheError);
            }
            
            return {
              address,
              balance: balance,
              source: 'blockchain',
              last_updated: new Date().toISOString()
            };
          }
        }
        
        throw new Error('Invalid balance format returned from API: ' + JSON.stringify(response.data));
      } catch (apiError) {
        console.warn(`API get balance failed for ${address}, trying fallback:`, apiError);
        
        // Try the second bootstrap node as fallback
        try {
          const fallbackPromise = axios.get(`${FALLBACK_API_URL}/wallet/balance/${address}`);
          const fallbackResponse = await Promise.race([fallbackPromise, timeoutPromise]);
          
          // Handle different API response formats for fallback API:
          // - New format: {"address": "19qDv...", "balance": 0.0}
          // - Old format: {"success": true, "balance": 0.0}
          if (fallbackResponse.data) {
            let isValid = false;
            let balance = null;
            
            // Check for new API format (direct balance field)
            if (fallbackResponse.data.address === address && typeof fallbackResponse.data.balance === 'number') {
              isValid = true;
              balance = fallbackResponse.data.balance;
            }
            // Check for old API format (success field)
            else if (fallbackResponse.data.success === true && typeof fallbackResponse.data.balance === 'number') {
              isValid = true;
              balance = fallbackResponse.data.balance;
            }
            
            if (isValid && balance !== null) {
              // Cache the balance
              try {
                const walletData = localStorage.getItem(`gcn_wallet_${address}`);
                let data = walletData ? JSON.parse(walletData) : { address };
                data.balance = balance;
                data.last_updated = new Date().toISOString();
                localStorage.setItem(`gcn_wallet_${address}`, JSON.stringify(data));
              } catch (cacheError) {
                console.warn('Error caching balance in localStorage:', cacheError);
              }
              
              return {
                address,
                balance: balance,
                source: 'blockchain_fallback',
                last_updated: new Date().toISOString()
              };
            }
          }
        } catch (fallbackError) {
          console.warn(`Fallback API get balance failed for ${address}, using localStorage:`, fallbackError);
        }
        
        // Both API attempts failed, use localStorage data if available
        const walletData = localStorage.getItem(`gcn_wallet_${address}`);
        if (walletData) {
          try {
            const data = JSON.parse(walletData);
            const balance = data.balance || 0;
            
            return { 
              address, 
              balance,
              source: 'localStorage',
              last_updated: data.last_updated || new Date().toISOString()
            };
          } catch (parseError) {
            console.warn('Error parsing wallet data from localStorage:', parseError);
          }
        }
        
        // Final fallback: generate mock data
        const addressSeed = address.split('').reduce((a, b) => a + b.charCodeAt(0), 0);
        const mockBalance = (addressSeed % 1000) / 100; // 0-10 range with decimals
        
        // Store this in localStorage for next time
        const mockData = {
          address,
          balance: mockBalance,
          createdAt: new Date().toISOString(),
          last_updated: new Date().toISOString()
        };
        localStorage.setItem(`gcn_wallet_${address}`, JSON.stringify(mockData));
        
        return { 
          address, 
          balance: mockBalance,
          source: 'mock',
          last_updated: new Date().toISOString()
        };
      }
    } catch (error) {
      console.error(`Error getting balance for ${address}:`, error);
      // Last resort fallback - generate a random balance
      return { 
        address, 
        balance: Math.random() * 10,
        source: 'emergency_fallback',
        last_updated: new Date().toISOString() 
      };
    }
  },
  
  /**
   * Get transactions for a wallet
   * @param {string} address - The wallet address
   * @param {number} page - Page number
   * @param {number} limit - Items per page
   * @returns {Promise<Object>} Transaction list
   */
  getTransactions: async function(address, page = 1, limit = 10) {
    try {
      // Use a timeout promise to prevent long-hanging requests
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timeout')), 5000)
      );
      
      try {
        // Try to get transactions directly from the wallet API
        const transactionsPromise = axios.get(`${API_BASE_URL}/wallet/transactions/${address}`);
        const transactionsResponse = await Promise.race([transactionsPromise, timeoutPromise]);
        
        // Process transactions from wallet API
        if (transactionsResponse.data && transactionsResponse.data.success && Array.isArray(transactionsResponse.data.transactions)) {
          const transactions = transactionsResponse.data.transactions.map(tx => ({
            // Use available transaction identifiers in order of preference
            id: tx.id || tx.tx_hash || tx.hash || tx.transaction_id || null,
            // Store original transaction hash fields for debugging/fallback
            tx_hash: tx.tx_hash || tx.hash || tx.id || null,
            hash: tx.hash || tx.tx_hash || tx.id || null,
            timestamp: tx.timestamp,
            from: tx.sender,
            to: tx.recipient,
            amount: tx.amount,
            fee: tx.fee || 0,
            status: 'confirmed',
            type: tx.type || (tx.sender === address ? 'sent' : 'received'),
            block_height: tx.blockIndex,
            block_hash: tx.blockHash || 'unknown'
          }));
          
          // Sort transactions by timestamp, newest first
          transactions.sort((a, b) => {
            const dateA = new Date(a.timestamp);
            const dateB = new Date(b.timestamp);
            return dateB - dateA;
          });
          
          // Paginate results
          const startIndex = (page - 1) * limit;
          const endIndex = page * limit;
          const paginatedTransactions = transactions.slice(startIndex, endIndex);
          
          const result = {
            address,
            transactions: paginatedTransactions,
            page,
            limit,
            total: transactions.length,
            pages: Math.ceil(transactions.length / limit),
            source: 'blockchain'
          };
          
          // Cache the result for future use
          localStorage.setItem(`gcn_transactions_${address}`, JSON.stringify({
            timestamp: new Date().toISOString(),
            data: result
          }));
          
          return result;
        }
        
        // If the wallet API fails or returns invalid data, fall back to the old method
        // The bootstrap node has mempool and blockchain APIs we can use to find transactions
        const blocksPromise = axios.get(`${API_BASE_URL}/blockchain/chain`);
        const blocksResponse = await Promise.race([blocksPromise, timeoutPromise]);
        
        // Iterate through the blockchain to find transactions for this address
        const transactions = [];
        
        if (blocksResponse.data && blocksResponse.data.chain && Array.isArray(blocksResponse.data.chain)) {
          // Scan the blockchain for transactions involving this address
          for (const block of blocksResponse.data.chain) {
            if (block.transactions && Array.isArray(block.transactions)) {
              for (const tx of block.transactions) {
                if (tx.sender === address || tx.recipient === address) {
                  transactions.push({
                    // Use available transaction identifiers in order of preference
                    id: tx.id || tx.tx_hash || tx.hash || tx.transaction_id || null,
                    // Store original transaction hash fields for debugging/fallback
                    tx_hash: tx.tx_hash || tx.hash || tx.id || null,
                    hash: tx.hash || tx.tx_hash || tx.id || null,
                    timestamp: tx.timestamp || block.timestamp,
                    from: tx.sender,
                    to: tx.recipient,
                    amount: tx.amount,
                    fee: tx.fee || 0,
                    status: 'confirmed',
                    type: tx.sender === address ? 'sent' : 'received',
                    block_height: block.index,
                    block_hash: block.hash
                  });
                }
              }
            }
          }
        }
        
        // Try to get mempool transactions as well
        try {
          const mempoolPromise = axios.get(`${API_BASE_URL}/transactions/mempool`);
          const mempoolResponse = await Promise.race([mempoolPromise, timeoutPromise]);
          
          if (mempoolResponse.data && Array.isArray(mempoolResponse.data)) {
            for (const tx of mempoolResponse.data) {
              if (tx.sender === address || tx.recipient === address) {
                transactions.push({
                  // Use available transaction identifiers in order of preference
                  id: tx.id || tx.tx_hash || tx.hash || tx.transaction_id || null,
                  // Store original transaction hash fields for debugging/fallback
                  tx_hash: tx.tx_hash || tx.hash || tx.id || null,
                  hash: tx.hash || tx.tx_hash || tx.id || null,
                  timestamp: tx.timestamp || new Date().toISOString(),
                  from: tx.sender,
                  to: tx.recipient,
                  amount: tx.amount,
                  fee: tx.fee || 0,
                  status: 'pending',
                  type: tx.sender === address ? 'sent' : 'received'
                });
              }
            }
          }
        } catch (mempoolError) {
          console.warn('Error getting mempool transactions:', mempoolError);
        }
        
        // Sort transactions by timestamp, newest first
        transactions.sort((a, b) => {
          const dateA = new Date(a.timestamp);
          const dateB = new Date(b.timestamp);
          return dateB - dateA;
        });
        
        // Paginate results
        const startIndex = (page - 1) * limit;
        const endIndex = page * limit;
        const paginatedTransactions = transactions.slice(startIndex, endIndex);
        
        const result = {
          address,
          transactions: paginatedTransactions,
          page,
          limit,
          total: transactions.length,
          pages: Math.ceil(transactions.length / limit),
          source: 'blockchain'
        };
        
        // Cache the result for future use
        localStorage.setItem(`gcn_transactions_${address}`, JSON.stringify({
          timestamp: new Date().toISOString(),
          data: result
        }));
        
        return result;
      } catch (apiError) {
        console.warn(`API get transactions failed for ${address}, trying fallback:`, apiError);
        
        // Try the fallback node's wallet API first
        try {
          const fallbackPromise = axios.get(`${FALLBACK_API_URL}/wallet/transactions/${address}`);
          const fallbackResponse = await Promise.race([fallbackPromise, timeoutPromise]);
          
          if (fallbackResponse.data && fallbackResponse.data.success && Array.isArray(fallbackResponse.data.transactions)) {
            const transactions = fallbackResponse.data.transactions.map(tx => ({
              // Use available transaction identifiers in order of preference
              id: tx.id || tx.tx_hash || tx.hash || tx.transaction_id || null,
              // Store original transaction hash fields for debugging/fallback
              tx_hash: tx.tx_hash || tx.hash || tx.id || null,
              hash: tx.hash || tx.tx_hash || tx.id || null,
              timestamp: tx.timestamp,
              from: tx.sender,
              to: tx.recipient,
              amount: tx.amount,
              fee: tx.fee || 0,
              status: 'confirmed',
              type: tx.type || (tx.sender === address ? 'sent' : 'received'),
              block_height: tx.blockIndex,
              block_hash: tx.blockHash || 'unknown'
            }));
            
            // Sort and paginate
            transactions.sort((a, b) => {
              const dateA = new Date(a.timestamp);
              const dateB = new Date(b.timestamp);
              return dateB - dateA;
            });
            
            const startIndex = (page - 1) * limit;
            const endIndex = page * limit;
            const paginatedTransactions = transactions.slice(startIndex, endIndex);
            
            const result = {
              address,
              transactions: paginatedTransactions,
              page,
              limit,
              total: transactions.length,
              pages: Math.ceil(transactions.length / limit),
              source: 'blockchain_fallback'
            };
            
            // Cache the result
            localStorage.setItem(`gcn_transactions_${address}`, JSON.stringify({
              timestamp: new Date().toISOString(),
              data: result
            }));
            
            return result;
          }
        } catch (fallbackWalletError) {
          console.warn(`Fallback wallet API get transactions failed for ${address}, trying blockchain API:`, fallbackWalletError);
        }
        
        // Try the fallback node's blockchain API
        try {
          const fallbackPromise = axios.get(`${FALLBACK_API_URL}/blockchain/chain`);
          const fallbackResponse = await Promise.race([fallbackPromise, timeoutPromise]);
          
          // Process transactions from fallback node (same logic as above)
          const transactions = [];
          
          if (fallbackResponse.data && fallbackResponse.data.chain && Array.isArray(fallbackResponse.data.chain)) {
            for (const block of fallbackResponse.data.chain) {
              if (block.transactions && Array.isArray(block.transactions)) {
                for (const tx of block.transactions) {
                  if (tx.sender === address || tx.recipient === address) {
                    transactions.push({
                      id: tx.id || `tx_${block.index}_${transactions.length}`,
                      timestamp: tx.timestamp || block.timestamp,
                      from: tx.sender,
                      to: tx.recipient,
                      amount: tx.amount,
                      fee: tx.fee || 0,
                      status: 'confirmed',
                      type: tx.sender === address ? 'sent' : 'received',
                      block_height: block.index,
                      block_hash: block.hash
                    });
                  }
                }
              }
            }
          }
          
          // Sort and paginate
          transactions.sort((a, b) => {
            const dateA = new Date(a.timestamp);
            const dateB = new Date(b.timestamp);
            return dateB - dateA;
          });
          
          const startIndex = (page - 1) * limit;
          const endIndex = page * limit;
          const paginatedTransactions = transactions.slice(startIndex, endIndex);
          
          const result = {
            address,
            transactions: paginatedTransactions,
            page,
            limit,
            total: transactions.length,
            pages: Math.ceil(transactions.length / limit),
            source: 'blockchain_fallback'
          };
          
          // Cache the result
          localStorage.setItem(`gcn_transactions_${address}`, JSON.stringify({
            timestamp: new Date().toISOString(),
            data: result
          }));
          
          return result;
        } catch (fallbackError) {
          console.warn(`Fallback blockchain API get transactions failed for ${address}, using cache:`, fallbackError);
        }
        
        // Check localStorage for cached transactions
        try {
          const cachedTransactions = localStorage.getItem(`gcn_transactions_${address}`);
          if (cachedTransactions) {
            const parsedData = JSON.parse(cachedTransactions);
            // Use cache if it's less than 30 minutes old
            const cacheAge = (Date.now() - new Date(parsedData.timestamp).getTime()) / 1000 / 60;
            if (cacheAge < 30) {
              console.log(`Using cached transactions (${cacheAge.toFixed(1)} min old)`);
              return parsedData.data;
            }
          }
        } catch (cacheError) {
          console.warn('Error reading cached transactions:', cacheError);
        }
        
        // Generate mock transaction data as last resort
        const mockData = this.getMockTransactions(address, page, limit);
        
        // Cache the mock data
        localStorage.setItem(`gcn_transactions_${address}`, JSON.stringify({
          timestamp: new Date().toISOString(),
          data: mockData
        }));
        
        return mockData;
      }
    } catch (error) {
      console.error(`Error getting transactions for ${address}:`, error);
      // Last resort fallback
      return { 
        address,
        transactions: [], 
        page, 
        limit, 
        total: 0, 
        pages: 0,
        source: 'error_fallback'
      };
    }
  },
  
  /**
   * Generate mock transaction data for development
   * @private
   */
  getMockTransactions: function(address, page = 1, limit = 10) {
    const transactions = [];
    const totalTxs = Math.floor(Math.random() * 10); // Random number up to 10 transactions
    
    for (let i = 0; i < Math.min(limit, totalTxs); i++) {
      const isSending = Math.random() > 0.5;
      const amount = Math.random() * 10 + 0.1; // Random amount between 0.1 and 10.1
      
      transactions.push({
        id: `tx_${Date.now()}_${Math.floor(Math.random() * 1000000)}`,
        timestamp: new Date(Date.now() - (i * 86400000 * Math.random())).toISOString(),
        from: isSending ? address : `gcn1${''.padStart(40, Math.random().toString(36).substring(2))}`,
        to: isSending ? `gcn1${''.padStart(40, Math.random().toString(36).substring(2))}` : address,
        amount: amount,
        fee: Math.random() * 0.01,
        status: 'confirmed',
        type: isSending ? 'sent' : 'received'
      });
    }
    
    return {
      address,
      transactions,
      page,
      limit,
      total: totalTxs,
      pages: Math.ceil(totalTxs / limit),
      source: 'mock'
    };
  },
  
  /**
   * Export private key for a wallet
   * @param {string} address - The wallet address
   * @returns {Promise<Object>} Private key info
   */
  exportPrivateKey: async function(address) {
    try {
      const response = await axios.post(`${API_BASE_URL}/wallet/export-key`, { address });
      return response.data;
    } catch (error) {
      console.error(`Error exporting private key for ${address}:`, error);
      throw error.response?.data || error;
    }
  },
  
  /**
   * Send transaction
   * @param {string} fromAddress - Sender address
   * @param {string} toAddress - Recipient address
   * @param {number} amount - Amount to send
   * @param {number} fee - Transaction fee
   * @returns {Promise<Object>} Transaction result
   */
  sendTransaction: async function(fromAddress, toAddress, amount, fee) {
    try {
      console.log('Sending transaction with params:', {
        sender: fromAddress,
        recipient: toAddress,
        amount,
        fee,
        env: isProduction ? 'production' : 'development',
        api_url: API_BASE_URL
      });
      
      // Step 1: Sign the transaction using the wallet's sign-transaction endpoint
      // This endpoint will handle the signature creation with the wallet's private key
      const signResponse = await axios.post(`${API_BASE_URL}/wallet/sign-transaction`, {
        sender: fromAddress,
        recipient: toAddress,
        amount: parseFloat(amount), // Ensure amount is a number
        fee: parseFloat(fee) // Ensure fee is a number
      }, axiosConfig);
      
      console.log('Transaction signing response:', signResponse.data);
      
      // Extract signature from the response (handle both formats)
      let signature;
      
      if (signResponse.data && signResponse.data.signature) {
        // Direct signature format
        signature = signResponse.data.signature;
      } else if (signResponse.data && signResponse.data.transaction && signResponse.data.transaction.signature) {
        // Nested signature format
        signature = signResponse.data.transaction.signature;
      } else {
        throw new Error('Failed to sign transaction: No signature returned');
      }
      
      console.log('Extracted signature:', signature);
      
      // Step 2: Submit the signed transaction to the transaction endpoint
      const submitResponse = await axios.post(`${API_BASE_URL}/transactions`, {
        sender: fromAddress,
        recipient: toAddress,
        amount: parseFloat(amount),
        fee: parseFloat(fee),
        signature: signature
      }, axiosConfig);
      
      console.log('Transaction submit response:', submitResponse.data);
      
      // Process response and return transaction data
      if (submitResponse.data) {
        // Return transaction data from the response
        return {
          transaction_id: submitResponse.data.id || submitResponse.data.transaction_id || submitResponse.data.hash || new Date().getTime().toString(),
          sender: fromAddress,
          recipient: toAddress,
          amount,
          fee,
          timestamp: submitResponse.data.timestamp || new Date().toISOString(),
          status: 'submitted'
        };
      }
      
      throw new Error('Invalid response from transaction submission API');
    } catch (error) {
      console.error('Error sending transaction:', error);
      
      // Try fallback node
      try {
        console.log('Trying fallback node for transaction');
        
        // Step 1: Sign with fallback node
        const fallbackSignResponse = await axios.post(`${FALLBACK_API_URL}/wallet/sign-transaction`, {
          sender: fromAddress,
          recipient: toAddress,
          amount: parseFloat(amount),
          fee: parseFloat(fee)
        }, axiosConfig);
        
        console.log('Fallback sign response:', fallbackSignResponse.data);
        
        // Extract signature from the response (handle both formats)
        let fallbackSignature;
        
        if (fallbackSignResponse.data && fallbackSignResponse.data.signature) {
          // Direct signature format
          fallbackSignature = fallbackSignResponse.data.signature;
        } else if (fallbackSignResponse.data && fallbackSignResponse.data.transaction && fallbackSignResponse.data.transaction.signature) {
          // Nested signature format
          fallbackSignature = fallbackSignResponse.data.transaction.signature;
        } else {
          throw new Error('Failed to sign transaction on fallback: No signature returned');
        }
        
        console.log('Extracted fallback signature:', fallbackSignature);
        
        // Step 2: Submit with fallback node
        const fallbackSubmitResponse = await axios.post(`${FALLBACK_API_URL}/transactions`, {
          sender: fromAddress,
          recipient: toAddress,
          amount: parseFloat(amount),
          fee: parseFloat(fee),
          signature: fallbackSignature
        }, axiosConfig);
        
        console.log('Fallback submit response:', fallbackSubmitResponse.data);
        
        if (fallbackSubmitResponse.data) {
          return {
            transaction_id: fallbackSubmitResponse.data.id || fallbackSubmitResponse.data.transaction_id || fallbackSubmitResponse.data.hash || new Date().getTime().toString(),
            sender: fromAddress,
            recipient: toAddress,
            amount,
            fee,
            timestamp: fallbackSubmitResponse.data.timestamp || new Date().toISOString(),
            status: 'submitted'
          };
        }
      } catch (fallbackError) {
        console.error('Fallback node transaction attempt also failed:', fallbackError);
      }
      
      // If all attempts fail, throw the original error
      throw error.response?.data || error;
    }
  },
  
  /**
   * Get fee estimate
   * @returns {Promise<Object>} Fee estimate
   */
  getFeeEstimate: async function() {
    try {
      const response = await axios.get(`${API_BASE_URL}/wallet/fee-estimate`);
      return response.data;
    } catch (error) {
      console.error('Error getting fee estimate:', error);
      return {
        recommended_fee: 0.001,
        min_fee: 0.0001,
        max_fee: 0.01
      };
    }
  },
  
  // Local storage utilities for wallet state
  
  /**
   * Store wallet address in local storage
   * @param {string} address - The wallet address
   */
  storeWalletAddress: function(address) {
    try {
      const wallets = this.getStoredWallets();
      
      if (!wallets.includes(address)) {
        wallets.push(address);
        localStorage.setItem('gcn_wallets', JSON.stringify(wallets));
      }
      
      // Set as current wallet
      localStorage.setItem('gcn_current_wallet', address);
    } catch (error) {
      console.error('Error storing wallet address:', error);
    }
  },
  
  /**
   * Get wallets from local storage
   * @returns {Array} List of wallet addresses
   */
  getStoredWallets: function() {
    try {
      const storedWallets = localStorage.getItem('gcn_wallets');
      return storedWallets ? JSON.parse(storedWallets) : [];
    } catch (error) {
      console.error('Error getting stored wallets:', error);
      return [];
    }
  },
  
  /**
   * Get current wallet from local storage
   * @returns {string|null} Current wallet address
   */
  getCurrentWallet: function() {
    return localStorage.getItem('gcn_current_wallet');
  },
  
  /**
   * Set current wallet
   * @param {string} address - Wallet address to set as current
   */
  setCurrentWallet: function(address) {
    localStorage.setItem('gcn_current_wallet', address);
  },
  
  /**
   * Clear wallet data
   */
  clearWalletData: function() {
    localStorage.removeItem('gcn_current_wallet');
    localStorage.removeItem('gcn_wallets');
  }
};

/**
 * Get the primary API URL
 * @returns {string} API base URL
 */
walletService.getApiUrl = function() {
  return API_BASE_URL;
};

/**
 * Get the fallback API URL
 * @returns {string} Fallback API base URL
 */
walletService.getFallbackApiUrl = function() {
  return FALLBACK_API_URL;
};

export default walletService;