import axios from 'axios';

// Production or dev API URLs (same as Explorer.js and walletService.js)
const PROD_API_URL = 'https://globalcoyn.com/api';
const DEV_API_URL = 'http://localhost:8001/api';

// Environment detection (same as Explorer.js and walletService.js)
const ENV_OVERRIDE = localStorage.getItem('gcn_environment');
const isProduction = ENV_OVERRIDE === 'production' || 
                    process.env.REACT_APP_ENV === 'production' || 
                    window.location.hostname === 'globalcoyn.com';

// Primary API URL (same as Explorer.js and walletService.js)
const API_BASE_URL = ENV_OVERRIDE === 'development' ? DEV_API_URL :
                    ENV_OVERRIDE === 'production' ? PROD_API_URL :
                    process.env.REACT_APP_API_URL || 
                    (isProduction ? PROD_API_URL : DEV_API_URL);

// Export API_URL for other components to use
export const API_URL = API_BASE_URL;

// Fallback URL - use the opposite environment for maximum availability
const FALLBACK_API_URL = isProduction ? 'http://localhost:8001/api' : 'https://globalcoyn.com/api';

/**
 * Network Service for Frontend
 * Handles interaction with the network API
 */
const networkService = {
  /**
   * Get network status
   * @returns {Promise<Object>} Network status
   */
  getNetworkStatus: async function() {
    try {
      console.log('Fetching network status from:', `${API_BASE_URL}/network/status`);
      const response = await axios.get(`${API_BASE_URL}/network/status`);
      
      if (response.data) {
        console.log('Network status response:', response.data);
        return {
          ...response.data,
          source: 'blockchain'
        };
      }
      
      throw new Error('Invalid network status data from API');
    } catch (error) {
      console.warn('Primary API get network status failed, trying fallback:', error);
      
      try {
        const fallbackResponse = await axios.get(`${FALLBACK_API_URL}/network/status`);
        
        if (fallbackResponse.data) {
          console.log('Fallback network status response:', fallbackResponse.data);
          return {
            ...fallbackResponse.data,
            source: 'blockchain_fallback'
          };
        }
      } catch (fallbackError) {
        console.warn('Fallback API get network status failed:', fallbackError);
      }
      
      return this.getMockNetworkStatus();
    }
  },
  
  /**
   * Get network peers
   * @returns {Promise<Object>} Network peers
   */
  getNetworkPeers: async function() {
    try {
      console.log('Fetching network peers from:', `${API_BASE_URL}/network/peers`);
      const response = await axios.get(`${API_BASE_URL}/network/peers`);
      
      if (response.data && Array.isArray(response.data.peers)) {
        console.log('Network peers response:', response.data);
        return {
          peers: response.data.peers,
          count: response.data.count || response.data.peers.length,
          source: 'blockchain'
        };
      }
      
      throw new Error('Invalid peers data from API');
    } catch (error) {
      console.warn('Primary API get peers failed, trying fallback:', error);
      
      try {
        const fallbackResponse = await axios.get(`${FALLBACK_API_URL}/network/peers`);
        
        if (fallbackResponse.data && Array.isArray(fallbackResponse.data.peers)) {
          console.log('Fallback network peers response:', fallbackResponse.data);
          return {
            peers: fallbackResponse.data.peers,
            count: fallbackResponse.data.count || fallbackResponse.data.peers.length,
            source: 'blockchain_fallback'
          };
        }
      } catch (fallbackError) {
        console.warn('Fallback API get peers failed:', fallbackError);
      }
      
      return this.getMockPeers();
    }
  },
  
  /**
   * Get network statistics
   * @returns {Promise<Object>} Network statistics
   */
  getNetworkStats: async function() {
    try {
      console.log('Fetching network stats from:', `${API_BASE_URL}/network/stats`);
      const response = await axios.get(`${API_BASE_URL}/network/stats`);
      
      if (response.data) {
        console.log('Network stats response:', response.data);
        return {
          ...response.data,
          source: 'blockchain'
        };
      }
      
      throw new Error('Invalid network stats data from API');
    } catch (error) {
      console.warn('Primary API get network stats failed, trying fallback:', error);
      
      try {
        const fallbackResponse = await axios.get(`${FALLBACK_API_URL}/network/stats`);
        
        if (fallbackResponse.data) {
          console.log('Fallback network stats response:', fallbackResponse.data);
          return {
            ...fallbackResponse.data,
            source: 'blockchain_fallback'
          };
        }
      } catch (fallbackError) {
        console.warn('Fallback API get network stats failed:', fallbackError);
      }
      
      return this.getMockNetworkStats();
    }
  },
  
  /**
   * Get blockchain information
   * @returns {Promise<Object>} Blockchain info
   */
  getBlockchainInfo: async function() {
    try {
      console.log('Fetching blockchain info from:', `${API_BASE_URL}/blockchain`);
      const response = await axios.get(`${API_BASE_URL}/blockchain`);
      
      if (response.data) {
        console.log('Blockchain info response:', response.data);
        return {
          ...response.data,
          source: 'blockchain'
        };
      }
      
      throw new Error('Invalid blockchain info data from API');
    } catch (error) {
      console.warn('Primary API get blockchain info failed, trying fallback:', error);
      
      try {
        const fallbackResponse = await axios.get(`${FALLBACK_API_URL}/blockchain`);
        
        if (fallbackResponse.data) {
          console.log('Fallback blockchain info response:', fallbackResponse.data);
          return {
            ...fallbackResponse.data,
            source: 'blockchain_fallback'
          };
        }
      } catch (fallbackError) {
        console.warn('Fallback API get blockchain info failed:', fallbackError);
      }
      
      return this.getMockBlockchainInfo();
    }
  },
  
  /**
   * Get information about the local node
   * @returns {Promise<Object>} Node information
   */
  getNodeInfo: async function() {
    try {
      // The root API endpoint returns node info
      console.log('Fetching node info from:', `${API_BASE_URL.replace('/api', '')}/`);
      const response = await axios.get(`${API_BASE_URL.replace('/api', '')}/`);
      
      if (response.data) {
        console.log('Node info response:', response.data);
        return {
          ...response.data,
          source: 'blockchain'
        };
      }
      
      throw new Error('Invalid node info data from API');
    } catch (error) {
      console.warn('Primary API get node info failed, trying fallback:', error);
      
      try {
        const fallbackResponse = await axios.get(`${FALLBACK_API_URL.replace('/api', '')}/`);
        
        if (fallbackResponse.data) {
          console.log('Fallback node info response:', fallbackResponse.data);
          return {
            ...fallbackResponse.data,
            source: 'blockchain_fallback'
          };
        }
      } catch (fallbackError) {
        console.warn('Fallback API get node info failed:', fallbackError);
      }
      
      return this.getMockNodeInfo();
    }
  },
  
  /**
   * Get network known nodes
   * @returns {Promise<Object>} List of known nodes
   */
  getKnownNodes: async function() {
    try {
      console.log('Fetching known nodes from:', `${API_BASE_URL}/network/nodes`);
      const response = await axios.get(`${API_BASE_URL}/network/nodes`);
      
      if (response.data && Array.isArray(response.data.nodes)) {
        console.log('Known nodes response:', response.data);
        return {
          nodes: response.data.nodes,
          count: response.data.count || response.data.nodes.length,
          source: 'blockchain'
        };
      }
      
      throw new Error('Invalid nodes data from API');
    } catch (error) {
      console.warn('Primary API get nodes failed, trying fallback:', error);
      
      try {
        const fallbackResponse = await axios.get(`${FALLBACK_API_URL}/network/nodes`);
        
        if (fallbackResponse.data && Array.isArray(fallbackResponse.data.nodes)) {
          console.log('Fallback known nodes response:', fallbackResponse.data);
          return {
            nodes: fallbackResponse.data.nodes,
            count: fallbackResponse.data.count || fallbackResponse.data.nodes.length,
            source: 'blockchain_fallback'
          };
        }
      } catch (fallbackError) {
        console.warn('Fallback API get nodes failed:', fallbackError);
      }
      
      return this.getMockKnownNodes();
    }
  },
  
  /**
   * Connect to the network (starts a new node)
   * @returns {Promise<Object>} Connection result
   */
  connectToNetwork: async function() {
    try {
      console.log('Connecting to network:', `${API_BASE_URL}/network/discover`);
      // First try to discover peers
      const response = await axios.post(`${API_BASE_URL}/network/discover`);
      
      if (response.data) {
        console.log('Network discover response:', response.data);
        return {
          success: response.data.success || true,
          peers: response.data.discovered_peers || [],
          peerCount: response.data.peer_count || 0,
          message: 'Successfully connected to the blockchain network',
          source: 'blockchain'
        };
      }
      
      throw new Error('Invalid discover response from API');
    } catch (error) {
      console.warn('Primary API network discovery failed, trying fallback:', error);
      
      try {
        const fallbackResponse = await axios.post(`${FALLBACK_API_URL}/network/discover`);
        
        if (fallbackResponse.data) {
          console.log('Fallback network discover response:', fallbackResponse.data);
          return {
            success: fallbackResponse.data.success || true,
            peers: fallbackResponse.data.discovered_peers || [],
            peerCount: fallbackResponse.data.peer_count || 0,
            message: 'Successfully connected to the blockchain network using fallback node',
            source: 'blockchain_fallback'
          };
        }
      } catch (fallbackError) {
        console.warn('Fallback API network discovery failed:', fallbackError);
      }
      
      // For development mode, still return success for better UX
      if (!isProduction) {
        return {
          success: true,
          peers: [],
          peerCount: 0,
          message: 'Development mode: Simulated successful connection',
          source: 'mock'
        };
      }
      
      return {
        success: false,
        peers: [],
        peerCount: 0,
        message: 'Failed to connect to the blockchain network. Please try again later.',
        source: 'mock'
      };
    }
  },
  
  /**
   * Sync with the network
   * @returns {Promise<Object>} Sync result
   */
  syncWithNetwork: async function() {
    try {
      console.log('Syncing with network:', `${API_BASE_URL}/network/sync`);
      const response = await axios.post(`${API_BASE_URL}/network/sync`);
      
      if (response.data) {
        console.log('Network sync response:', response.data);
        return {
          ...response.data,
          success: response.data.success || true,
          source: 'blockchain'
        };
      }
      
      throw new Error('Invalid sync response from API');
    } catch (error) {
      console.warn('Primary API network sync failed, trying fallback:', error);
      
      try {
        const fallbackResponse = await axios.post(`${FALLBACK_API_URL}/network/sync`);
        
        if (fallbackResponse.data) {
          console.log('Fallback network sync response:', fallbackResponse.data);
          return {
            ...fallbackResponse.data,
            success: fallbackResponse.data.success || true,
            source: 'blockchain_fallback'
          };
        }
      } catch (fallbackError) {
        console.warn('Fallback API network sync failed:', fallbackError);
      }
      
      // For development mode, still return success for better UX
      if (!isProduction) {
        return {
          success: true,
          message: 'Development mode: Simulated successful synchronization',
          synchronized: true,
          source: 'mock'
        };
      }
      
      return {
        success: false,
        message: 'Failed to sync with the blockchain network. Please try again later.',
        source: 'mock'
      };
    }
  },
  
  /**
   * Get API URLs used by this service
   * @returns {Object} API URLs
   */
  getApiUrls: function() {
    return {
      primary: API_BASE_URL,
      fallback: FALLBACK_API_URL,
      isProduction: isProduction
    };
  },
  
  /**
   * Generate mock network status data for development
   * @private
   */
  getMockNetworkStatus: function() {
    const nodePorts = [9000, 9001, 9002, 9003];
    const peers = nodePorts.map((port, index) => ({
      node_id: `localhost:${port}`,
      address: 'localhost',
      port: port,
      last_seen: Math.random() * 60
    }));
    
    return {
      status: 'online',
      network_mode: 'development',
      this_node: {
        address: 'localhost',
        port: 8001,
        blockchain_height: 10 + Math.floor(Math.random() * 100)
      },
      connected_peers: peers,
      peer_count: peers.length,
      uptime: 3600 + Math.random() * 86400,
      source: 'mock'
    };
  },
  
  /**
   * Generate mock peers data for development
   * @private
   */
  getMockPeers: function() {
    const nodePorts = [9000, 9001, 9002, 9003];
    const peers = nodePorts.map((port, index) => ({
      node_id: `localhost:${port}`,
      address: 'localhost',
      port: port,
      last_seen: Math.random() * 60
    }));
    
    return {
      peers,
      count: peers.length,
      source: 'mock'
    };
  },
  
  /**
   * Generate mock network stats data for development
   * @private
   */
  getMockNetworkStats: function() {
    const nodePorts = [9000, 9001, 9002, 9003];
    const peerStats = nodePorts.map((port, index) => ({
      node_id: `localhost:${port}`,
      last_seen_seconds: Math.random() * 60,
      is_active: Math.random() > 0.2
    }));
    
    // Calculate active peers
    const activePeers = peerStats.filter(p => p.is_active).length;
    
    return {
      total_peers: peerStats.length,
      active_peers: activePeers,
      inactive_peers: peerStats.length - activePeers,
      uptime: 3600 + Math.random() * 86400,
      peer_stats: peerStats,
      source: 'mock'
    };
  },
  
  /**
   * Generate mock blockchain info data for development
   * @private
   */
  getMockBlockchainInfo: function() {
    return {
      status: 'online',
      chain_length: 10 + Math.floor(Math.random() * 100),
      latest_block_hash: '0x' + Math.random().toString(16).substring(2, 66),
      latest_block_timestamp: new Date().toISOString(),
      difficulty: {
        bits: 20 + Math.floor(Math.random() * 4),
        target: '0x' + '0'.repeat(5) + Math.random().toString(16).substring(2, 60)
      },
      transactions_in_mempool: Math.floor(Math.random() * 5),
      node_count: 4,
      network_mode: 'development',
      source: 'mock'
    };
  },
  
  /**
   * Generate mock node info data for development
   * @private
   */
  getMockNodeInfo: function() {
    return {
      name: 'GlobalCoyn Blockchain Node',
      version: '1.0.0',
      node_number: Math.floor(Math.random() * 5) + 1,
      p2p_port: 9000 + Math.floor(Math.random() * 5),
      api_port: 8000 + Math.floor(Math.random() * 5),
      blockchain_height: 10 + Math.floor(Math.random() * 100),
      connected_peers: Math.floor(Math.random() * 4) + 1,
      source: 'mock'
    };
  },
  
  /**
   * Generate mock known nodes data for development
   * @private
   */
  getMockKnownNodes: function() {
    const nodes = [];
    
    // Generate mock nodes based on default port ranges
    for (let i = 1; i <= 4; i++) {
      nodes.push({
        address: 'localhost',
        web_port: 8000 + i,
        p2p_port: 9000 + (i - 1),
        connected: Math.random() > 0.2,
        last_seen: Math.random() * 300
      });
    }
    
    return {
      nodes,
      count: nodes.length,
      source: 'mock'
    };
  }
};

export default networkService;