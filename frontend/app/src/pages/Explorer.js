import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

// Production or dev API URLs
const PROD_API_URL = 'https://globalcoyn.com/api';
const DEV_API_URL = 'http://localhost:8001/api';

// Environment detection (matching walletService.js)
// 1. Check for explicit environment setting in localStorage (useful for testing)
// 2. Check for REACT_APP_ENV environment variable
// 3. Check domain name
const ENV_OVERRIDE = localStorage.getItem('gcn_environment');
const isProduction = ENV_OVERRIDE === 'production' || 
                    process.env.REACT_APP_ENV === 'production' || 
                    window.location.hostname === 'globalcoyn.com';

// Primary API URL with same logic as walletService.js
const API_BASE_URL = ENV_OVERRIDE === 'development' ? DEV_API_URL :
                    ENV_OVERRIDE === 'production' ? PROD_API_URL :
                    process.env.REACT_APP_API_URL || 
                    (isProduction ? PROD_API_URL : DEV_API_URL);

const Explorer = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [blocks, setBlocks] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Load blockchain data when component mounts
    loadBlockchainData();
  }, []);

  const loadBlockchainData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch blockchain data from the bootstrap node
      // Changed from /chain to /blockchain/chain to match the actual API endpoint
      console.log('Fetching blockchain data from:', `${API_BASE_URL}/blockchain/chain`);
      const blocksResponse = await axios.get(`${API_BASE_URL}/blockchain/chain`);
      
      if (blocksResponse.data && blocksResponse.data.chain && Array.isArray(blocksResponse.data.chain)) {
        // Sort blocks by index/height in reverse order (newest first)
        const sortedBlocks = [...blocksResponse.data.chain].sort((a, b) => b.index - a.index);
        // Take only the latest 10 blocks
        const latestBlocks = sortedBlocks.slice(0, 10);
        setBlocks(latestBlocks);
        
        // Extract recent transactions from blocks
        const allTransactions = [];
        for (const block of latestBlocks) {
          if (block.transactions && Array.isArray(block.transactions)) {
            for (const tx of block.transactions) {
              allTransactions.push({
                ...tx,
                block_hash: block.hash,
                block_height: block.index,
                timestamp: tx.timestamp || block.timestamp
              });
            }
          }
        }
        
        // Sort transactions by timestamp (newest first) and take the first 10
        const sortedTxs = allTransactions.sort((a, b) => {
          const dateA = new Date(a.timestamp);
          const dateB = new Date(b.timestamp);
          return dateB - dateA;
        }).slice(0, 10);
        
        setTransactions(sortedTxs);
      } else {
        setError('Invalid blockchain data format from API');
      }
    } catch (error) {
      console.error('Error loading blockchain data:', error);
      setError('Failed to load blockchain data. Please try again later.');
      
      // Try fallback node with opposite environment
      try {
        // If we're in production, fallback to dev and vice versa
        const fallbackUrl = isProduction ? 'http://localhost:8001/api' : 'https://globalcoyn.com/api';
        console.log('Trying fallback:', `${fallbackUrl}/blockchain/chain`);
        const fallbackResponse = await axios.get(`${fallbackUrl}/blockchain/chain`);
        
        if (fallbackResponse.data && fallbackResponse.data.chain && Array.isArray(fallbackResponse.data.chain)) {
          // Process data from fallback node
          const sortedBlocks = [...fallbackResponse.data.chain].sort((a, b) => b.index - a.index);
          const latestBlocks = sortedBlocks.slice(0, 10);
          setBlocks(latestBlocks);
          
          const allTransactions = [];
          for (const block of latestBlocks) {
            if (block.transactions && Array.isArray(block.transactions)) {
              for (const tx of block.transactions) {
                allTransactions.push({
                  ...tx,
                  block_hash: block.hash,
                  block_height: block.index,
                  timestamp: tx.timestamp || block.timestamp
                });
              }
            }
          }
          
          const sortedTxs = allTransactions.sort((a, b) => {
            const dateA = new Date(a.timestamp);
            const dateB = new Date(b.timestamp);
            return dateB - dateA;
          }).slice(0, 10);
          
          setTransactions(sortedTxs);
          setError(null); // Clear error if fallback was successful
        }
      } catch (fallbackError) {
        console.error('Fallback node also failed:', fallbackError);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery) return;
    
    try {
      setLoading(true);
      
      // Determine if the search query is a block hash, transaction ID, or address
      // This is a simplistic approach - in a real app, you'd have better validation
      
      if (searchQuery.startsWith('1')) {
        // Search for address 
        // Bitcoin-like addresses typically start with 1, not gcn1
        console.log('Searching for wallet address:', searchQuery);
        const response = await axios.get(`${API_BASE_URL}/wallet/balance/${searchQuery}`);
        console.log('Address search result:', response.data);
        // You would normally navigate to an address detail page here
        
        // Handle different API response formats
        let balance = "Unknown";
        if (response.data && response.data.balance !== undefined) {
          balance = response.data.balance;
        } else if (response.data && response.data.success && response.data.balance !== undefined) {
          balance = response.data.balance;
        }
        
        // Navigate to wallet details page instead of showing alert
        navigate(`/app/explorer/address/${searchQuery}`);
      } else if (searchQuery.length === 64) {
        // Search for block or transaction by hash
        try {
          // Try as block hash first
          console.log('Searching for block:', searchQuery);
          const blockResponse = await axios.get(`${API_BASE_URL}/blockchain/blocks/${searchQuery}`);
          console.log('Block search result:', blockResponse.data);
          // Navigate to the block details page
          navigate(`/app/explorer/block/${searchQuery}`);
        } catch (blockError) {
          // Try as transaction ID
          try {
            console.log('Searching for transaction:', searchQuery);
            const txResponse = await axios.get(`${API_BASE_URL}/transactions/${searchQuery}`);
            console.log('Transaction search result:', txResponse.data);
            // Navigate to the transaction details page
            navigate(`/app/explorer/transaction/${searchQuery}`);
          } catch (txError) {
            alert(`No matches found for: ${searchQuery}`);
          }
        }
      } else {
        alert('Please enter a valid address, block hash, or transaction ID');
      }
    } catch (error) {
      console.error('Search error:', error);
      alert('Error searching. Please try again.');
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
  
  const viewWalletDetails = (walletAddress) => {
    navigate(`/app/explorer/address/${walletAddress}`);
  };
  
  const viewTransactionDetails = (transactionId) => {
    navigate(`/app/explorer/transaction/${transactionId}`);
  };

  return (
    <div className="space-y-0">
      <div className="flex flex-col space-y-0 mb-4 px-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Blockchain Explorer</h1>
            <div className="text-sm text-gray-500 dark:text-gray-400 mt-0">
              Network Mode: <span className="font-medium">{isProduction ? 'Production' : 'Development'}</span>
            </div>
          </div>
          
          {/* Search moved to the right */}
          <div className="w-1/2">
            <div className="flex rounded-md shadow-sm">
              <input
                type="text"
                name="search"
                id="search"
                className="flex-1 block w-full rounded-md border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 focus:border-green-500 focus:ring-green-500"
                placeholder="Search block hash, transaction ID, or address"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
              />
              <button
                type="button"
                className="ml-3 inline-flex items-center px-4 py-2 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                onClick={handleSearch}
                disabled={loading || !searchQuery}
                style={{ fontFamily: 'Helvetica, Arial, sans-serif', whiteSpace: 'nowrap' }}
              >
                {loading ? 'Searching...' : 'Search'}
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {error && (
        <div className="border-t border-b border-red-400 text-red-700 px-4 py-3 relative" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
          <strong className="font-bold">Error:</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}
      
      {/* Latest Blocks */}
      <div className="border-t border-gray-300 dark:border-gray-700">
        <div className="px-6 py-1 border-b border-gray-200 dark:border-gray-700 mb-0 mt-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>Latest Blocks</h2>
        </div>
        <div className="overflow-x-auto p-0 mt-0">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Block</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Time</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Hash</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Transactions</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Difficulty</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {loading ? (
                <tr>
                  <td colSpan="5" className="px-6 py-10 text-center text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                    Loading blockchain data...
                  </td>
                </tr>
              ) : blocks.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-10 text-center text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                    No blocks found.
                  </td>
                </tr>
              ) : (
                blocks.map((block) => (
                  <tr 
                    key={block.hash} 
                    className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
                    onClick={() => viewBlockDetails(block.hash)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      {block.index}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {formatTime(block.timestamp)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="font-mono text-orange-500 dark:text-orange-400">
                        {truncateHash(block.hash)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {block.transactions ? block.transactions.length : 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {block.difficulty || block.difficulty_bits || 'Unknown'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Recent Transactions */}
      <div className="border-t border-gray-300 dark:border-gray-700">
        <div className="px-6 py-1 border-b border-gray-200 dark:border-gray-700 mb-0 mt-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>Recent Transactions</h2>
        </div>
        <div className="overflow-x-auto p-0 mt-0">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Transaction ID</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>From</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>To</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Amount</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Fee</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {loading ? (
                <tr>
                  <td colSpan="5" className="px-6 py-10 text-center text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                    Loading transaction data...
                  </td>
                </tr>
              ) : transactions.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-10 text-center text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                    No transactions found.
                  </td>
                </tr>
              ) : (
                transactions.map((tx, index) => (
                  <tr key={tx.id || tx.tx_hash || tx.hash || `tx-${index}`}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div 
                        className="font-mono truncate max-w-xs text-orange-500 dark:text-orange-400 cursor-pointer hover:underline"
                        onClick={(e) => {
                          e.stopPropagation();
                          // Use the transaction hash if available
                          const txId = tx.id || tx.tx_hash || tx.hash;
                          if (txId) {
                            viewTransactionDetails(txId);
                          } else {
                            alert("Transaction ID not available");
                          }
                        }}
                      >
                        {truncateHash(tx.id || tx.tx_hash || tx.hash || "Unknown")}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div 
                        className="truncate max-w-xs text-blue-500 dark:text-blue-400 cursor-pointer hover:underline"
                        onClick={(e) => {
                          e.stopPropagation();
                          viewWalletDetails(tx.sender);
                        }}
                      >
                        {truncateHash(tx.sender)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div 
                        className="truncate max-w-xs text-blue-500 dark:text-blue-400 cursor-pointer hover:underline"
                        onClick={(e) => {
                          e.stopPropagation();
                          viewWalletDetails(tx.recipient);
                        }}
                      >
                        {truncateHash(tx.recipient)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {typeof tx.amount === 'number' ? tx.amount.toFixed(8) : tx.amount} GCN
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {typeof tx.fee === 'number' ? tx.fee.toFixed(8) : tx.fee || '0.00000000'} GCN
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Removed the reload button as it would be redundant with our header refresh option */}
    </div>
  );
};

export default Explorer;