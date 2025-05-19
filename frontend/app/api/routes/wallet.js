const express = require('express');
const router = express.Router();

// Import wallet service
const walletService = require('../services/walletService');

/**
 * @route POST /api/wallet/create
 * @description Create a new wallet
 */
router.post('/create', (req, res) => {
  try {
    const walletInfo = walletService.createWallet();
    res.json(walletInfo);
  } catch (error) {
    console.error('Error creating wallet:', error);
    res.status(500).json({ 
      error: 'Failed to create wallet',
      message: error.message 
    });
  }
});

/**
 * @route POST /api/wallet/import/seed
 * @description Import wallet from seed phrase
 */
router.post('/import/seed', (req, res) => {
  try {
    const { seedPhrase } = req.body;
    
    if (!seedPhrase) {
      return res.status(400).json({ error: 'Seed phrase is required' });
    }
    
    const walletInfo = walletService.importWalletFromSeed(seedPhrase);
    res.json(walletInfo);
  } catch (error) {
    console.error('Error importing wallet from seed:', error);
    res.status(500).json({ 
      error: 'Failed to import wallet',
      message: error.message 
    });
  }
});

/**
 * @route POST /api/wallet/import/key
 * @description Import wallet from private key
 */
router.post('/import/key', (req, res) => {
  try {
    const { privateKey } = req.body;
    
    if (!privateKey) {
      return res.status(400).json({ error: 'Private key is required' });
    }
    
    const walletInfo = walletService.importWalletFromPrivateKey(privateKey);
    res.json(walletInfo);
  } catch (error) {
    console.error('Error importing wallet from private key:', error);
    res.status(500).json({ 
      error: 'Failed to import wallet',
      message: error.message 
    });
  }
});

/**
 * @route GET /api/wallet/list
 * @description Get all wallet addresses
 */
router.get('/list', (req, res) => {
  try {
    const wallets = walletService.getWallets();
    res.json({ wallets });
  } catch (error) {
    console.error('Error listing wallets:', error);
    res.status(500).json({ 
      error: 'Failed to list wallets',
      message: error.message 
    });
  }
});

/**
 * @route POST /api/wallet/export-key
 * @description Export private key for a wallet
 */
router.post('/export-key', (req, res) => {
  try {
    const { address } = req.body;
    
    if (!address) {
      return res.status(400).json({ error: 'Wallet address is required' });
    }
    
    const privateKey = walletService.exportPrivateKey(address);
    res.json({ address, privateKey });
  } catch (error) {
    console.error('Error exporting private key:', error);
    res.status(500).json({ 
      error: 'Failed to export private key',
      message: error.message 
    });
  }
});

/**
 * @route POST /api/wallet/sign
 * @description Sign a transaction
 */
router.post('/sign', (req, res) => {
  try {
    const { fromAddress, toAddress, amount, fee } = req.body;
    
    // Validate required fields
    if (!fromAddress || !toAddress || !amount) {
      return res.status(400).json({ error: 'Missing required fields' });
    }
    
    // Validate amount
    if (parseFloat(amount) <= 0) {
      return res.status(400).json({ error: 'Amount must be greater than 0' });
    }
    
    const signedTx = walletService.signTransaction(fromAddress, toAddress, amount, fee);
    res.json(signedTx);
  } catch (error) {
    console.error('Error signing transaction:', error);
    res.status(500).json({ 
      error: 'Failed to sign transaction',
      message: error.message 
    });
  }
});

/**
 * @route GET /api/wallet/balance/:address
 * @description Get wallet balance for an address
 */
router.get('/balance/:address', async (req, res) => {
  try {
    const { address } = req.params;
    const balance = await walletService.getBalance(address);
    res.json(balance);
  } catch (error) {
    console.error(`Error fetching balance for ${req.params.address}:`, error);
    res.status(500).json({ 
      error: 'Failed to fetch wallet balance',
      message: error.message 
    });
  }
});

/**
 * @route GET /api/wallet/transactions/:address
 * @description Get transactions for a wallet address
 */
router.get('/transactions/:address', async (req, res) => {
  try {
    const { address } = req.params;
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    
    const transactions = await walletService.getTransactions(address, page, limit);
    res.json(transactions);
  } catch (error) {
    console.error(`Error fetching transactions for ${req.params.address}:`, error);
    res.status(500).json({ 
      error: 'Failed to fetch wallet transactions',
      message: error.message 
    });
  }
});

/**
 * @route POST /api/wallet/send
 * @description Send GCN to another address
 */
router.post('/send', async (req, res) => {
  try {
    const { fromAddress, toAddress, amount, signature, fee } = req.body;
    
    // Validate required fields
    if (!fromAddress || !toAddress || !amount || !signature) {
      return res.status(400).json({ error: 'Missing required fields' });
    }
    
    // Validate amount
    if (amount <= 0) {
      return res.status(400).json({ error: 'Amount must be greater than 0' });
    }
    
    const result = await walletService.sendTransaction(fromAddress, toAddress, amount, signature, fee);
    res.json(result);
  } catch (error) {
    console.error('Error sending transaction:', error);
    res.status(500).json({ 
      error: 'Failed to send transaction',
      message: error.message 
    });
  }
});

/**
 * @route GET /api/wallet/address/:publicKey
 * @description Get address from public key
 */
router.get('/address/:publicKey', (req, res) => {
  try {
    const { publicKey } = req.params;
    const address = walletService.getAddressFromPublicKey(publicKey);
    res.json({ publicKey, address });
  } catch (error) {
    console.error('Error generating address:', error);
    res.status(500).json({ 
      error: 'Failed to generate address',
      message: error.message 
    });
  }
});

/**
 * @route GET /api/wallet/fee-estimate
 * @description Get estimated transaction fee
 */
router.get('/fee-estimate', async (req, res) => {
  try {
    const feeEstimate = await walletService.getFeeEstimate();
    res.json(feeEstimate);
  } catch (error) {
    console.error('Error estimating fee:', error);
    res.status(500).json({ 
      error: 'Failed to estimate fee',
      message: error.message 
    });
  }
});

module.exports = router;