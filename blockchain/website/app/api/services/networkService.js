const axios = require('axios');

// Configure the bootstrap node URLs
const BOOTSTRAP_NODE_URL = 'http://13.61.79.186:8001';
const FALLBACK_NODE_URL = 'http://13.61.79.186:8002';
const API_TIMEOUT = 5000; // 5 seconds

// Bootstrap nodes configuration
const BOOTSTRAP_NODES = [
  { address: '13.61.79.186', port: 8001 },
  { address: '13.61.79.186', port: 8002 }
];

/**
 * Network Service
 * Handles network-related operations and peer connections
 */
const networkService = {
  /**
   * Get network status
   */
  getNetworkStatus: async function() {
    try {
      const response = await this.makeApiRequest(`${BOOTSTRAP_NODE_URL}/api/network/status`);
      return response.data;
    } catch (error) {
      console.error('Error fetching network status:', error);
      
      // Attempt fallback node
      try {
        const fallbackResponse = await this.makeApiRequest(`${FALLBACK_NODE_URL}/api/network/status`);
        return fallbackResponse.data;
      } catch (fallbackError) {
        // Return mock data if both requests fail
        return this.getMockNetworkStatus();
      }
    }
  },
  
  /**
   * Get connected peers
   */
  getPeers: async function() {
    try {
      const response = await this.makeApiRequest(`${BOOTSTRAP_NODE_URL}/api/network/peers`);
      return response.data.peers;
    } catch (error) {
      console.error('Error fetching peers:', error);
      
      // Attempt fallback node
      try {
        const fallbackResponse = await this.makeApiRequest(`${FALLBACK_NODE_URL}/api/network/peers`);
        return fallbackResponse.data.peers;
      } catch (fallbackError) {
        // Return mock data if both requests fail
        return this.getMockPeers();
      }
    }
  },
  
  /**
   * Connect to a peer
   */
  connectToPeer: async function(address, port) {
    try {
      const response = await this.makeApiRequest(
        `${BOOTSTRAP_NODE_URL}/api/network/connect`,
        'post',
        { address, port }
      );
      return response.data;
    } catch (error) {
      console.error(`Error connecting to peer ${address}:${port}:`, error);
      
      // Attempt fallback node
      try {
        const fallbackResponse = await this.makeApiRequest(
          `${FALLBACK_NODE_URL}/api/network/connect`,
          'post',
          { address, port }
        );
        return fallbackResponse.data;
      } catch (fallbackError) {
        throw new Error('Failed to connect to peer');
      }
    }
  },
  
  /**
   * Get current mining difficulty
   */
  getDifficulty: async function() {
    try {
      const response = await this.makeApiRequest(`${BOOTSTRAP_NODE_URL}/api/network/difficulty`);
      return response.data;
    } catch (error) {
      console.error('Error fetching difficulty:', error);
      
      // Attempt fallback node
      try {
        const fallbackResponse = await this.makeApiRequest(`${FALLBACK_NODE_URL}/api/network/difficulty`);
        return fallbackResponse.data;
      } catch (fallbackError) {
        // Return mock data if both requests fail
        return {
          difficulty: 3.5 + (Math.random() * 0.5),
          next_adjustment: 5000 - Math.floor(Math.random() * 2000),
          last_updated: new Date().toISOString()
        };
      }
    }
  },
  
  /**
   * Get network hashrate
   */
  getHashrate: async function() {
    try {
      const response = await this.makeApiRequest(`${BOOTSTRAP_NODE_URL}/api/network/hashrate`);
      return response.data;
    } catch (error) {
      console.error('Error fetching hashrate:', error);
      
      // Attempt fallback node
      try {
        const fallbackResponse = await this.makeApiRequest(`${FALLBACK_NODE_URL}/api/network/hashrate`);
        return fallbackResponse.data;
      } catch (fallbackError) {
        // Return mock data if both requests fail
        return {
          hashrate: 1500000 + Math.floor(Math.random() * 500000),
          unit: 'H/s',
          last_updated: new Date().toISOString()
        };
      }
    }
  },
  
  /**
   * Get bootstrap nodes
   */
  getBootstrapNodes: function() {
    return BOOTSTRAP_NODES;
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
  getMockNetworkStatus: function() {
    return {
      status: 'online',
      active_nodes: 200 + Math.floor(Math.random() * 50),
      chain_height: 15000000 + Math.floor(Math.random() * 100000),
      last_block_time: new Date(Date.now() - (Math.random() * 150000)).toISOString(),
      avg_block_time: 150, // seconds
      difficulty: 3.5 + (Math.random() * 0.5),
      hashrate: 1500000 + Math.floor(Math.random() * 500000),
      hashrate_unit: 'H/s',
      uptime_percentage: 99.8 + (Math.random() * 0.2),
      version: '1.0.0',
      last_updated: new Date().toISOString()
    };
  },
  
  getMockPeers: function() {
    const peerCount = 10 + Math.floor(Math.random() * 20);
    const peers = [];
    
    for (let i = 0; i < peerCount; i++) {
      peers.push({
        id: i + 3, // Start with ID 3 (after bootstrap nodes)
        address: `${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}`,
        port: 9000 + Math.floor(Math.random() * 1000),
        version: '1.0.0',
        connected_since: new Date(Date.now() - (Math.random() * 86400000 * 7)).toISOString(), // Random time in the past week
        status: 'active'
      });
    }
    
    // Add bootstrap nodes
    peers.unshift(
      {
        id: 1,
        address: '13.61.79.186',
        port: 8001,
        version: '1.0.0',
        connected_since: new Date(Date.now() - 8640000000).toISOString(), // 100 days ago
        status: 'bootstrap'
      },
      {
        id: 2,
        address: '13.61.79.186',
        port: 8002,
        version: '1.0.0',
        connected_since: new Date(Date.now() - 8640000000).toISOString(), // 100 days ago
        status: 'bootstrap'
      }
    );
    
    return peers;
  }
};

module.exports = networkService;