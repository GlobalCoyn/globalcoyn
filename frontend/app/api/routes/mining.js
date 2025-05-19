const express = require('express');
const router = express.Router();

// Import mining service
const miningService = require('../services/miningService');

/**
 * @route GET /api/mining/status
 * @description Get mining status
 */
router.get('/status', async (req, res) => {
  try {
    const status = await miningService.getMiningStatus();
    res.json(status);
  } catch (error) {
    console.error('Error fetching mining status:', error);
    res.status(500).json({ 
      error: 'Failed to fetch mining status',
      message: error.message 
    });
  }
});

/**
 * @route POST /api/mining/start
 * @description Start mining
 */
router.post('/start', async (req, res) => {
  try {
    const { walletAddress, threads, cpuUsage } = req.body;
    
    // Validate required fields
    if (!walletAddress) {
      return res.status(400).json({ error: 'Missing wallet address' });
    }
    
    const result = await miningService.startMining(walletAddress, threads, cpuUsage);
    res.json(result);
  } catch (error) {
    console.error('Error starting mining:', error);
    res.status(500).json({ 
      error: 'Failed to start mining',
      message: error.message 
    });
  }
});

/**
 * @route POST /api/mining/stop
 * @description Stop mining
 */
router.post('/stop', async (req, res) => {
  try {
    const result = await miningService.stopMining();
    res.json(result);
  } catch (error) {
    console.error('Error stopping mining:', error);
    res.status(500).json({ 
      error: 'Failed to stop mining',
      message: error.message 
    });
  }
});

/**
 * @route GET /api/mining/rewards/:address
 * @description Get mining rewards for an address
 */
router.get('/rewards/:address', async (req, res) => {
  try {
    const { address } = req.params;
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    
    const rewards = await miningService.getMiningRewards(address, page, limit);
    res.json(rewards);
  } catch (error) {
    console.error(`Error fetching mining rewards for ${req.params.address}:`, error);
    res.status(500).json({ 
      error: 'Failed to fetch mining rewards',
      message: error.message 
    });
  }
});

/**
 * @route GET /api/mining/hashrate
 * @description Get current mining hashrate
 */
router.get('/hashrate', async (req, res) => {
  try {
    const hashrate = await miningService.getHashrate();
    res.json(hashrate);
  } catch (error) {
    console.error('Error fetching mining hashrate:', error);
    res.status(500).json({ 
      error: 'Failed to fetch mining hashrate',
      message: error.message 
    });
  }
});

/**
 * @route GET /api/mining/estimate/:address
 * @description Get estimated mining rewards
 */
router.get('/estimate/:address', async (req, res) => {
  try {
    const { address } = req.params;
    const hashrate = parseFloat(req.query.hashrate) || 0;
    
    const estimate = await miningService.getRewardEstimate(address, hashrate);
    res.json(estimate);
  } catch (error) {
    console.error('Error calculating mining estimate:', error);
    res.status(500).json({ 
      error: 'Failed to calculate mining estimate',
      message: error.message 
    });
  }
});

module.exports = router;