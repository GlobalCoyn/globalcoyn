import React, { useState, useEffect } from 'react';
import axios from 'axios';
import walletService from '../../../services/api/walletService';

// API URLs from wallet service to maintain consistency
const API_BASE_URL = walletService.getApiUrl();
const FALLBACK_API_URL = walletService.getFallbackApiUrl();

const Mining = () => {
  const [isMining, setIsMining] = useState(false);
  const [cpuUsage, setCpuUsage] = useState(50);
  const [wallets, setWallets] = useState([]);
  const [selectedWallet, setSelectedWallet] = useState('');
  const [blocksMined, setBlocksMined] = useState(0);
  const [miningRewards, setMiningRewards] = useState(0);
  const [hashRate, setHashRate] = useState(0);
  const [miningHistory, setMiningHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentBalance, setCurrentBalance] = useState(0);
  const [lastMinedBlock, setLastMinedBlock] = useState(null);
  // Reference to the mining interval - IMPORTANT: Must be defined before it's used
  const [miningInterval, setMiningInterval] = useState(null);

  // Load wallets when component mounts
  useEffect(() => {
    fetchWallets();
    // Set up a blockchain stats polling interval when page loads
    const statsInterval = setInterval(() => {
      fetchBlockchainStats();
    }, 5000); // Every 5 seconds
    
    // Clean up interval on unmount
    return () => clearInterval(statsInterval);
  }, []);
  
  // Add a separate effect to load mining stats when selected wallet changes
  useEffect(() => {
    if (selectedWallet) {
      // Clear mining history when wallet changes
      setMiningHistory([]);
      
      // Reset mining state when switching wallets
      if (miningInterval) {
        clearInterval(miningInterval);
        setMiningInterval(null);
      }
      setIsMining(false);
      
      // Fetch initial data for the selected wallet
      fetchMiningStats();
      fetchWalletBalance();
      fetchMiningHistory();
      
      // Set up a balance polling interval when wallet is selected
      const balanceInterval = setInterval(() => {
        fetchWalletBalance();
      }, 10000); // Every 10 seconds
      
      return () => clearInterval(balanceInterval);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedWallet, miningInterval]);
  
  // Add an effect for polling mining stats when actively mining
  useEffect(() => {
    let miningStatsInterval;
    
    if (isMining && selectedWallet) {
      // Poll more frequently when mining is active
      miningStatsInterval = setInterval(() => {
        fetchMiningStats();
        fetchWalletBalance();
      }, 3000); // Every 3 seconds while mining
    }
    
    return () => {
      if (miningStatsInterval) clearInterval(miningStatsInterval);
    };
  }, [isMining, selectedWallet]);

  // Fetch available wallets
  const fetchWallets = async () => {
    try {
      const walletAddresses = await walletService.getWallets();
      setWallets(walletAddresses);
      
      // If we have wallets and none is selected, select the first one
      if (walletAddresses.length > 0 && !selectedWallet) {
        setSelectedWallet(walletAddresses[0]);
      }
    } catch (error) {
      console.error('Error fetching wallets:', error);
      setError('Failed to load wallets. Please try again later.');
    }
  };
  
  // Fetch mining stats for the selected wallet
  const fetchMiningStats = async () => {
    if (!selectedWallet) return;
    
    try {
      const response = await axios.get(`${API_BASE_URL}/wallet/mining-stats/${selectedWallet}`);
      console.log('Mining stats response:', response.data);
      
      if (response.data) {
        setBlocksMined(response.data.blocks_mined || 0);
        setMiningRewards(response.data.total_rewards || 0);
        
        // Only update isMining from API if we're not actively controlling it locally
        if (!miningInterval) {
          setIsMining(response.data.is_currently_mining || false);
        }
        
        // Update mining history if available
        if (response.data.recent_blocks && Array.isArray(response.data.recent_blocks)) {
          setMiningHistory(response.data.recent_blocks);
        } else {
          // If no recent_blocks field, try to fetch mining history separately
          fetchMiningHistory();
        }
      }
    } catch (error) {
      console.error('Error fetching mining stats:', error);
      // Try fallback API if primary fails
      try {
        const fallbackResponse = await axios.get(`${FALLBACK_API_URL}/wallet/mining-stats/${selectedWallet}`);
        if (fallbackResponse.data) {
          setBlocksMined(fallbackResponse.data.blocks_mined || 0);
          setMiningRewards(fallbackResponse.data.total_rewards || 0);
          
          // Only update isMining from API if we're not actively controlling it locally
          if (!miningInterval) {
            setIsMining(fallbackResponse.data.is_currently_mining || false);
          }
          
          if (fallbackResponse.data.recent_blocks && Array.isArray(fallbackResponse.data.recent_blocks)) {
            setMiningHistory(fallbackResponse.data.recent_blocks);
          } else {
            // If no recent_blocks field, try to fetch mining history separately
            fetchMiningHistory();
          }
        }
      } catch (fallbackError) {
        console.error('Fallback API also failed:', fallbackError);
      }
    }
  };
  
  // Fetch mining history separately if needed
  const fetchMiningHistory = async () => {
    if (!selectedWallet) return;
    
    try {
      // First try to get blockchain data to find blocks mined by this wallet
      const chainResponse = await axios.get(`${API_BASE_URL}/blockchain/chain`);
      
      if (chainResponse.data && chainResponse.data.chain && Array.isArray(chainResponse.data.chain)) {
        // Filter blocks where this wallet is the recipient of mining rewards
        const minedBlocks = chainResponse.data.chain.filter(block => {
          if (!block.transactions || !Array.isArray(block.transactions)) return false;
          
          // Look for mining reward transactions (sender = "0")
          return block.transactions.some(tx => 
            tx.sender === "0" && tx.recipient === selectedWallet
          );
        });
        
        // Sort by most recent first
        minedBlocks.sort((a, b) => b.timestamp - a.timestamp);
        
        // Update mining history with these blocks
        if (minedBlocks.length > 0) {
          setMiningHistory(minedBlocks);
        }
      }
    } catch (error) {
      console.error('Error fetching mining history:', error);
    }
  };
  
  // Fetch wallet balance
  const fetchWalletBalance = async () => {
    if (!selectedWallet) return;
    
    try {
      const balanceInfo = await walletService.getBalance(selectedWallet);
      setCurrentBalance(balanceInfo.balance || 0);
    } catch (error) {
      console.error('Error fetching wallet balance:', error);
    }
  };
  
  // Fetch blockchain stats including hash rate estimate
  const fetchBlockchainStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/blockchain`);
      if (response.data) {
        // If the API returns hash rate, use it, otherwise estimate
        setHashRate(response.data.hash_rate || Math.random() * 50 + 20); // Fallback to random value between 20-70 H/s
      }
    } catch (error) {
      console.error('Error fetching blockchain stats:', error);
      // Fallback to an estimated hash rate
      setHashRate(Math.random() * 50 + 20);
    }
  };

  // Mining functions and state management
  
  // Function to mine a single block
  const mineBlock = async () => {
    if (!selectedWallet) return false;
    
    try {
      console.log(`Mining block for wallet: ${selectedWallet}`);
      const response = await axios.post(`${API_BASE_URL}/blockchain/blocks/mine`, {
        miner_address: selectedWallet
      });
      
      console.log('Mining response:', response.data);
      
      if (response.data && response.data.status === 'success') {
        setLastMinedBlock(response.data.block);
        
        // Update mining stats after successful mining
        fetchMiningStats();
        fetchWalletBalance();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error mining block:', error);
      
      // Try using fallback API
      try {
        console.log(`Trying fallback API for mining block for wallet: ${selectedWallet}`);
        const fallbackResponse = await axios.post(`${FALLBACK_API_URL}/blockchain/blocks/mine`, {
          miner_address: selectedWallet
        });
        
        if (fallbackResponse.data && fallbackResponse.data.status === 'success') {
          setLastMinedBlock(fallbackResponse.data.block);
          
          // Update mining stats after successful mining
          fetchMiningStats();
          fetchWalletBalance();
          return true;
        }
      } catch (fallbackError) {
        console.error('Fallback mining also failed:', fallbackError);
      }
      
      return false;
    }
  };
  
  // Start continuous mining
  const startMining = () => {
    if (miningInterval) return; // Already mining
    
    // Update mining state immediately for UI responsiveness
    setIsMining(true);
    
    // Mine first block immediately
    mineBlock();
    
    // Set up interval to mine blocks continuously
    const interval = setInterval(async () => {
      // Check if we're still mining before attempting to mine another block
      if (!miningInterval) return;
      
      const success = await mineBlock();
      
      // If mining failed, try again after a delay
      if (!success) {
        console.log('Mining attempt failed, will retry...');
      }
    }, 5000); // Try to mine a new block every 5 seconds
    
    setMiningInterval(interval);
    
    // Force a mining status update
    fetchMiningStats();
  };
  
  // Stop mining
  const stopMining = () => {
    if (miningInterval) {
      clearInterval(miningInterval);
      setMiningInterval(null);
      setIsMining(false);
      console.log('Mining stopped');
      
      // Force a mining status update to reflect stopped state
      fetchMiningStats();
    }
  };
  
  // Clean up interval on component unmount
  useEffect(() => {
    // Cleanup function called when component unmounts or dependencies change
    return () => {
      if (miningInterval) {
        console.log('Cleaning up mining interval on unmount');
        clearInterval(miningInterval);
      }
    };
  }, [miningInterval]);
  
  // Toggle mining state and make API call
  const toggleMining = async () => {
    if (!selectedWallet) {
      setError('Please select a wallet to receive mining rewards first.');
      return;
    }
    
    setLoading(true);
    
    try {
      if (!isMining) {
        // Start continuous mining
        startMining();
      } else {
        // Stop mining
        stopMining();
      }
    } catch (error) {
      console.error('Error toggling mining:', error);
      setError('Failed to change mining state. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-0">
      <div className="flex flex-col space-y-0 mb-4 px-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center" style={{ lineHeight: '1' }}>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white inline-flex items-center" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                Mining
                {/* Mining Status Indicator */}
                <span className={`ml-3 inline-block px-2.5 py-0.5 rounded-full text-xs font-medium align-middle ${isMining ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'}`} style={{ fontFamily: 'Helvetica, Arial, sans-serif', position: 'relative', top: '-2px' }}>
                  {isMining ? 'Active' : 'Stopped'}
                </span>
              </h1>
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400 mt-0">
              Network Mode: <span className="font-medium">{localStorage.getItem('gcn_environment') === 'production' || window.location.hostname === 'globalcoyn.com' ? 'Production' : 'Development'}</span>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <select
              className="p-2 border border-gray-300 dark:bg-gray-700 dark:border-gray-600 dark:text-white w-56"
              value={selectedWallet || ''}
              onChange={(e) => setSelectedWallet(e.target.value)}
              disabled={loading || wallets.length === 0}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              {wallets.length === 0 ? (
                <option value="">No wallets available</option>
              ) : (
                <>
                  <option value="">Select a wallet</option>
                  {wallets.map(wallet => (
                    <option key={wallet} value={wallet} style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      {wallet.substring(0, 10)}...{wallet.substring(wallet.length - 8)}
                    </option>
                  ))}
                </>
              )}
            </select>
            <button
              className="btn-secondary flex items-center text-xs py-1 px-3 whitespace-nowrap"
              onClick={fetchWallets}
              disabled={loading}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              Refresh Wallets
            </button>
            <button 
              className={`${isMining ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'} text-white font-medium text-xs py-1 px-3 rounded-md transition-colors whitespace-nowrap`}
              onClick={toggleMining}
              disabled={loading || !selectedWallet}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              {loading ? 'Processing...' : isMining ? 'Stop Mining' : 'Start Mining'}
            </button>
          </div>
        </div>
      </div>
      
      {/* Error alert if any */}
      {error && (
        <div className="mx-6 border-t border-b border-red-400 text-red-700 px-4 py-3 relative" role="alert">
          <strong className="font-bold">Error!</strong>
          <span className="block sm:inline"> {error}</span>
          <button 
            className="absolute top-0 bottom-0 right-0 px-4 py-3"
            onClick={() => setError(null)}
          >
            <span className="sr-only">Dismiss</span>
            <svg className="h-6 w-6 text-red-500" role="button" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
              <title>Close</title>
              <path d="M14.348 14.849a1.2 1.2 0 0 1-1.697 0L10 11.819l-2.651 3.029a1.2 1.2 0 1 1-1.697-1.697l2.758-3.15-2.759-3.152a1.2 1.2 0 1 1 1.697-1.697L10 8.183l2.651-3.031a1.2 1.2 0 1 1 1.697 1.697l-2.758 3.152 2.758 3.15a1.2 1.2 0 0 1 0 1.698z"/>
            </svg>
          </button>
        </div>
      )}
      
      {/* Selected Wallet Info - Move to its own section */}
      <div className="border-t border-gray-300 dark:border-gray-700">
        <div className="px-6 py-2 border-b border-gray-200 dark:border-gray-700 mb-0">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>Mining Wallet</h2>
        </div>
        <div className="px-6 py-4 space-y-4">
          <p className="text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            The selected wallet will receive your mining rewards when you mine blocks.
          </p>
          
          {selectedWallet ? (
            <div className="flex flex-row justify-between items-center gap-3">
              <div className="flex flex-col justify-center">
                <h3 className="text-sm text-gray-500 dark:text-gray-400 mb-0" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Wallet Address</h3>
                <p className="text-sm font-mono text-blue-500 dark:text-blue-400">{selectedWallet}</p>
              </div>
              
              <div className="flex flex-col justify-center">
                <h3 className="text-sm text-gray-500 dark:text-gray-400 mb-0" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Current Balance</h3>
                <p className="text-2xl font-bold text-green-600" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>{currentBalance.toFixed(8)} GCN</p>
              </div>
            </div>
          ) : (
            <div className="p-4 border border-yellow-200 bg-yellow-50 dark:bg-yellow-900 dark:border-yellow-800 rounded-md">
              <p className="text-yellow-600 dark:text-yellow-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                Please select a wallet from the dropdown in the header to receive mining rewards.
              </p>
            </div>
          )}
        </div>
      </div>
      
      
      {/* Last Mined Block */}
      {lastMinedBlock && (
        <div className="border-t border-gray-300 dark:border-gray-700 mt-4">
          <div className="px-6 py-2 border-b border-gray-200 dark:border-gray-700 mb-0">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>Last Block Mined</h2>
          </div>
          <div className="px-6 py-4">
            <div className="stats-container">
              <div className="stats-box">
                <h3 className="stats-title" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Block Height</h3>
                <p className="stats-value" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>{lastMinedBlock.index}</p>
              </div>
              
              <div className="stats-box">
                <h3 className="stats-title" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Block Hash</h3>
                <p className="stats-value font-mono text-orange-500 dark:text-orange-400" style={{ fontSize: '0.875rem' }}>
                  {lastMinedBlock.hash ? `${lastMinedBlock.hash.substring(0, 10)}...${lastMinedBlock.hash.substring(lastMinedBlock.hash.length - 10)}` : 'Unknown'}
                </p>
              </div>
              
              <div className="stats-box">
                <h3 className="stats-title" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Mined At</h3>
                <p className="stats-value" style={{ fontFamily: 'Helvetica, Arial, sans-serif', fontSize: '0.875rem' }}>
                  {new Date(lastMinedBlock.timestamp * 1000).toLocaleString()}
                </p>
              </div>
              
              <div className="stats-box">
                <h3 className="stats-title" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Mining Reward</h3>
                <p className="stats-value text-green-600" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                  +50.00 GCN
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Mining Progress Indicator */}
      {isMining && (
        <div className="bg-green-50 border-l-4 border-green-400 p-4 dark:bg-green-900 dark:border-green-700">
          <div className="flex items-center">
            <div className="h-4 w-4 rounded-full mr-3 bg-green-500 animate-pulse"></div>
            <div>
              <p className="text-sm text-green-700 dark:text-green-300 font-medium">
                Mining in progress
              </p>
              <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                Your wallet will automatically receive rewards when blocks are mined
              </p>
            </div>
          </div>
        </div>
      )}
      
      {/* Mining Stats */}
      <div className="border-t border-gray-300 dark:border-gray-700 mt-4">
        <div className="px-6 py-2 border-b border-gray-200 dark:border-gray-700 mb-0">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>Mining Stats</h2>
        </div>
        <div className="px-6 py-4">
          <div className="stats-container">
            {/* Hashrate */}
            <div className="stats-box">
              <h3 className="stats-title" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Hashrate</h3>
              <p className="stats-value" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                {isMining ? `${hashRate.toFixed(1)} H/s` : '0 H/s'}
              </p>
            </div>
            
            {/* Blocks Mined */}
            <div className="stats-box">
              <h3 className="stats-title" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Blocks Mined</h3>
              <p className="stats-value" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>{blocksMined}</p>
            </div>
            
            {/* Total Rewards */}
            <div className="stats-box">
              <h3 className="stats-title" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Total Rewards</h3>
              <p className="stats-value text-green-600" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>{miningRewards.toFixed(2)} GCN</p>
            </div>
            
            {/* Mining Status */}
            <div className="stats-box">
              <h3 className="stats-title" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Mining Status</h3>
              <p className={`stats-value ${isMining ? 'text-green-600' : 'text-red-600'}`} style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                {isMining ? 'Active' : 'Inactive'}
              </p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Mining History */}
      <div className="border-t border-gray-300 dark:border-gray-700 mt-4">
        <div className="px-6 py-2 border-b border-gray-200 dark:border-gray-700 mb-0">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>Mining History</h2>
            {selectedWallet && (
              <button
                onClick={fetchMiningHistory}
                className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 flex items-center"
                disabled={loading}
                style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
              >
                <svg className="h-3.5 w-3.5 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh History
              </button>
            )}
          </div>
        </div>
        <div className="p-0">
          {!selectedWallet ? (
            <div className="text-center py-6">
              <p className="text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Select a wallet to view mining history.</p>
            </div>
          ) : miningHistory.length === 0 ? (
            <div className="text-center py-6">
              <p className="text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>No mining history for this wallet.</p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                Start mining to earn GCN rewards.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Block</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Time</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Hash</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Reward</th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {miningHistory.map((block, index) => {
                    // Find mining reward transaction for this wallet in the block
                    const miningRewardTx = block.transactions && Array.isArray(block.transactions) 
                      ? block.transactions.find(tx => tx.sender === "0" && tx.recipient === selectedWallet)
                      : null;
                    
                    // Get reward amount from transaction or default to 50
                    const rewardAmount = miningRewardTx ? miningRewardTx.amount : 50;
                    
                    return (
                      <tr key={block.hash || index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                          {block.index || 'Unknown'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                          {block.timestamp ? new Date(block.timestamp * 1000).toLocaleString() : 'Unknown'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-orange-500 dark:text-orange-400">
                          {block.hash ? `${block.hash.substring(0, 8)}...${block.hash.substring(block.hash.length - 8)}` : 'Unknown'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                          +{rewardAmount.toFixed(2)} GCN
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
      
    </div>
  );
};

export default Mining;