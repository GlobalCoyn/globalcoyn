import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import networkService from '../../services/api/networkService';
import walletService from '../../services/api/walletService';
import profileService from '../../services/api/profileService';
import DashboardHeader from './components/DashboardHeader';
import './Dashboard.css';

const Dashboard = () => {
  const navigate = useNavigate();
  
  // State for blockchain and network data
  const [blockchainInfo, setBlockchainInfo] = useState(null);
  const [networkStats, setNetworkStats] = useState(null);
  const [walletBalance, setWalletBalance] = useState(null);
  const [miningStatus, setMiningStatus] = useState({ status: 'stopped' });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [allTransactions, setAllTransactions] = useState([]);
  const [mempoolStats, setMempoolStats] = useState(null);
  const [hasWallet, setHasWallet] = useState(false);
  const [profile, setProfile] = useState(null);
  const [currentWallet, setCurrentWallet] = useState(null);
  
  // State for transaction modal
  const [isTransactionModalOpen, setIsTransactionModalOpen] = useState(false);

  // Header action handlers
  const handleSendGCN = () => {
    navigate('/app/wallet');
  };

  const handleCreateWallet = () => {
    navigate('/app/wallet');
  };

  const handleImportWallet = () => {
    navigate('/app/wallet');
  };

  const handleBack = () => {
    navigate(-1); // Go back to previous page
  };

  // Get environment information
  const { isProduction } = networkService.getApiUrls();

  // Format large numbers with commas
  const formatNumber = (num) => {
    return num ? num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",") : '0';
  };

  // State for nodes data
  const [knownNodesData, setKnownNodesData] = useState(null);

  // Load dashboard data
  const loadDashboardData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Load data in parallel
      const [blockchainRes, statsRes, statusRes, nodesRes, allTxRes, mempoolRes] = await Promise.all([
        networkService.getBlockchainInfo(),
        networkService.getNetworkStats(),
        networkService.getNetworkStatus(),
        networkService.getKnownNodes(),
        axios.get(`${networkService.getApiUrls().primary}/blockchain/chain`), // Get all blockchain transactions
        axios.get(`${networkService.getApiUrls().primary}/blockchain/mempool`) // Get mempool stats
      ]);
      
      // Current wallet (if any)
      const currentWalletAddress = walletService.getCurrentWallet();
      setCurrentWallet(currentWalletAddress);
      setHasWallet(!!currentWalletAddress);
      
      let balanceRes = null;
      let txRes = null;
      let profileRes = null;
      
      if (currentWalletAddress) {
        // Use axios to get ALL transactions directly from the API like WalletDetails does
        const API_BASE_URL = networkService.getApiUrls().primary;
        [balanceRes, txRes, profileRes] = await Promise.all([
          walletService.getBalance(currentWalletAddress),
          axios.get(`${API_BASE_URL}/wallet/transactions/${currentWalletAddress}`),
          profileService.getProfile(currentWalletAddress)
        ]);
      }
      
      // Process all blockchain transactions
      if (allTxRes && allTxRes.data && allTxRes.data.chain) {
        const allTxs = allTxRes.data.chain.reduce((acc, block) => {
          if (block.transactions && Array.isArray(block.transactions)) {
            return acc.concat(block.transactions);
          }
          return acc;
        }, []);
        setAllTransactions(allTxs);
      }

      // Process mempool stats
      if (mempoolRes && mempoolRes.data) {
        setMempoolStats(mempoolRes.data);
      }

      console.log('Dashboard data loaded:', {
        blockchain: blockchainRes,
        stats: statsRes,
        status: statusRes,
        nodes: nodesRes,
        balance: balanceRes,
        transactions: txRes,
        allTransactions: allTxRes?.data,
        mempool: mempoolRes?.data
      });
      
      setBlockchainInfo(blockchainRes);
      setNetworkStats(statsRes);
      setKnownNodesData(nodesRes);
      
      // Extract mining status from blockchain info or network status
      const isMining = blockchainInfo?.is_mining || statusRes?.mining || false;
      setMiningStatus({
        status: isMining ? 'mining' : 'stopped',
        startTime: isMining ? blockchainInfo?.mining_since || new Date().toISOString() : null
      });
      
      if (balanceRes) {
        setWalletBalance(balanceRes);
      }
      
      if (txRes && txRes.data && txRes.data.transactions) {
        setTransactions(txRes.data.transactions);
      } else {
        setTransactions([]);
      }
      
      if (profileRes && profileRes.success && profileRes.profile) {
        setProfile(profileRes.profile);
      } else {
        setProfile(null);
      }
      
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Calculate total nodes (known nodes + dev frontend node)
  const getTotalNodeCount = () => {
    // In development mode, we have existing nodes plus the dev frontend node
    if (!isProduction) {
      // Use known nodes count from API response
      const knownNodesCount = knownNodesData?.nodes?.length || 0;
      console.log('Development mode node count calculation:', { 
        knownNodes: knownNodesCount,
        frontendNode: 1,
        total: knownNodesCount + 1
      });
      
      // For development, we should show 5 nodes (4 known nodes + frontend node)
      return (knownNodesCount > 0) ? knownNodesCount + 1 : 5;
    } else if (blockchainInfo) {
      // In production, use the node_count from blockchain info
      return blockchainInfo.node_count || 0;
    } else {
      return 'Unknown';
    }
  };
  
  // Format balance with 2 decimal places
  const formatBalance = (balance) => {
    if (balance === null || balance === undefined) return '0.00';
    return parseFloat(balance).toFixed(2);
  };
  
  // Format date to readable format
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  // Format time like WalletDetails does
  const formatTime = (timestamp) => {
    if (!timestamp) return 'Unknown';
    try {
      const timeMs = typeof timestamp === 'number' && timestamp < 10000000000 ? 
                     timestamp * 1000 : timestamp;
      const date = new Date(timeMs);
      return date.toLocaleString();
    } catch (e) {
      console.error('Error formatting timestamp:', timestamp, e);
      return 'Invalid date';
    }
  };

  // Truncate hash like WalletDetails does
  const truncateHash = (hash) => {
    if (!hash) return 'Unknown';
    return `${hash.substring(0, 6)}...${hash.substring(hash.length - 6)}`;
  };

  // Navigation functions
  const viewTransactionDetails = (transactionId) => {
    navigate(`/app/explorer/transaction/${transactionId}`);
  };

  const viewWalletDetails = (address) => {
    if (address !== currentWallet) {
      navigate(`/app/explorer/address/${address}`);
    }
  };
  
  // Handle mining button click
  const toggleMining = async () => {
    try {
      if (miningStatus.status === 'mining') {
        // Stop mining
        const result = await fetch(`${networkService.getApiUrls().primary}/mining/stop`, { method: 'POST' });
        if (result.ok) {
          setMiningStatus({
            status: 'stopped',
            startTime: null
          });
        }
      } else {
        // Start mining
        const result = await fetch(`${networkService.getApiUrls().primary}/mining/start`, { method: 'POST' });
        if (result.ok) {
          setMiningStatus({
            status: 'mining',
            startTime: new Date().toISOString()
          });
        }
      }
      
      // Refresh dashboard data to update the UI
      setTimeout(() => loadDashboardData(), 1000);
      
    } catch (err) {
      console.error('Mining toggle error:', err);
      setError(`Failed to ${miningStatus.status === 'mining' ? 'stop' : 'start'} mining`);
    }
  };
  
  // Load data on component mount and set up polling
  useEffect(() => {
    loadDashboardData();
    
    // Set up polling to refresh data every 30 seconds
    const interval = setInterval(() => {
      loadDashboardData();
    }, 30000);
    
    // Clean up on unmount
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div className="dashboard">
      <DashboardHeader 
        onSendGCN={handleSendGCN}
        onCreateWallet={handleCreateWallet}
        onImportWallet={handleImportWallet}
        onBack={handleBack}
        hasWallet={hasWallet}
        blockchainInfo={blockchainInfo}
        walletBalance={walletBalance}
        networkStats={networkStats}
        allTransactions={allTransactions}
        mempoolStats={mempoolStats}
      />
      
      {/* Error Message */}
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
      
      
      {/* Current Wallet Profile */}
      {currentWallet && (
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4">
            <div className="flex items-start space-x-4">
              {/* Profile Picture */}
              <div className="flex-shrink-0">
                <img
                  src={profile?.imageUrl || profileService.getDefaultAvatar(currentWallet)}
                  alt={profile?.alias || 'Wallet Avatar'}
                  className="w-16 h-16 rounded-full border-2 border-gray-200 dark:border-gray-600"
                  onError={(e) => {
                    e.target.src = profileService.getDefaultAvatar(currentWallet);
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
                    {currentWallet}
                  </div>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(currentWallet);
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
                      {formatBalance(walletBalance?.balance)} GCN
                    </div>
                  </div>
                  
                  {/* Total Received */}
                  <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg px-4 py-3">
                    <div className="text-xs font-medium text-blue-700 dark:text-blue-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      Total Received
                    </div>
                    <div className="text-lg font-bold text-blue-600 dark:text-blue-400 mt-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      {transactions.reduce((acc, tx) => tx.recipient === currentWallet ? acc + (typeof tx.amount === 'number' ? tx.amount : 0) : acc, 0).toFixed(8)} GCN
                    </div>
                  </div>
                  
                  {/* Total Sent */}
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3">
                    <div className="text-xs font-medium text-red-700 dark:text-red-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      Total Sent
                    </div>
                    <div className="text-lg font-bold text-red-600 dark:text-red-400 mt-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      {transactions.reduce((acc, tx) => tx.sender === currentWallet ? acc + (typeof tx.amount === 'number' ? tx.amount : 0) : acc, 0).toFixed(8)} GCN
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Recent Transactions */}
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
                  const isSender = tx.sender === currentWallet;
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
            {isLoading ? 'Loading transactions...' : 'No transactions found for this wallet'}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;