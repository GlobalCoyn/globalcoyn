const express = require('express');
const axios = require('axios');
const router = express.Router();

// Configure the bootstrap node URLs for blockchain operations
const BOOTSTRAP_NODE_URL = 'http://13.61.79.186:8001';
const FALLBACK_NODE_URL = 'http://13.61.79.186:8002';
const API_TIMEOUT = 10000; // 10 seconds for profile operations

// IPFS configuration using the provided Pinata credentials
const PINATA_JWT = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiJhNTE3MmY4Mi04NTkzLTQ2YjgtOWJhOC1kMDEzOGNhZTNmZTAiLCJlbWFpbCI6ImFkYW1uZXRvZGV2QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJwaW5fcG9saWN5Ijp7InJlZ2lvbnMiOlt7ImRlc2lyZWRSZXBsaWNhdGlvbkNvdW50IjoxLCJpZCI6IkZSQTEifSx7ImRlc2lyZWRSZXBsaWNhdGlvbkNvdW50IjoxLCJpZCI6Ik5ZQzEifV0sInZlcnNpb24iOjF9LCJtZmFfZW5hYmxlZCI6ZmFsc2UsInN0YXR1cyI6IkFDVElWRSJ9LCJhdXRoZW50aWNhdGlvblR5cGUiOiJzY29wZWRLZXkiLCJzY29wZWRLZXlLZXkiOiIwNTg4MDNiMDM3MTM0MTFmN2JiOCIsInNjb3BlZEtleVNlY3JldCI6IjdiZTczYzNiZWNjM2Y4NmE0YWIzMGY3ODg3NjhiMmMyZjBhODExZTBkMzY5MGEyNTRjNTA0NTIxNDU3YWY3OGMiLCJleHAiOjE3Njc2MTg5MTR9.qd4PTUx5F9hJkRrq8PZsAT3qFh6-xhxSmhAq_VO9EYs';

// Helper function to validate wallet address format (GlobalCoyn format)
const isValidAddress = (address) => {
  return /^gcn1[a-zA-Z0-9]{39}$/.test(address) || /^[a-zA-Z0-9]{34,44}$/.test(address);
};

// Helper function to validate IPFS hash
const isValidIPFSHash = (hash) => {
  return /^Qm[a-zA-Z0-9]{44}$/.test(hash) || /^baf[a-zA-Z0-9]{56}$/.test(hash);
};

// Helper function to validate alias
const isValidAlias = (alias) => {
  return /^[a-zA-Z0-9_-]{3,20}$/.test(alias);
};

// Helper function to make blockchain API requests
const makeBlockchainRequest = async (endpoint, method = 'GET', data = null) => {
  try {
    const response = await axios({
      method,
      url: `${BOOTSTRAP_NODE_URL}${endpoint}`,
      data,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  } catch (error) {
    console.log(`Primary node failed, trying fallback for ${endpoint}`);
    try {
      const fallbackResponse = await axios({
        method,
        url: `${FALLBACK_NODE_URL}${endpoint}`,
        data,
        timeout: API_TIMEOUT,
        headers: {
          'Content-Type': 'application/json'
        }
      });
      return fallbackResponse.data;
    } catch (fallbackError) {
      console.error(`Both nodes failed for ${endpoint}:`, fallbackError.message);
      throw new Error(`Blockchain nodes unavailable: ${fallbackError.message}`);
    }
  }
};

// Helper function to validate IPFS image upload
const validateIPFSImage = async (ipfsHash) => {
  if (!ipfsHash) return true; // Optional field
  
  try {
    // Check if the IPFS hash is accessible via Pinata gateway
    const response = await axios.head(`https://gateway.pinata.cloud/ipfs/${ipfsHash}`, {
      timeout: 5000
    });
    return response.status === 200;
  } catch (error) {
    console.error(`IPFS validation failed for hash ${ipfsHash}:`, error.message);
    return false;
  }
};

// GET /api/profiles/:address - Get profile by wallet address
router.get('/:address', async (req, res) => {
  try {
    const { address } = req.params;
    
    if (!isValidAddress(address)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid wallet address format'
      });
    }

    // Call the blockchain node to get profile from smart contract
    const profileData = await makeBlockchainRequest(`/api/contracts/profile/get/${address}`);
    
    if (!profileData || !profileData.profile) {
      return res.status(404).json({
        success: false,
        error: 'Profile not found'
      });
    }

    res.json({
      success: true,
      profile: {
        walletAddress: address,
        alias: profileData.profile.alias,
        bio: profileData.profile.bio,
        ipfsHash: profileData.profile.ipfsHash,
        lastUpdated: profileData.profile.lastUpdated
      }
    });
  } catch (error) {
    console.error('Error fetching profile:', error);
    
    if (error.message.includes('Profile not found') || error.message.includes('404')) {
      return res.status(404).json({
        success: false,
        error: 'Profile not found'
      });
    }
    
    res.status(500).json({
      success: false,
      error: 'Failed to fetch profile from blockchain'
    });
  }
});

