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

const TransactionDetails = () => {
  const { transactionId } = useParams();
  const navigate = useNavigate();
  const [transaction, setTransaction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Load transaction data when component mounts
    loadTransactionData();
  }, [transactionId]);

  const loadTransactionData = async () => {
    if (!transactionId) {
      setError('No transaction ID provided');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      let responseData = null;

      // Fetch transaction data using the correct endpoint path
      console.log('Fetching transaction data from:', `${API_BASE_URL}/transactions/${transactionId}`);
      
      // Only proceed with real transaction IDs, not placeholders like tx-{n}
      if (transactionId.startsWith('tx-')) {
        setError('Unable to fetch transaction details for a placeholder ID. Please use a real transaction ID.');
        return;
      }
      
      // Try the direct endpoint first
      try {
        const txResponse = await axios.get(`${API_BASE_URL}/transactions/${transactionId}`);
        responseData = txResponse.data;
      } catch (directError) {
        console.log('Direct endpoint failed, trying with wallet transaction history endpoint');
        
        // If direct endpoint fails, try checking if we can find it in transaction history
        try {
          // Get all transaction history if the API supports it
          const historyResponse = await axios.get(`${API_BASE_URL}/transactions/history`);
          
          // Look for the transaction in the history
          if (historyResponse.data && historyResponse.data.transactions) {
            const foundTx = historyResponse.data.transactions.find(tx => 
              tx.id === transactionId || tx.tx_hash === transactionId
            );
            
            if (foundTx) {
              responseData = foundTx;
            }
          }
        } catch (historyError) {
          console.log('History endpoint also failed:', historyError);
          // If history endpoint also fails, throw the original error
          throw directError;
        }
      }
      
      // Process the response data
      if (responseData) {
        // Handle API response format which contains transaction data within the 'transaction' property
        if (responseData.transaction) {
          const txData = {
            ...responseData.transaction,
            status: responseData.status,
            confirmations: responseData.confirmations,
            block_hash: responseData.block_hash,
            block_index: responseData.block_index
          };
          setTransaction(txData);
        } else {
          setTransaction(responseData);
        }
      } else {
        setError('Invalid transaction data format from API');
      }
    } catch (error) {
      console.error('Error loading transaction data:', error);
      setError('Failed to load transaction data. Please try again later.');
      
      // Try fallback node with opposite environment
      try {
        // If we're in production, fallback to dev and vice versa
        const fallbackUrl = isProduction ? 'http://localhost:8001/api' : 'https://globalcoyn.com/api';
        console.log('Trying fallback:', `${fallbackUrl}/transactions/${transactionId}`);
        
        let fallbackData = null;
        
        // Only proceed with real transaction IDs, not placeholders
        if (transactionId.startsWith('tx-')) {
          return;
        }
        
        // Try the direct endpoint first
        try {
          const fallbackResponse = await axios.get(`${fallbackUrl}/transactions/${transactionId}`);
          fallbackData = fallbackResponse.data;
        } catch (directError) {
          // If direct endpoint fails, try history endpoint
          try {
            const historyResponse = await axios.get(`${fallbackUrl}/transactions/history`);
            
            // Look for the transaction in the history
            if (historyResponse.data && historyResponse.data.transactions) {
              const foundTx = historyResponse.data.transactions.find(tx => 
                tx.id === transactionId || tx.tx_hash === transactionId
              );
              
              if (foundTx) {
                fallbackData = foundTx;
              }
            }
          } catch (historyError) {
            // If history endpoint also fails, throw the original error
            throw directError;
          }
        }
        
        // Process fallback data
        if (fallbackData) {
          // Handle API response format which contains transaction data within the 'transaction' property
          if (fallbackData.transaction) {
            const txData = {
              ...fallbackData.transaction,
              status: fallbackData.status,
              confirmations: fallbackData.confirmations,
              block_hash: fallbackData.block_hash,
              block_index: fallbackData.block_index
            };
            setTransaction(txData);
          } else {
            setTransaction(fallbackData);
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
    navigate(`/app/explorer/address/${address}`);
  };

  const goBack = () => {
    navigate('/app/explorer');
  };

  // Calculate transaction status based on API status or confirmations
  const getTransactionStatus = () => {
    if (!transaction) return 'Unknown';
    
    // If API provides a status directly, use it
    if (transaction.status) {
      if (transaction.status === 'pending') return 'Pending';
      if (transaction.status === 'confirmed') {
        if (transaction.confirmations >= 6) return 'Confirmed';
        return `Confirming (${transaction.confirmations || 1} of 6)`;
      }
      return transaction.status.charAt(0).toUpperCase() + transaction.status.slice(1);
    }
    
    // Fall back to using confirmations
    if (transaction.confirmations === 0) return 'Pending';
    if (transaction.confirmations >= 6) return 'Confirmed';
    return `Confirming (${transaction.confirmations} of 6)`;
  };

  // Get appropriate status color
  const getStatusColor = () => {
    if (!transaction) return 'gray';
    
    // If API provides a status directly, use it
    if (transaction.status) {
      if (transaction.status === 'pending') return 'yellow';
      if (transaction.status === 'confirmed') {
        if (transaction.confirmations >= 6) return 'green';
        return 'blue';
      }
      return 'gray';
    }
    
    // Fall back to using confirmations
    if (transaction.confirmations === 0) return 'yellow';
    if (transaction.confirmations >= 6) return 'green';
    return 'blue';
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col space-y-0 mb-4 px-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Transaction Details</h1>
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
          <div className="text-lg text-gray-500 dark:text-gray-400">Loading transaction data...</div>
        </div>
      ) : transaction ? (
        <div className="bg-white dark:bg-gray-800 overflow-hidden">
          {/* Transaction Header */}
          <div className="px-6 py-1 border-b border-gray-200 dark:border-gray-700 mb-0 mt-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>
              Transaction ID
            </h2>
            <div className="text-sm font-mono text-orange-500 dark:text-orange-400 break-all">
              {transaction.id || transactionId}
            </div>
          </div>
          
          {/* Transaction Details */}
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left Column */}
              <div className="space-y-4">
                <div>
                  <h3 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Status</h3>
                  <div className={`mt-1 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${getStatusColor()}-100 text-${getStatusColor()}-800 dark:bg-${getStatusColor()}-900 dark:text-${getStatusColor()}-200`}>
                    {getTransactionStatus()}
                  </div>
                </div>
                
                <div>
                  <h3 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Amount</h3>
                  <div className="mt-1 text-xl text-green-600 dark:text-green-400 font-bold" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                    {typeof transaction.amount === 'number' ? transaction.amount.toFixed(8) : transaction.amount} GCN
                  </div>
                </div>
                
                <div>
                  <h3 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Fee</h3>
                  <div className="mt-1 text-sm text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                    {typeof transaction.fee === 'number' ? transaction.fee.toFixed(8) : transaction.fee || '0.00000000'} GCN
                  </div>
                </div>
              </div>
              
              {/* Right Column */}
              <div className="space-y-4">
                <div>
                  <h3 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Timestamp</h3>
                  <div className="mt-1 text-sm text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                    {formatTime(transaction.timestamp)}
                  </div>
                </div>
                
                <div>
                  <h3 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Block</h3>
                  <div 
                    className="mt-1 text-sm text-orange-500 dark:text-orange-400 cursor-pointer hover:underline"
                    onClick={() => transaction.block_hash && viewBlockDetails(transaction.block_hash)}
                    style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
                  >
                    {transaction.block_index || transaction.block_height || (transaction.status === "pending" ? 'Pending' : 'Unknown')} 
                    {transaction.block_hash ? ` (${truncateHash(transaction.block_hash)})` : ''}
                  </div>
                </div>
                
                {transaction.confirmations !== undefined && (
                  <div>
                    <h3 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Confirmations</h3>
                    <div className="mt-1 text-sm text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      {transaction.confirmations || 0}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {/* Sender and Recipient */}
          <div className="border-t border-gray-300 dark:border-gray-700">
            <div className="px-6 py-1 border-b border-gray-200 dark:border-gray-700 mb-0 mt-4">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>
                Transaction Details
              </h3>
            </div>
            
            <div className="px-6 py-4 space-y-4">
              <div>
                <h3 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>From</h3>
                <div 
                  className="mt-1 text-blue-500 dark:text-blue-400 cursor-pointer hover:underline break-all"
                  onClick={() => viewWalletDetails(transaction.sender)}
                >
                  {transaction.sender}
                </div>
              </div>
              
              <div>
                <h3 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>To</h3>
                <div 
                  className="mt-1 text-blue-500 dark:text-blue-400 cursor-pointer hover:underline break-all"
                  onClick={() => viewWalletDetails(transaction.recipient)}
                >
                  {transaction.recipient}
                </div>
              </div>
            </div>
          </div>
          
          {/* Transaction Data (if any) */}
          {transaction.data && (
            <div className="border-t border-gray-300 dark:border-gray-700">
              <div className="px-6 py-1 border-b border-gray-200 dark:border-gray-700 mb-0 mt-4">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>
                  Transaction Data
                </h3>
              </div>
              
              <div className="px-6 py-4">
                <div className="font-mono text-sm text-gray-600 dark:text-gray-400 break-all bg-gray-100 dark:bg-gray-900 p-4 rounded">
                  {typeof transaction.data === 'string' ? transaction.data : JSON.stringify(transaction.data, null, 2)}
                </div>
              </div>
            </div>
          )}
          
          {/* Transaction Signature (if any) */}
          {transaction.signature && (
            <div className="border-t border-gray-300 dark:border-gray-700">
              <div className="px-6 py-1 border-b border-gray-200 dark:border-gray-700 mb-0 mt-4">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>
                  Signature
                </h3>
              </div>
              
              <div className="px-6 py-4">
                <div className="font-mono text-sm text-gray-600 dark:text-gray-400 break-all">
                  {transaction.signature}
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="flex justify-center items-center p-10">
          <div className="text-lg text-gray-500 dark:text-gray-400">No transaction found with ID: {transactionId}</div>
        </div>
      )}
    </div>
  );
};

export default TransactionDetails;