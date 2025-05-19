const express = require('express');
const router = express.Router();

// Import blockchain service
const blockchainService = require('../services/blockchainService');

/**
 * @route GET /api/blockchain
 * @description Get blockchain information
 */
router.get('/', async (req, res) => {
  try {
    const data = await blockchainService.getBlockchainInfo();
    res.json(data);
  } catch (error) {
    console.error('Error fetching blockchain info:', error);
    res.status(500).json({ 
      error: 'Failed to fetch blockchain information',
      message: error.message 
    });
  }
});

/**
 * @route GET /api/blockchain/blocks
 * @description Get a list of blocks
 */
router.get('/blocks', async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    
    const blocks = await blockchainService.getBlocks(page, limit);
    res.json(blocks);
  } catch (error) {
    console.error('Error fetching blocks:', error);
    res.status(500).json({ 
      error: 'Failed to fetch blocks',
      message: error.message 
    });
  }
});

/**
 * @route GET /api/blockchain/block/:hash
 * @description Get block by hash
 */
router.get('/block/:hash', async (req, res) => {
  try {
    const { hash } = req.params;
    const block = await blockchainService.getBlockByHash(hash);
    
    if (!block) {
      return res.status(404).json({ error: 'Block not found' });
    }
    
    res.json(block);
  } catch (error) {
    console.error(`Error fetching block ${req.params.hash}:`, error);
    res.status(500).json({ 
      error: 'Failed to fetch block',
      message: error.message 
    });
  }
});

/**
 * @route GET /api/blockchain/transactions
 * @description Get recent transactions
 */
router.get('/transactions', async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    
    const transactions = await blockchainService.getTransactions(page, limit);
    res.json(transactions);
  } catch (error) {
    console.error('Error fetching transactions:', error);
    res.status(500).json({ 
      error: 'Failed to fetch transactions',
      message: error.message 
    });
  }
});

/**
 * @route GET /api/blockchain/transaction/:id
 * @description Get transaction by ID
 */
router.get('/transaction/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const transaction = await blockchainService.getTransactionById(id);
    
    if (!transaction) {
      return res.status(404).json({ error: 'Transaction not found' });
    }
    
    res.json(transaction);
  } catch (error) {
    console.error(`Error fetching transaction ${req.params.id}:`, error);
    res.status(500).json({ 
      error: 'Failed to fetch transaction',
      message: error.message 
    });
  }
});

/**
 * @route GET /api/blockchain/supply
 * @description Get total coin supply
 */
router.get('/supply', async (req, res) => {
  try {
    const supply = await blockchainService.getTotalSupply();
    res.json(supply);
  } catch (error) {
    console.error('Error fetching supply:', error);
    res.status(500).json({ 
      error: 'Failed to fetch supply information',
      message: error.message 
    });
  }
});

module.exports = router;