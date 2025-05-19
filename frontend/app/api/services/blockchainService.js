const axios = require('axios');

// Configure the bootstrap node URLs
const BOOTSTRAP_NODE_URL = 'http://13.61.79.186:8001';
const FALLBACK_NODE_URL = 'http://13.61.79.186:8002';
const API_TIMEOUT = 5000; // 5 seconds

/**
 * Blockchain Service
 * Handles communication with blockchain nodes for data retrieval
 */
const blockchainService = {
  /**
   * Get general blockchain information
   */
  getBlockchainInfo: async function() {
    try {
      const response = await this.makeApiRequest(`${BOOTSTRAP_NODE_URL}/api/blockchain`);
      return response.data;
    } catch (error) {
      console.error('Error fetching blockchain info:', error);
      
      // Attempt fallback node
      try {
        const fallbackResponse = await this.makeApiRequest(`${FALLBACK_NODE_URL}/api/blockchain`);
        return fallbackResponse.data;
      } catch (fallbackError) {
        // Return mock data if both requests fail
        return this.getMockBlockchainInfo();
      }
    }
  },
  
  /**
   * Get blocks with pagination
   */
  getBlocks: async function(page = 1, limit = 10) {
    try {
      const response = await this.makeApiRequest(
        `${BOOTSTRAP_NODE_URL}/api/blockchain/blocks?page=${page}&limit=${limit}`
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching blocks:', error);
      
      // Attempt fallback node
      try {
        const fallbackResponse = await this.makeApiRequest(
          `${FALLBACK_NODE_URL}/api/blockchain/blocks?page=${page}&limit=${limit}`
        );
        return fallbackResponse.data;
      } catch (fallbackError) {
        // Return mock data if both requests fail
        return this.getMockBlocks(page, limit);
      }
    }
  },
  
  /**
   * Get a specific block by its hash
   */
  getBlockByHash: async function(hash) {
    try {
      const response = await this.makeApiRequest(`${BOOTSTRAP_NODE_URL}/api/blockchain/block/${hash}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching block ${hash}:`, error);
      
      // Attempt fallback node
      try {
        const fallbackResponse = await this.makeApiRequest(
          `${FALLBACK_NODE_URL}/api/blockchain/block/${hash}`
        );
        return fallbackResponse.data;
      } catch (fallbackError) {
        // Return null if both requests fail (this is an error case)
        return null;
      }
    }
  },
  
  /**
   * Get transactions with pagination
   */
  getTransactions: async function(page = 1, limit = 10) {
    try {
      const response = await this.makeApiRequest(
        `${BOOTSTRAP_NODE_URL}/api/blockchain/transactions?page=${page}&limit=${limit}`
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching transactions:', error);
      
      // Attempt fallback node
      try {
        const fallbackResponse = await this.makeApiRequest(
          `${FALLBACK_NODE_URL}/api/blockchain/transactions?page=${page}&limit=${limit}`
        );
        return fallbackResponse.data;
      } catch (fallbackError) {
        // Return mock data if both requests fail
        return this.getMockTransactions(page, limit);
      }
    }
  },
  
  /**
   * Get a specific transaction by its ID
   */
  getTransactionById: async function(id) {
    try {
      const response = await this.makeApiRequest(
        `${BOOTSTRAP_NODE_URL}/api/blockchain/transaction/${id}`
      );
      return response.data;
    } catch (error) {
      console.error(`Error fetching transaction ${id}:`, error);
      
      // Attempt fallback node
      try {
        const fallbackResponse = await this.makeApiRequest(
          `${FALLBACK_NODE_URL}/api/blockchain/transaction/${id}`
        );
        return fallbackResponse.data;
      } catch (fallbackError) {
        // Return null if both requests fail (this is an error case)
        return null;
      }
    }
  },
  
  /**
   * Get total coin supply
   */
  getTotalSupply: async function() {
    try {
      const response = await this.makeApiRequest(`${BOOTSTRAP_NODE_URL}/api/blockchain/supply`);
      return response.data;
    } catch (error) {
      console.error('Error fetching total supply:', error);
      
      // Attempt fallback node
      try {
        const fallbackResponse = await this.makeApiRequest(`${FALLBACK_NODE_URL}/api/blockchain/supply`);
        return fallbackResponse.data;
      } catch (fallbackError) {
        // Return mock data if both requests fail
        return {
          total_supply: 42000000 + Math.floor(Math.random() * 1000000),
          circulating_supply: 15000000 + Math.floor(Math.random() * 500000),
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
  getMockBlockchainInfo: function() {
    return {
      chain_length: 15000000 + Math.floor(Math.random() * 100000),
      difficulty: 3.5 + (Math.random() * 0.5),
      last_block_hash: '0x' + [...Array(64)].map(() => Math.floor(Math.random() * 16).toString(16)).join(''),
      block_time: 150, // seconds
      version: '1.0.0',
      consensus: 'Proof of Work',
      status: 'Active',
      timestamp: new Date().toISOString()
    };
  },
  
  getMockBlocks: function(page, limit) {
    const blocks = [];
    const totalBlocks = 15000000 + Math.floor(Math.random() * 100000);
    const startBlock = totalBlocks - ((page - 1) * limit);
    
    for (let i = 0; i < limit; i++) {
      const blockHeight = startBlock - i;
      if (blockHeight <= 0) break;
      
      blocks.push({
        height: blockHeight,
        hash: '0x' + [...Array(64)].map(() => Math.floor(Math.random() * 16).toString(16)).join(''),
        prev_hash: '0x' + [...Array(64)].map(() => Math.floor(Math.random() * 16).toString(16)).join(''),
        timestamp: new Date(Date.now() - (i * 150000)).toISOString(),
        tx_count: Math.floor(Math.random() * 20),
        size: 1024 + Math.floor(Math.random() * 2048),
        miner: 'gcn1' + [...Array(40)].map(() => Math.floor(Math.random() * 16).toString(16)).join('')
      });
    }
    
    return {
      blocks,
      page,
      limit,
      total: totalBlocks,
      pages: Math.ceil(totalBlocks / limit)
    };
  },
  
  getMockTransactions: function(page, limit) {
    const transactions = [];
    const totalTxs = 25000000 + Math.floor(Math.random() * 100000);
    
    for (let i = 0; i < limit; i++) {
      transactions.push({
        id: '0x' + [...Array(64)].map(() => Math.floor(Math.random() * 16).toString(16)).join(''),
        block_height: 15000000 - Math.floor(Math.random() * 1000),
        timestamp: new Date(Date.now() - (i * 60000)).toISOString(),
        from: 'gcn1' + [...Array(40)].map(() => Math.floor(Math.random() * 16).toString(16)).join(''),
        to: 'gcn1' + [...Array(40)].map(() => Math.floor(Math.random() * 16).toString(16)).join(''),
        amount: Math.floor(Math.random() * 100) + Math.random(),
        fee: 0.001 + (Math.random() * 0.01),
        status: 'confirmed'
      });
    }
    
    return {
      transactions,
      page,
      limit,
      total: totalTxs,
      pages: Math.ceil(totalTxs / limit)
    };
  }
};

module.exports = blockchainService;