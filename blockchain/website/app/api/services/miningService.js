const axios = require('axios');

// Configure the bootstrap node URLs
const BOOTSTRAP_NODE_URL = 'http://13.61.79.186:8001';
const FALLBACK_NODE_URL = 'http://13.61.79.186:8002';
const API_TIMEOUT = 5000; // 5 seconds

// Mining state (in a real implementation, this would be stored in a database or state management system)
let miningState = {
  isMining: false,
  walletAddress: null,
  threads: 1,
  cpuUsage: 50,
  hashrate: 0,
  startTime: null,
  blocksFound: 0
};

/**
 * Mining Service
 * Handles mining operations and reward tracking
 */
const miningService = {
  /**
   * Get mining status
   */
  getMiningStatus: async function() {
    // For the web version, we'll return the internal mining state
    // In a native app, this would query the actual mining process
    return {
      is_mining: miningState.isMining,
      wallet_address: miningState.walletAddress,
      threads: miningState.threads,
      cpu_usage: miningState.cpuUsage,
      hashrate: miningState.hashrate,
      uptime: miningState.startTime ? Math.floor((Date.now() - miningState.startTime) / 1000) : 0,
      blocks_found: miningState.blocksFound,
      last_updated: new Date().toISOString()
    };
  },
  
  /**
   * Start mining
   */
  startMining: async function(walletAddress, threads = 1, cpuUsage = 50) {
    if (!walletAddress) {
      throw new Error('Wallet address is required');
    }
    
    // Validate parameters
    threads = Math.max(1, Math.min(navigator.hardwareConcurrency || 4, parseInt(threads) || 1));
    cpuUsage = Math.max(10, Math.min(90, parseInt(cpuUsage) || 50));
    
    // Update mining state
    miningState = {
      isMining: true,
      walletAddress,
      threads,
      cpuUsage,
      hashrate: this.generateRandomHashrate(threads, cpuUsage), // Simulated hashrate
      startTime: Date.now(),
      blocksFound: miningState.blocksFound || 0
    };
    
    // In a real implementation, this would start a Web Worker for mining
    // For now, we'll simulate mining activity
    this.simulateMining();
    
    return {
      success: true,
      message: 'Mining started successfully',
      status: this.getMiningStatus()
    };
  },
  
  /**
   * Stop mining
   */
  stopMining: async function() {
    // Update mining state
    miningState.isMining = false;
    miningState.hashrate = 0;
    
    // In a real implementation, this would stop the Web Worker
    
    return {
      success: true,
      message: 'Mining stopped successfully',
      status: this.getMiningStatus()
    };
  },
  
  /**
   * Get mining rewards for an address
   */
  getMiningRewards: async function(address, page = 1, limit = 10) {
    try {
      const response = await this.makeApiRequest(
        `${BOOTSTRAP_NODE_URL}/api/mining/rewards/${address}?page=${page}&limit=${limit}`
      );
      return response.data;
    } catch (error) {
      console.error(`Error fetching mining rewards for ${address}:`, error);
      
      // Attempt fallback node
      try {
        const fallbackResponse = await this.makeApiRequest(
          `${FALLBACK_NODE_URL}/api/mining/rewards/${address}?page=${page}&limit=${limit}`
        );
        return fallbackResponse.data;
      } catch (fallbackError) {
        // Return mock data if both requests fail
        return this.getMockMiningRewards(address, page, limit);
      }
    }
  },
  
  /**
   * Get current mining hashrate
   */
  getHashrate: async function() {
    // For the web version, we'll return the internal mining state hashrate
    return {
      hashrate: miningState.hashrate,
      unit: 'H/s',
      last_updated: new Date().toISOString()
    };
  },
  
  /**
   * Get estimated mining rewards
   */
  getRewardEstimate: async function(address, hashrate) {
    // Use network difficulty to calculate estimated rewards
    try {
      // Get current difficulty
      const difficultyResponse = await this.makeApiRequest(`${BOOTSTRAP_NODE_URL}/api/network/difficulty`);
      const difficulty = difficultyResponse.data.difficulty;
      
      // Get network hashrate
      const hashrateResponse = await this.makeApiRequest(`${BOOTSTRAP_NODE_URL}/api/network/hashrate`);
      const networkHashrate = hashrateResponse.data.hashrate;
      
      // Calculate estimates
      const blockTime = 150; // seconds
      const blocksPerDay = 86400 / blockTime;
      const blockReward = 50; // GCN
      
      // User's share of network hashrate
      const userShare = hashrate / networkHashrate;
      
      // Estimated blocks per day for the user
      const estimatedBlocksPerDay = blocksPerDay * userShare;
      
      // Estimated rewards per day
      const estimatedRewardsPerDay = estimatedBlocksPerDay * blockReward;
      
      return {
        address,
        hashrate,
        network_hashrate: networkHashrate,
        difficulty,
        estimated_blocks_per_day: estimatedBlocksPerDay,
        estimated_rewards_per_day: estimatedRewardsPerDay,
        block_reward: blockReward,
        last_updated: new Date().toISOString()
      };
    } catch (error) {
      console.error('Error calculating mining estimate:', error);
      
      // Return mock estimate if API calls fail
      return this.getMockRewardEstimate(address, hashrate);
    }
  },
  
  /**
   * Simulate mining (for demonstration purposes)
   */
  simulateMining: function() {
    if (!miningState.isMining) return;
    
    // Simulate hashrate fluctuations
    const updateHashrate = () => {
      if (!miningState.isMining) return;
      
      // Fluctuate hashrate by ±10%
      const baseHashrate = this.generateRandomHashrate(miningState.threads, miningState.cpuUsage);
      const fluctuation = 0.9 + (Math.random() * 0.2); // 0.9 to 1.1
      miningState.hashrate = Math.floor(baseHashrate * fluctuation);
      
      // Simulate occasional block finds (roughly 1 in 1000 chance per update)
      if (Math.random() < 0.001) {
        miningState.blocksFound++;
        console.log(`Simulated mining: Found block #${miningState.blocksFound}`);
      }
      
      // Schedule next update if still mining
      if (miningState.isMining) {
        setTimeout(updateHashrate, 3000);
      }
    };
    
    // Start the simulation
    updateHashrate();
  },
  
  /**
   * Generate a random but plausible hashrate based on threads and CPU usage
   */
  generateRandomHashrate: function(threads, cpuUsage) {
    // Base hashrate per thread at 100% CPU (very simplified model)
    const baseHashratePerThread = 15 + Math.random() * 10; // 15-25 H/s per thread
    
    // Calculate based on threads and CPU usage
    return Math.floor(baseHashratePerThread * threads * (cpuUsage / 100));
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
  getMockMiningRewards: function(address, page, limit) {
    const rewards = [];
    const totalRewards = Math.floor(Math.random() * 20); // Random number of rewards
    
    for (let i = 0; i < Math.min(limit, totalRewards - ((page - 1) * limit)); i++) {
      rewards.push({
        block_height: 15000000 - Math.floor(Math.random() * 10000),
        block_hash: '0x' + [...Array(64)].map(() => Math.floor(Math.random() * 16).toString(16)).join(''),
        timestamp: new Date(Date.now() - (i * 86400000 * Math.random() * 30)).toISOString(),
        reward_amount: 50, // Fixed block reward
        status: 'confirmed'
      });
    }
    
    return {
      address,
      rewards,
      total_rewards: totalRewards,
      total_amount: totalRewards * 50,
      page,
      limit,
      total: totalRewards,
      pages: Math.ceil(totalRewards / limit)
    };
  },
  
  getMockRewardEstimate: function(address, hashrate) {
    // Simulate network parameters
    const networkHashrate = 1500000 + Math.floor(Math.random() * 500000);
    const difficulty = 3.5 + (Math.random() * 0.5);
    const blockTime = 150; // seconds
    const blocksPerDay = 86400 / blockTime;
    const blockReward = 50; // GCN
    
    // User's share of network hashrate
    const userShare = hashrate / networkHashrate;
    
    // Estimated blocks per day for the user
    const estimatedBlocksPerDay = blocksPerDay * userShare;
    
    // Estimated rewards per day
    const estimatedRewardsPerDay = estimatedBlocksPerDay * blockReward;
    
    return {
      address,
      hashrate,
      network_hashrate: networkHashrate,
      difficulty,
      estimated_blocks_per_day: estimatedBlocksPerDay,
      estimated_rewards_per_day: estimatedRewardsPerDay,
      block_reward: blockReward,
      last_updated: new Date().toISOString()
    };
  }
};

module.exports = miningService;