import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

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
      <div className="flex flex-col space-y-0 mb-4 px-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Wallet Details</h1>
            <div className="text-sm text-gray-500 dark:text-gray-400 mt-0">
              Network Mode: <span className="font-medium">{isProduction ? 'Production' : 'Development'}</span>
            </div>
          </div>
          
          <button
            onClick={goBack}
            className="inline-flex items-center px-4 py-2 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
            style={{ fontFamily: 'Helvetica, Arial, sans-serif', whiteSpace: 'nowrap' }}
          >
            Back to Explorer
          </button>
        </div>
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
          <div className="px-6 py-1 border-b border-gray-200 dark:border-gray-700 mb-0 mt-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>
              Wallet Address
            </h2>
            <div className="text-sm font-mono text-orange-500 dark:text-orange-400 break-all">
              {walletInfo.address}
            </div>
          </div>
          
          {/* Wallet Balance */}
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left Column */}
              <div className="space-y-4">
                <div>
                  <h3 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Balance</h3>
                  <div className="mt-1 text-xl text-green-600 dark:text-green-400 font-bold" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                    {typeof walletInfo.balance === 'number' ? walletInfo.balance.toFixed(8) : walletInfo.balance} GCN
                  </div>
                </div>
              </div>
              
              {/* Right Column */}
              <div className="space-y-4">
                <div>
                  <h3 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Last Updated</h3>
                  <div className="mt-1 text-sm text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                    {formatTime(walletInfo.last_updated)}
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
          
          {/* Additional Wallet Stats (Optional) */}
          <div className="border-t border-gray-300 dark:border-gray-700">
            <div className="px-6 py-1 border-b border-gray-200 dark:border-gray-700 mb-0 mt-4">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>
                Wallet Statistics
              </h3>
            </div>
            
            <div className="px-6 py-4 grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div>
                <h4 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Total Sent</h4>
                <div className="mt-1 text-sm text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                  {transactions.reduce((acc, tx) => tx.sender === walletInfo.address ? acc + (typeof tx.amount === 'number' ? tx.amount : 0) : acc, 0).toFixed(8)} GCN
                </div>
              </div>
              
              <div>
                <h4 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Total Received</h4>
                <div className="mt-1 text-sm text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                  {transactions.reduce((acc, tx) => tx.recipient === walletInfo.address ? acc + (typeof tx.amount === 'number' ? tx.amount : 0) : acc, 0).toFixed(8)} GCN
                </div>
              </div>
              
              <div>
                <h4 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Transaction Count</h4>
                <div className="mt-1 text-sm text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                  {transactions.length}
                </div>
              </div>
            </div>
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