import axios from 'axios';

// Production or dev API URLs - matches Explorer.js and walletService.js
const PROD_API_URL = 'https://globalcoyn.com/api';
const DEV_API_URL = 'http://localhost:8001/api';

// Environment detection (matching walletService.js and Explorer.js)
const ENV_OVERRIDE = localStorage.getItem('gcn_environment');
const isProduction = ENV_OVERRIDE === 'production' || 
                    process.env.REACT_APP_ENV === 'production' || 
                    window.location.hostname === 'globalcoyn.com';

// Primary API URL with same logic as Explorer.js and walletService.js
const API_BASE_URL = ENV_OVERRIDE === 'development' ? DEV_API_URL :
                    ENV_OVERRIDE === 'production' ? PROD_API_URL :
                    process.env.REACT_APP_API_URL || 
                    (isProduction ? PROD_API_URL : DEV_API_URL);

// Log the configuration
console.log('Contract Service API Configuration:', {
  primaryUrl: API_BASE_URL,
  environment: isProduction ? 'production' : 'development',
  override: ENV_OVERRIDE || 'none'
});

/**
 * Contract Service for Frontend
 * Handles interaction with the smart contract API
 */
const contractService = {
  /**
   * Get available contract types
   * @returns {Promise<Array>} List of contract types
   */
  getContractTypes: async function() {
    try {
      const response = await axios.get(`${API_BASE_URL}/contracts/types`);
      
      if (response.data && response.data.status === 'success') {
        return response.data.contract_types;
      }
      
      return this.getDefaultContractTypes();
    } catch (error) {
      console.error('Error fetching contract types:', error);
      return this.getDefaultContractTypes();
    }
  },
  
  /**
   * Get all contracts on the blockchain
   * @returns {Promise<Array>} List of all contracts
   */
  getAllContracts: async function() {
    try {
      const response = await axios.get(`${API_BASE_URL}/contracts/all`);
      
      if (response.data && response.data.status === 'success') {
        return response.data.contracts;
      }
      
      return [];
    } catch (error) {
      console.error('Error fetching all contracts:', error);
      return [];
    }
  },
  
  /**
   * Get contracts created by an address
   * @param {string} creatorAddress - The creator's wallet address
   * @returns {Promise<Array>} List of contracts
   */
  getContractsByCreator: async function(creatorAddress) {
    try {
      const response = await axios.get(`${API_BASE_URL}/contracts/byCreator/${creatorAddress}`);
      
      if (response.data && response.data.status === 'success') {
        return response.data.contracts;
      }
      
      return [];
    } catch (error) {
      console.error(`Error fetching contracts for ${creatorAddress}:`, error);
      return [];
    }
  },
  
  /**
   * Deploy a token contract with fee payment
   * @param {Object} tokenData - Token contract data
   * @param {Function} sendFeeCallback - Callback function to send fee transaction
   * @returns {Promise<Object>} Deployment result
   */
  deployTokenContract: async function(tokenData, sendFeeCallback) {
    try {
      // First attempt to deploy the contract
      const response = await axios.post(`${API_BASE_URL}/contracts/templates/token`, tokenData);
      
      if (response.data && response.data.status === 'success') {
        const contractAddress = response.data.contract_address;
        
        // If we have a callback for sending the fee, use it
        if (sendFeeCallback && typeof sendFeeCallback === 'function') {
          try {
            console.log('Sending contract fee transaction');
            // Send the fee transaction
            // The fee is 100 GCN to CONTRACT_FEE_ADDRESS
            await sendFeeCallback(
              tokenData.creator,              // from address
              "1LVkyzYqPBYYhMEjxFm1dLXsFUox2gtdDr", // fee address
              100,                             // amount (100 GCN)
              0.01                             // transaction fee
            );
            console.log('Contract fee transaction sent');
          } catch (feeError) {
            console.error('Failed to send contract fee, but contract was deployed:', feeError);
            // Still return success since the contract was deployed
          }
        }
        
        return {
          success: true,
          contractAddress: contractAddress,
          message: response.data.message || 'Token contract deployed successfully. Please ensure the contract fee is paid.'
        };
      }
      
      throw new Error(response.data.message || 'Failed to deploy token contract');
    } catch (error) {
      console.error('Error deploying token contract:', error);
      throw error;
    }
  },
  
  /**
   * Deploy a crowdfunding contract with fee payment
   * @param {Object} crowdfundData - Crowdfunding contract data
   * @param {Function} sendFeeCallback - Callback function to send fee transaction
   * @returns {Promise<Object>} Deployment result
   */
  deployCrowdfundContract: async function(crowdfundData, sendFeeCallback) {
    try {
      // First attempt to deploy the contract
      const response = await axios.post(`${API_BASE_URL}/contracts/templates/crowdfunding`, crowdfundData);
      
      if (response.data && response.data.status === 'success') {
        const contractAddress = response.data.contract_address;
        
        // If we have a callback for sending the fee, use it
        if (sendFeeCallback && typeof sendFeeCallback === 'function') {
          try {
            console.log('Sending contract fee transaction');
            // Send the fee transaction
            // The fee is 100 GCN to CONTRACT_FEE_ADDRESS
            await sendFeeCallback(
              crowdfundData.creator,           // from address
              "1LVkyzYqPBYYhMEjxFm1dLXsFUox2gtdDr", // fee address
              100,                              // amount (100 GCN)
              0.01                              // transaction fee
            );
            console.log('Contract fee transaction sent');
          } catch (feeError) {
            console.error('Failed to send contract fee, but contract was deployed:', feeError);
            // Still return success since the contract was deployed
          }
        }
        
        return {
          success: true,
          contractAddress: contractAddress,
          message: response.data.message || 'Crowdfunding contract deployed successfully. Please ensure the contract fee is paid.'
        };
      }
      
      throw new Error(response.data.message || 'Failed to deploy crowdfunding contract');
    } catch (error) {
      console.error('Error deploying crowdfunding contract:', error);
      throw error;
    }
  },
  
  /**
   * Deploy a voting contract with fee payment
   * @param {Object} votingData - Voting contract data
   * @param {Function} sendFeeCallback - Callback function to send fee transaction
   * @returns {Promise<Object>} Deployment result
   */
  deployVotingContract: async function(votingData, sendFeeCallback) {
    try {
      // First attempt to deploy the contract
      const response = await axios.post(`${API_BASE_URL}/contracts/templates/voting`, votingData);
      
      if (response.data && response.data.status === 'success') {
        const contractAddress = response.data.contract_address;
        
        // If we have a callback for sending the fee, use it
        if (sendFeeCallback && typeof sendFeeCallback === 'function') {
          try {
            console.log('Sending contract fee transaction');
            // Send the fee transaction
            // The fee is 100 GCN to CONTRACT_FEE_ADDRESS
            await sendFeeCallback(
              votingData.creator,               // from address
              "1LVkyzYqPBYYhMEjxFm1dLXsFUox2gtdDr", // fee address
              100,                               // amount (100 GCN)
              0.01                               // transaction fee
            );
            console.log('Contract fee transaction sent');
          } catch (feeError) {
            console.error('Failed to send contract fee, but contract was deployed:', feeError);
            // Still return success since the contract was deployed
          }
        }
        
        return {
          success: true,
          contractAddress: contractAddress,
          message: response.data.message || 'Voting contract deployed successfully. Please ensure the contract fee is paid.'
        };
      }
      
      throw new Error(response.data.message || 'Failed to deploy voting contract');
    } catch (error) {
      console.error('Error deploying voting contract:', error);
      throw error;
    }
  },
  
  /**
   * Get contract state
   * @param {string} contractAddress - The contract address
   * @returns {Promise<Object>} Contract state
   */
  /**
   * Get a specific contract by address
   * @param {string} contractAddress - The contract address
   * @returns {Promise<Object>} Contract details
   */
  getContract: async function(contractAddress) {
    try {
      const response = await axios.get(`${API_BASE_URL}/contracts/${contractAddress}`);
      
      if (response.data && response.data.status === 'success') {
        return response.data.contract;
      }
      
      throw new Error(response.data.message || 'Failed to get contract details');
    } catch (error) {
      console.error(`Error getting contract ${contractAddress}:`, error);
      throw error;
    }
  },

  getContractState: async function(contractAddress) {
    try {
      const response = await axios.get(`${API_BASE_URL}/contracts/${contractAddress}/state`);
      
      if (response.data && response.data.status === 'success') {
        return response.data.state;
      }
      
      throw new Error(response.data.message || 'Failed to get contract state');
    } catch (error) {
      console.error(`Error getting state for contract ${contractAddress}:`, error);
      throw error;
    }
  },
  
  /**
   * Execute a contract function
   * @param {string} contractAddress - The contract address
   * @param {string} functionName - The function to execute
   * @param {Object} args - Function arguments
   * @param {string} caller - Caller's wallet address
   * @returns {Promise<Object>} Execution result
   */
  executeContract: async function(contractAddress, functionName, args, caller) {
    try {
      const response = await axios.post(`${API_BASE_URL}/contracts/${contractAddress}/execute`, {
        function: functionName,
        args: args,
        caller: caller
      });
      
      if (response.data && response.data.status === 'success') {
        return {
          success: true,
          result: response.data.result,
          message: response.data.message || 'Function executed successfully'
        };
      }
      
      throw new Error(response.data.message || 'Failed to execute contract function');
    } catch (error) {
      console.error(`Error executing function ${functionName} on contract ${contractAddress}:`, error);
      throw error;
    }
  },
  
  /**
   * Transfer tokens from a token contract
   * @param {string} contractAddress - The contract address
   * @param {string} fromAddress - Sender address
   * @param {string} toAddress - Recipient address
   * @param {number} amount - Amount to transfer
   * @returns {Promise<Object>} Transfer result
   */
  transferTokens: async function(contractAddress, fromAddress, toAddress, amount) {
    try {
      const response = await axios.post(`${API_BASE_URL}/contracts/token/${contractAddress}/transfer`, {
        from_address: fromAddress,
        to_address: toAddress,
        amount: amount
      });
      
      if (response.data && response.data.status === 'success') {
        return {
          success: true,
          transactionId: response.data.transaction_id,
          message: response.data.message || 'Tokens transferred successfully'
        };
      }
      
      throw new Error(response.data.message || 'Failed to transfer tokens');
    } catch (error) {
      console.error(`Error transferring tokens from contract ${contractAddress}:`, error);
      throw error;
    }
  },
  
  /**
   * Get default contract types when API is unavailable
   * @private
   */
  getDefaultContractTypes: function() {
    return [
      {
        type: 'TOKEN',
        name: 'Token Contract',
        description: 'Create your own custom token'
      },
      {
        type: 'CROWDFUND',
        name: 'Crowdfunding Campaign',
        description: 'Start a fundraising campaign'
      },
      {
        type: 'VOTING',
        name: 'Voting Contract',
        description: 'Create a voting system for governance'
      }
    ];
  },
  
  /**
   * Generate a transaction fee callback that uses walletService
   * @param {Object} walletService - The wallet service instance
   * @returns {Function} Callback function for sending fee transactions
   */
  createWalletServiceFeeCallback: function(walletService) {
    if (!walletService || typeof walletService.sendTransaction !== 'function') {
      console.error('Invalid wallet service provided for fee callback');
      return null;
    }
    
    // Return a function that can be used as the sendFeeCallback
    return async function(fromAddress, toAddress, amount, fee) {
      try {
        console.log(`Sending fee transaction: ${amount} GCN from ${fromAddress} to ${toAddress}`);
        // Use the wallet service to send the transaction
        const result = await walletService.sendTransaction(fromAddress, toAddress, amount, fee);
        
        console.log('Fee transaction result:', result);
        return result;
      } catch (error) {
        console.error('Error sending fee transaction:', error);
        throw error;
      }
    };
  }
};

export default contractService;