const express = require('express');
const router = express.Router();

// Import network service
const networkService = require('../services/networkService');

/**
 * @route GET /api/network/status
 * @description Get network status
 */
router.get('/status', async (req, res) => {
  try {
    const status = await networkService.getNetworkStatus();
    res.json(status);
  } catch (error) {
    console.error('Error fetching network status:', error);
    res.status(500).json({ 
      error: 'Failed to fetch network status',
      message: error.message 
    });
  }
});

/**
 * @route GET /api/network/peers
 * @description Get all connected peers
 */
router.get('/peers', async (req, res) => {
  try {
    const peers = await networkService.getPeers();
    res.json({ peers });
  } catch (error) {
    console.error('Error fetching peers:', error);
    res.status(500).json({ 
      error: 'Failed to fetch peer information',
      message: error.message 
    });
  }
});

/**
 * @route POST /api/network/connect
 * @description Connect to a peer
 */
router.post('/connect', async (req, res) => {
  try {
    const { address, port } = req.body;
    
    // Validate required fields
    if (!address || !port) {
      return res.status(400).json({ error: 'Missing address or port' });
    }
    
    const result = await networkService.connectToPeer(address, port);
    res.json(result);
  } catch (error) {
    console.error('Error connecting to peer:', error);
    res.status(500).json({ 
      error: 'Failed to connect to peer',
      message: error.message 
    });
  }
});

/**
 * @route GET /api/network/difficulty
 * @description Get current mining difficulty
 */
router.get('/difficulty', async (req, res) => {
  try {
    const difficulty = await networkService.getDifficulty();
    res.json(difficulty);
  } catch (error) {
    console.error('Error fetching difficulty:', error);
    res.status(500).json({ 
      error: 'Failed to fetch difficulty',
      message: error.message 
    });
  }
});

/**
 * @route GET /api/network/hashrate
 * @description Get network hashrate
 */
router.get('/hashrate', async (req, res) => {
  try {
    const hashrate = await networkService.getHashrate();
    res.json(hashrate);
  } catch (error) {
    console.error('Error fetching hashrate:', error);
    res.status(500).json({ 
      error: 'Failed to fetch hashrate',
      message: error.message 
    });
  }
});

/**
 * @route GET /api/network/bootstrap-nodes
 * @description Get bootstrap nodes
 */
router.get('/bootstrap-nodes', (req, res) => {
  try {
    const bootstrapNodes = networkService.getBootstrapNodes();
    res.json({ bootstrapNodes });
  } catch (error) {
    console.error('Error fetching bootstrap nodes:', error);
    res.status(500).json({ 
      error: 'Failed to fetch bootstrap nodes',
      message: error.message 
    });
  }
});

module.exports = router;