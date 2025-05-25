import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import profileService from '../../../services/api/profileService';
import contractService from '../../../services/api/contractService';

// Production or dev API URLs - matches Explorer.js
const PROD_API_URL = 'https://globalcoyn.com/api';
const DEV_API_URL = 'http://localhost:8001/api';

// Environment detection (matching walletService.js and Explorer.js)
const ENV_OVERRIDE = localStorage.getItem('gcn_environment');
const isProduction = ENV_OVERRIDE === 'production' || 
                    process.env.REACT_APP_ENV === 'production' || 
                    window.location.hostname === 'globalcoyn.com';

// Primary API URL with same logic as Explorer.js
const API_BASE_URL = ENV_OVERRIDE === 'development' ? DEV_API_URL :
                    ENV_OVERRIDE === 'production' ? PROD_API_URL :
                    process.env.REACT_APP_API_URL || 
                    (isProduction ? PROD_API_URL : DEV_API_URL);

const WalletDetails = () => {
  const { walletAddress } = useParams();
  const navigate = useNavigate();
  const [walletInfo, setWalletInfo] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [profile, setProfile] = useState(null);
  const [contracts, setContracts] = useState([]);
  const [miningHistory, setMiningHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Load wallet data when component mounts
    loadWalletData();
  }, [walletAddress]);

  const loadWalletData = async () => {
    if (!walletAddress) {
      setError('No wallet address provided');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Fetch wallet balance
      console.log('Fetching wallet data from:', `${API_BASE_URL}/wallet/balance/${walletAddress}`);
      const walletResponse = await axios.get(`${API_BASE_URL}/wallet/balance/${walletAddress}`);
      
      // Fetch wallet transactions
      console.log('Fetching wallet transactions from:', `${API_BASE_URL}/wallet/transactions/${walletAddress}`);
      const txResponse = await axios.get(`${API_BASE_URL}/wallet/transactions/${walletAddress}`);
      
      // Fetch wallet profile
      console.log('Fetching wallet profile for:', walletAddress);
      const profileResponse = await profileService.getProfile(walletAddress);
      if (profileResponse.success && profileResponse.profile) {
        setProfile(profileResponse.profile);
      } else {
        setProfile(null);
      }
      
      // Fetch wallet contracts
      try {
        console.log('Fetching wallet contracts for:', walletAddress);
        const contractsResponse = await contractService.getContractsByCreator(walletAddress);
        if (contractsResponse && contractsResponse.length > 0) {
          setContracts(contractsResponse);
        } else {
          setContracts([]);
        }
      } catch (contractError) {
        console.error('Error fetching contracts:', contractError);
        setContracts([]);
      }
      
      // Fetch mining history
      try {
        console.log('Fetching mining history for:', walletAddress);
        // First try to get mining stats
        const miningStatsResponse = await axios.get(`${API_BASE_URL}/wallet/mining-stats/${walletAddress}`);
        
        if (miningStatsResponse.data && miningStatsResponse.data.recent_blocks && Array.isArray(miningStatsResponse.data.recent_blocks)) {
          setMiningHistory(miningStatsResponse.data.recent_blocks);
        } else {
          // If no recent_blocks field, try to get blockchain data to find blocks mined by this wallet
          const chainResponse = await axios.get(`${API_BASE_URL}/blockchain/chain`);
          
          if (chainResponse.data && chainResponse.data.chain && Array.isArray(chainResponse.data.chain)) {
            // Filter blocks where this wallet is the recipient of mining rewards
            const minedBlocks = chainResponse.data.chain.filter(block => {
              if (!block.transactions || !Array.isArray(block.transactions)) return false;
              
              // Look for mining reward transactions (sender = "0")
              return block.transactions.some(tx => 
                tx.sender === "0" && tx.recipient === walletAddress
              );
            });
            
            // Sort by most recent first
            minedBlocks.sort((a, b) => b.timestamp - a.timestamp);
            
            setMiningHistory(minedBlocks);
          } else {
            setMiningHistory([]);
          }
        }
      } catch (miningError) {
        console.error('Error fetching mining history:', miningError);
        setMiningHistory([]);
      }
      
      if (walletResponse.data) {
        // Handle different API response formats
        let balance = "Unknown";
        if (walletResponse.data && walletResponse.data.balance !== undefined) {
          balance = walletResponse.data.balance;
        } else if (walletResponse.data && walletResponse.data.success && walletResponse.data.balance !== undefined) {
          balance = walletResponse.data.balance;
        }
        
        setWalletInfo({
          address: walletAddress,
          balance: balance,
          last_updated: new Date().toISOString()
        });
      } else {
        setError('Invalid wallet data format from API');
      }
      
      if (txResponse.data && txResponse.data.transactions) {
        setTransactions(txResponse.data.transactions);
      } else {
        // If no transactions endpoint or empty response, create an empty array
        setTransactions([]);
      }
    } catch (error) {
      console.error('Error loading wallet data:', error);
      setError('Failed to load wallet data. Please try again later.');
      
      // Try fallback node with opposite environment
      try {
        // If we're in production, fallback to dev and vice versa
        const fallbackUrl = isProduction ? 'http://localhost:8001/api' : 'https://globalcoyn.com/api';
        console.log('Trying fallback:', `${fallbackUrl}/wallet/balance/${walletAddress}`);
        const fallbackResponse = await axios.get(`${fallbackUrl}/wallet/balance/${walletAddress}`);
        
        if (fallbackResponse.data) {
          // Handle different API response formats for fallback
          let balance = "Unknown";
          if (fallbackResponse.data && fallbackResponse.data.balance !== undefined) {
            balance = fallbackResponse.data.balance;
          } else if (fallbackResponse.data && fallbackResponse.data.success && fallbackResponse.data.balance !== undefined) {
            balance = fallbackResponse.data.balance;
          }
          
          setWalletInfo({
            address: walletAddress,
            balance: balance,
            last_updated: new Date().toISOString()
          });
          
          // Try to get transactions from fallback
          try {
            const fallbackTxResponse = await axios.get(`${fallbackUrl}/wallet/transactions/${walletAddress}`);
            if (fallbackTxResponse.data && fallbackTxResponse.data.transactions) {
              setTransactions(fallbackTxResponse.data.transactions);
            }
          } catch (txError) {
            console.error('Fallback node transaction fetch failed:', txError);
          }
          
          setError(null); // Clear error if fallback was successful
        }
      } catch (fallbackError) {
        console.error('Fallback node also failed:', fallbackError);
      }
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return 'Unknown';
    try {
      // The API returns UNIX timestamps in seconds, not milliseconds
      // If timestamp is already very large (> 10^12), it's likely in milliseconds
      // Otherwise, assume it's in seconds and convert to milliseconds
      const timeMs = typeof timestamp === 'number' && timestamp < 10000000000 ? 
                     timestamp * 1000 : timestamp;
      const date = new Date(timeMs);
      return date.toLocaleString();
    } catch (e) {
      console.error('Error formatting timestamp:', timestamp, e);
      return 'Invalid date';
    }
  };

  const truncateHash = (hash) => {
    if (!hash) return 'Unknown';
    return `${hash.substring(0, 6)}...${hash.substring(hash.length - 6)}`;
  };

  const viewBlockDetails = (blockHash) => {
    navigate(`/app/explorer/block/${blockHash}`);
  };
  
  const viewWalletDetails = (address) => {
    if (address !== walletAddress) {
      navigate(`/app/explorer/address/${address}`);
    }
  };

  const viewTransactionDetails = (transactionId) => {
    navigate(`/app/explorer/transaction/${transactionId}`);
  };

  const goBack = () => {
    navigate('/app/explorer');
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col space-y-0 mb-4 px-6 pt-6">
        <button
          onClick={goBack}
          className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 mb-4"
          style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Explorer
        </button>
      </div>
      
      {error && (
        <div className="border-t border-b border-red-400 text-red-700 px-4 py-3 relative" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
          <strong className="font-bold">Error:</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}
      
      {loading ? (
        <div className="flex justify-center items-center p-10">
          <div className="text-lg text-gray-500 dark:text-gray-400">Loading wallet data...</div>
        </div>
      ) : walletInfo ? (
        <div className="bg-white dark:bg-gray-800 overflow-hidden">
          {/* Wallet Header */}
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 mb-0 mt-4">
            <div className="flex items-start space-x-4">
              {/* Profile Picture */}
              <div className="flex-shrink-0">
                <img
                  src={profile?.imageUrl || profileService.getDefaultAvatar(walletAddress)}
                  alt={profile?.alias || 'Wallet Avatar'}
                  className="w-16 h-16 rounded-full border-2 border-gray-200 dark:border-gray-600"
                  onError={(e) => {
                    e.target.src = profileService.getDefaultAvatar(walletAddress);
                  }}
                />
              </div>
              
              {/* Profile Info */}
              <div className="flex-grow">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-1 text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                  {profile?.alias || 'Anonymous Wallet'}
                </h2>
                
                {/* Wallet Address with Copy Button */}
                <div className="flex items-center space-x-2 mb-2">
                  <div className="font-mono text-sm text-orange-500 dark:text-orange-400 break-all">
                    {walletInfo.address}
                  </div>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(walletInfo.address);
                      // Could add a toast notification here
                    }}
                    className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                    title="Copy address"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </button>
                </div>
                
                {profile?.bio && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                    {profile.bio}
                  </p>
                )}
                
                {/* Balance and Transaction Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-3">
                  {/* Balance */}
                  <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg px-4 py-3">
                    <div className="text-xs font-medium text-green-700 dark:text-green-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      Balance
                    </div>
                    <div className="text-lg font-bold text-green-600 dark:text-green-400 mt-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      {typeof walletInfo.balance === 'number' ? walletInfo.balance.toFixed(8) : walletInfo.balance} GCN
                    </div>
                  </div>
                  
                  {/* Total Received */}
                  <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg px-4 py-3">
                    <div className="text-xs font-medium text-blue-700 dark:text-blue-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      Total Received
                    </div>
                    <div className="text-lg font-bold text-blue-600 dark:text-blue-400 mt-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      {transactions.reduce((acc, tx) => tx.recipient === walletInfo.address ? acc + (typeof tx.amount === 'number' ? tx.amount : 0) : acc, 0).toFixed(8)} GCN
                    </div>
                  </div>
                  
                  {/* Total Sent */}
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3">
                    <div className="text-xs font-medium text-red-700 dark:text-red-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      Total Sent
                    </div>
                    <div className="text-lg font-bold text-red-600 dark:text-red-400 mt-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      {transactions.reduce((acc, tx) => tx.sender === walletInfo.address ? acc + (typeof tx.amount === 'number' ? tx.amount : 0) : acc, 0).toFixed(8)} GCN
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          
          {/* Transaction History */}
          <div className="border-t border-gray-300 dark:border-gray-700">
            <div className="px-6 py-1 border-b border-gray-200 dark:border-gray-700 mb-0 mt-4">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>
                Transaction History ({transactions.length})
              </h3>
            </div>
            
            {transactions && transactions.length > 0 ? (
              <div className="overflow-x-auto p-0 mt-0">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        Transaction ID
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        Type
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        Counterparty
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        Amount
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        Timestamp
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {transactions.map((tx, index) => {
                      // Determine if this wallet is sender or recipient
                      const isSender = tx.sender === walletInfo.address;
                      const counterparty = isSender ? tx.recipient : tx.sender;
                      const txType = isSender ? 'Sent' : 'Received';
                      
                      return (
                        <tr key={tx.id || tx.tx_hash || tx.hash || `tx-${index}`}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <div 
                              className="font-mono text-orange-500 dark:text-orange-400 truncate max-w-xs cursor-pointer hover:underline"
                              onClick={() => {
                                const txId = tx.id || tx.tx_hash || tx.hash;
                                if (txId && !txId.startsWith('tx-')) {
                                  viewTransactionDetails(txId);
                                }
                              }}
                            >
                              {truncateHash(tx.id || tx.tx_hash || tx.hash || `tx-${index}`)}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              isSender ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                            }`}>
                              {txType}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <div 
                              className="truncate max-w-xs text-blue-500 dark:text-blue-400 cursor-pointer hover:underline"
                              onClick={() => viewWalletDetails(counterparty)}
                            >
                              {truncateHash(counterparty)}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                            {typeof tx.amount === 'number' ? tx.amount.toFixed(8) : tx.amount} GCN
                            {isSender ? ` (Fee: ${typeof tx.fee === 'number' ? tx.fee.toFixed(8) : tx.fee || '0.00000000'} GCN)` : ''}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                            {formatTime(tx.timestamp)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                No transactions found for this wallet
              </div>
            )}
          </div>
          
          {/* Contracts Section */}
          <div className="border-t border-gray-300 dark:border-gray-700">
            <div className="px-6 py-1 border-b border-gray-200 dark:border-gray-700 mb-0 mt-4">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>
                Smart Contracts ({contracts.length})
              </h3>
            </div>
            
            {contracts && contracts.length > 0 ? (
              <div className="overflow-x-auto p-0 mt-0">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        Contract Address
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        Name
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        Type
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        Created
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {contracts.map((contract, index) => (
                      <tr key={contract.address || `contract-${index}`}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div 
                            className="font-mono text-orange-500 dark:text-orange-400 truncate max-w-xs cursor-pointer hover:underline"
                            onClick={() => navigate(`/app/contracts/${contract.address}`)}
                          >
                            {truncateHash(contract.address)}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                          {contract.name || 'Unnamed Contract'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
                            {contract.contractType || 'Smart Contract'}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                          {formatTime(contract.createdAt || contract.timestamp)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                No smart contracts created by this wallet
              </div>
            )}
          </div>
          
          {/* Mining History Section */}
          <div className="border-t border-gray-300 dark:border-gray-700">
            <div className="px-6 py-1 border-b border-gray-200 dark:border-gray-700 mb-0 mt-4">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>
                Mining History ({miningHistory.length})
              </h3>
            </div>
            
            {miningHistory && miningHistory.length > 0 ? (
              <div className="overflow-x-auto p-0 mt-0">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        Block Hash
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        Block Height
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        Reward
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        Timestamp
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {miningHistory.map((block, index) => {
                      // Find mining reward transaction for this wallet in the block
                      const miningRewardTx = block.transactions && Array.isArray(block.transactions) 
                        ? block.transactions.find(tx => tx.sender === "0" && tx.recipient === walletAddress)
                        : null;
                      
                      // Get reward amount from transaction or default to 50
                      const rewardAmount = miningRewardTx ? miningRewardTx.amount : 50;
                      
                      return (
                        <tr key={block.hash || `mining-${index}`}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <div 
                              className="font-mono text-orange-500 dark:text-orange-400 truncate max-w-xs cursor-pointer hover:underline"
                              onClick={() => navigate(`/app/explorer/block/${block.hash}`)}
                            >
                              {truncateHash(block.hash)}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                            {block.index || 'Unknown'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
                              +{typeof rewardAmount === 'number' ? rewardAmount.toFixed(2) : rewardAmount} GCN
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                            {formatTime(block.timestamp)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                No mining rewards found for this wallet
              </div>
            )}
          </div>
          
        </div>
      ) : (
        <div className="flex justify-center items-center p-10">
          <div className="text-lg text-gray-500 dark:text-gray-400">No wallet found with address: {walletAddress}</div>
        </div>
      )}
    </div>
  );
};

export default WalletDetails;