// POST /api/profiles - Create or update profile (stores on blockchain)
router.post('/', async (req, res) => {
  try {
    const { walletAddress, alias, bio, ipfsHash } = req.body;

    // Validate required fields
    if (!walletAddress || !alias) {
      return res.status(400).json({
        success: false,
        error: 'Wallet address and alias are required'
      });
    }

    // Validate wallet address
    if (!isValidAddress(walletAddress)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid wallet address format'
      });
    }

    // Validate alias
    if (!isValidAlias(alias)) {
      return res.status(400).json({
        success: false,
        error: 'Alias must be 3-20 characters and contain only letters, numbers, underscores, and hyphens'
      });
    }

    // Validate bio length
    if (bio && bio.length > 500) {
      return res.status(400).json({
        success: false,
        error: 'Bio must be less than 500 characters'
      });
    }

    // Validate IPFS hash if provided
    if (ipfsHash) {
      if (!isValidIPFSHash(ipfsHash)) {
        return res.status(400).json({
          success: false,
          error: 'Invalid IPFS hash format'
        });
      }
      
      // Validate IPFS image is accessible
      const isValidImage = await validateIPFSImage(ipfsHash);
      if (!isValidImage) {
        return res.status(400).json({
          success: false,
          error: 'IPFS image is not accessible or invalid'
        });
      }
    }

    // Check if alias is available (call blockchain)
    try {
      const aliasCheck = await makeBlockchainRequest(`/api/contracts/profile/alias/${alias}/available`);
      if (!aliasCheck.available) {
        return res.status(409).json({
          success: false,
          error: 'Alias is already taken'
        });
      }
    } catch (error) {
      console.error('Error checking alias availability:', error);
      // Continue with profile creation if alias check fails
    }

    // Store profile on blockchain via smart contract
    const profileData = {
      walletAddress,
      alias,
      bio: bio || '',
      ipfsHash: ipfsHash || '',
      lastUpdated: Math.floor(Date.now() / 1000)
    };

    const result = await makeBlockchainRequest('/api/contracts/profile/set', 'POST', profileData);

    if (!result || !result.success) {
      throw new Error(result?.error || 'Failed to store profile on blockchain');
    }

    res.json({
      success: true,
      message: 'Profile saved successfully on blockchain',
      profile: profileData,
      transactionId: result.transactionId
    });
  } catch (error) {
    console.error('Error saving profile:', error);
    res.status(500).json({
      success: false,
      error: `Failed to save profile: ${error.message}`
    });
  }
});

// GET /api/profiles/alias/:alias/available - Check if alias is available
router.get('/alias/:alias/available', async (req, res) => {
  try {
    const { alias } = req.params;

    if (!isValidAlias(alias)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid alias format'
      });
    }

    // Check alias availability on blockchain
    const result = await makeBlockchainRequest(`/api/contracts/profile/alias/${alias}/available`);

    res.json({
      success: true,
      available: result.available
    });
  } catch (error) {
    console.error('Error checking alias availability:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to check alias availability'
    });
  }
});

// GET /api/profiles/search/:query - Search profiles by alias
router.get('/search/:query', async (req, res) => {
  try {
    const { query } = req.params;
    const limit = parseInt(req.query.limit) || 10;

    if (!query || query.length < 2) {
      return res.status(400).json({
        success: false,
        error: 'Search query must be at least 2 characters'
      });
    }

    // Search profiles on blockchain
    const result = await makeBlockchainRequest(`/api/contracts/profile/search/${encodeURIComponent(query)}?limit=${limit}`);

    res.json({
      success: true,
      results: result.profiles || [],
      total: result.total || 0
    });
  } catch (error) {
    console.error('Error searching profiles:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to search profiles'
    });
  }
});

// POST /api/profiles/ipfs/upload - Upload image to IPFS using Pinata
router.post('/ipfs/upload', async (req, res) => {
  try {
    const { imageData, fileName } = req.body;

    if (!imageData) {
      return res.status(400).json({
        success: false,
        error: 'Image data is required'
      });
    }

    // Convert base64 to buffer
    let imageBuffer;
    if (imageData.startsWith('data:')) {
      const base64Data = imageData.split(',')[1];
      imageBuffer = Buffer.from(base64Data, 'base64');
    } else {
      imageBuffer = Buffer.from(imageData, 'base64');
    }

    // Create form data for Pinata
    const FormData = require('form-data');
    const formData = new FormData();
    formData.append('file', imageBuffer, fileName || 'profile-image.jpg');

    const metadata = JSON.stringify({
      name: fileName || 'Profile Image',
      keyvalues: {
        type: 'profile-image',
        uploadedAt: new Date().toISOString()
      }
    });
    formData.append('pinataMetadata', metadata);

    const pinataOptions = JSON.stringify({
      cidVersion: 1
    });
    formData.append('pinataOptions', pinataOptions);

    const uploadResponse = await axios.post(
      'https://api.pinata.cloud/pinning/pinFileToIPFS',
      formData,
      {
        headers: {
          'Authorization': `Bearer ${PINATA_JWT}`,
          ...formData.getHeaders()
        },
        timeout: 30000 // 30 seconds for file upload
      }
    );

    const ipfsHash = uploadResponse.data.IpfsHash;
    const imageUrl = `https://gateway.pinata.cloud/ipfs/${ipfsHash}`;

    res.json({
      success: true,
      hash: ipfsHash,
      url: imageUrl
    });
  } catch (error) {
    console.error('Error uploading to IPFS:', error);
    res.status(500).json({
      success: false,
      error: `Failed to upload image to IPFS: ${error.message}`
    });
  }
});

// DELETE /api/profiles/:address - Delete profile from blockchain
router.delete('/:address', async (req, res) => {
  try {
    const { address } = req.params;

    if (!isValidAddress(address)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid wallet address format'
      });
    }

    // Delete profile from blockchain
    const result = await makeBlockchainRequest(`/api/contracts/profile/delete/${address}`, 'DELETE');

    res.json({
      success: true,
      message: 'Profile deleted successfully',
      transactionId: result.transactionId
    });
  } catch (error) {
    console.error('Error deleting profile:', error);
    res.status(500).json({
      success: false,
      error: `Failed to delete profile: ${error.message}`
    });
  }
});

module.exports = router;