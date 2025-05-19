import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import networkService from '../services/networkService';
import walletService from '../services/walletService';

const Dashboard = () => {
  // State for blockchain and network data
  const [blockchainInfo, setBlockchainInfo] = useState(null);
  const [networkStats, setNetworkStats] = useState(null);
  const [walletBalance, setWalletBalance] = useState(null);
  const [miningStatus, setMiningStatus] = useState({ status: 'stopped' });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [transactions, setTransactions] = useState([]);
  
  // State for transaction modal
  const [isTransactionModalOpen, setIsTransactionModalOpen] = useState(false);

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
      const [blockchainRes, statsRes, statusRes, nodesRes] = await Promise.all([
        networkService.getBlockchainInfo(),
        networkService.getNetworkStats(),
        networkService.getNetworkStatus(),
        networkService.getKnownNodes()
      ]);
      
      // Current wallet (if any)
      const currentWallet = walletService.getCurrentWallet();
      let balanceRes = null;
      let txRes = null;
      
      if (currentWallet) {
        [balanceRes, txRes] = await Promise.all([
          walletService.getBalance(currentWallet),
          walletService.getTransactions(currentWallet, 1, 5) // First 5 transactions
        ]);
      }
      
      console.log('Dashboard data loaded:', {
        blockchain: blockchainRes,
        stats: statsRes,
        status: statusRes,
        nodes: nodesRes,
        balance: balanceRes,
        transactions: txRes
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
      
      if (txRes && txRes.transactions) {
        setTransactions(txRes.transactions);
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
    <div className="space-y-0">
      <div className="flex flex-col space-y-0 mb-4 px-6">
        <div className="flex items-center justify-between">
          <div className="w-full">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Dashboard</h1>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Network Mode: <span className="font-medium">{!isProduction ? 'Development' : 'Production'}</span>
              {lastUpdated && (
                <span className="ml-4 inline-flex items-center">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                  <button
                    className="ml-2 text-gray-500 dark:text-gray-400 inline-flex items-center"
                    onClick={loadDashboardData}
                    disabled={isLoading}
                    style={{ marginTop: '-1px' }}
                  >
                    {isLoading ? (
                      <svg className="animate-spin h-3.5 w-3.5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    ) : (
                      <svg className="h-3.5 w-3.5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    )}
                  </button>
                </span>
              )}
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <button 
              className="btn-primary flex items-center text-xs py-1 px-3 whitespace-nowrap"
              onClick={() => setIsTransactionModalOpen(true)}
            >
              Send GCN
            </button>
            
            <Link 
              to="/app/wallet" 
              className="btn-secondary flex items-center text-xs py-1 px-3 whitespace-nowrap"
            >
              Create/Import Wallet
            </Link>
          </div>
        </div>
      </div>
      
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
      
      {/* Development Mode Alert */}
      {!isProduction && (
        <div className="border-t border-b border-blue-400 bg-blue-50 text-blue-700 px-4 py-3 relative dark:bg-blue-900 dark:bg-opacity-20 dark:text-blue-300">
          <strong className="font-bold">Development Mode:</strong>
          <span className="block sm:inline"> You are connected to the development blockchain network. Your browser is acting as a node.</span>
        </div>
      )}
      
      {/* Stats Overview */}
      <div className="stats-container">
        {/* Wallet Balance */}
        <div className="stats-box">
          <h3 className="stats-title">Wallet Balance</h3>
          <p className={`stats-value ${isLoading ? 'text-gray-500' : 'text-green-600'}`}>
            {isLoading ? 'Loading...' : `${formatBalance(walletBalance?.balance)} GCN`}
          </p>
          {walletBalance?.source === 'mock' && (
            <p className="text-xs text-gray-500 mt-1">(Simulated for development)</p>
          )}
        </div>
        
        {/* Blockchain Height */}
        <div className="stats-box">
          <h3 className="stats-title">Blockchain Height</h3>
          <p className="stats-value">
            {isLoading ? 'Loading...' : (
              blockchainInfo ? formatNumber(blockchainInfo.chain_length) : '0'
            )}
          </p>
          {blockchainInfo?.source === 'mock' && (
            <p className="text-xs text-gray-500 mt-1">(Simulated for development)</p>
          )}
        </div>
        
        {/* Mining Status */}
        <div className="stats-box">
          <h3 className="stats-title">Mining Status</h3>
          <p className={`stats-value ${miningStatus.status === 'mining' ? 'text-green-600' : 'text-red-600'}`}>
            {miningStatus.status === 'mining' ? 'Mining Active' : 'Not Mining'}
          </p>
          {miningStatus.status === 'mining' && miningStatus.startTime && (
            <p className="text-sm text-gray-500 mt-1">
              Since {formatDate(miningStatus.startTime)}
            </p>
          )}
          <button 
            className={`btn-primary mt-3 text-sm ${miningStatus.status === 'mining' ? 'bg-red-600 hover:bg-red-700' : ''}`}
            onClick={toggleMining}
          >
            {miningStatus.status === 'mining' ? 'Stop Mining' : 'Start Mining'}
          </button>
        </div>
        
        {/* Network Nodes */}
        <div className="stats-box">
          <h3 className="stats-title">Network Nodes</h3>
          <p className="stats-value">
            {isLoading ? 'Loading...' : formatNumber(getTotalNodeCount())}
          </p>
          {!isProduction && (
            <p className="text-xs text-gray-500 mt-1">
              (Including your browser node)
            </p>
          )}
        </div>
      </div>
      
      {/* No Quick Actions section, it's been moved to the header */}
      
      {/* Recent Transactions */}
      <div className="card">
        <div className="px-6 py-2 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Recent Transactions</h2>
        </div>
        <div className="p-0">
          {transactions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Date</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Type</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Amount</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {transactions.map((tx, index) => (
                    <tr key={tx.id || index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {formatDate(tx.timestamp)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          tx.type === 'sent' 
                            ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300' 
                            : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                        }`}>
                          {tx.type === 'sent' ? 'Sent' : 'Received'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {formatBalance(tx.amount)} GCN
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          tx.status === 'confirmed' 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' 
                            : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                        }`}>
                          {tx.status === 'confirmed' ? 'Confirmed' : 'Pending'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="px-6 py-4 text-gray-600 dark:text-gray-400">
              {isLoading ? 'Loading transactions...' : 'No transactions yet.'}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;