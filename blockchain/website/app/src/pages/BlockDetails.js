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

const BlockDetails = () => {
  const { blockHash } = useParams();
  const navigate = useNavigate();
  const [block, setBlock] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Load block data when component mounts
    loadBlockData();
  }, [blockHash]);

  const loadBlockData = async () => {
    if (!blockHash) {
      setError('No block hash provided');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Fetch block data using the correct endpoint format
      console.log('Fetching block data from:', `${API_BASE_URL}/blockchain/blocks/${blockHash}`);
      const blockResponse = await axios.get(`${API_BASE_URL}/blockchain/blocks/${blockHash}`);
      
      if (blockResponse.data) {
        setBlock(blockResponse.data);
      } else {
        setError('Invalid block data format from API');
      }
    } catch (error) {
      console.error('Error loading block data:', error);
      setError('Failed to load block data. Please try again later.');
      
      // Try fallback node with opposite environment
      try {
        // If we're in production, fallback to dev and vice versa
        const fallbackUrl = isProduction ? 'http://localhost:8001/api' : 'https://globalcoyn.com/api';
        console.log('Trying fallback:', `${fallbackUrl}/blockchain/blocks/${blockHash}`);
        const fallbackResponse = await axios.get(`${fallbackUrl}/blockchain/blocks/${blockHash}`);
        
        if (fallbackResponse.data) {
          setBlock(fallbackResponse.data);
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

  const viewBlockDetails = (blockHash) => {
    if (blockHash && typeof blockHash === 'string') {
      navigate(`/app/explorer/block/${blockHash}`);
    }
  };

  const viewTransactionDetails = (transactionId) => {
    // Only navigate if we have a valid transaction ID
    if (transactionId && typeof transactionId === 'string') {
      // Skip placeholders like tx-{n}
      if (!transactionId.startsWith('tx-')) {
        navigate(`/app/explorer/transaction/${transactionId}`);
      }
    }
  };

  const viewWalletDetails = (walletAddress) => {
    // Only navigate if we have a valid wallet address
    if (walletAddress && typeof walletAddress === 'string') {
      navigate(`/app/explorer/address/${walletAddress}`);
    }
  };

  const goBack = () => {
    navigate('/app/explorer');
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col space-y-0 mb-4 px-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Block Details</h1>
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
          <div className="text-lg text-gray-500 dark:text-gray-400">Loading block data...</div>
        </div>
      ) : block ? (
        <div className="bg-white dark:bg-gray-800 overflow-hidden">
          {/* Block Header */}
          <div className="px-6 py-1 border-b border-gray-200 dark:border-gray-700 mb-0 mt-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>
              Block #{block.index}
            </h2>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {formatTime(block.timestamp)}
            </div>
          </div>
          
          {/* Block Details */}
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left Column */}
              <div className="space-y-4">
                <div>
                  <h3 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Hash</h3>
                  <div className="mt-1 font-mono text-sm text-orange-500 dark:text-orange-400 break-all">
                    {block.hash}
                  </div>
                </div>
                
                <div>
                  <h3 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Previous Hash</h3>
                  <div 
                    className="mt-1 font-mono text-sm text-orange-500 dark:text-orange-400 break-all cursor-pointer hover:underline"
                    onClick={() => viewBlockDetails(block.previous_hash)}
                  >
                    {block.previous_hash}
                  </div>
                </div>
                
                <div>
                  <h3 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Merkle Root</h3>
                  <div className="mt-1 font-mono text-sm text-orange-500 dark:text-orange-400 break-all">
                    {block.merkle_root || 'N/A'}
                  </div>
                </div>
              </div>
              
              {/* Right Column */}
              <div className="space-y-4">
                <div>
                  <h3 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Timestamp</h3>
                  <div className="mt-1 text-sm text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                    {formatTime(block.timestamp)}
                  </div>
                </div>
                
                <div>
                  <h3 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Nonce</h3>
                  <div className="mt-1 text-sm text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                    {block.nonce}
                  </div>
                </div>
                
                <div>
                  <h3 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Difficulty</h3>
                  <div className="mt-1 text-sm text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                    {block.difficulty || block.difficulty_bits || 'Unknown'}
                  </div>
                </div>
                
                <div>
                  <h3 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Size</h3>
                  <div className="mt-1 text-sm text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                    {block.size || 'N/A'} bytes
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Transactions */}
          <div className="border-t border-gray-300 dark:border-gray-700">
            <div className="px-6 py-1 border-b border-gray-200 dark:border-gray-700 mb-0 mt-4">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>
                Transactions ({block.transactions ? block.transactions.length : 0})
              </h3>
            </div>
            
            {block.transactions && block.transactions.length > 0 ? (
              <div className="overflow-x-auto p-0 mt-0">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        Transaction ID
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        From
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        To
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        Amount
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        Fee
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {block.transactions.map((tx, index) => (
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
                            {tx.id || tx.tx_hash || tx.hash || `tx-${index}`}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div 
                            className="text-blue-500 dark:text-blue-400 truncate max-w-xs cursor-pointer hover:underline"
                            onClick={() => viewWalletDetails(tx.sender)}
                          >
                            {tx.sender}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div 
                            className="text-blue-500 dark:text-blue-400 truncate max-w-xs cursor-pointer hover:underline"
                            onClick={() => viewWalletDetails(tx.recipient)}
                          >
                            {tx.recipient}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                          {typeof tx.amount === 'number' ? tx.amount.toFixed(8) : tx.amount} GCN
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                          {typeof tx.fee === 'number' ? tx.fee.toFixed(8) : tx.fee || '0.00000000'} GCN
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                No transactions in this block
              </div>
            )}
          </div>
          
          {/* Technical Details (Optional) */}
          {block.version || block.confirmations ? (
            <div className="border-t border-gray-300 dark:border-gray-700">
              <div className="px-6 py-1 border-b border-gray-200 dark:border-gray-700 mb-0 mt-4">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>
                  Technical Details
                </h3>
              </div>
              
              <div className="px-6 py-4 grid grid-cols-1 lg:grid-cols-2 gap-6">
                {block.version && (
                  <div>
                    <h4 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Version</h4>
                    <div className="mt-1 text-sm text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      {block.version}
                    </div>
                  </div>
                )}
                
                {block.confirmations && (
                  <div>
                    <h4 className="text-md font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Confirmations</h4>
                    <div className="mt-1 text-sm text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      {block.confirmations}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>
      ) : (
        <div className="flex justify-center items-center p-10">
          <div className="text-lg text-gray-500 dark:text-gray-400">No block found with hash: {blockHash}</div>
        </div>
      )}
    </div>
  );
};

export default BlockDetails;