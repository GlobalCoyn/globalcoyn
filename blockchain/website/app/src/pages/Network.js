import React, { useState, useEffect } from 'react';
import networkService from '../services/networkService';

const Network = () => {
  // State for network data
  const [networkStatus, setNetworkStatus] = useState(null);
  const [networkPeers, setNetworkPeers] = useState([]);
  const [networkStats, setNetworkStats] = useState(null);
  const [blockchainInfo, setBlockchainInfo] = useState(null);
  const [nodeInfo, setNodeInfo] = useState(null);
  const [knownNodes, setKnownNodes] = useState([]);
  
  // State for UI
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  
  // Get environment information
  const { isProduction } = networkService.getApiUrls();
  
  // Format time elapsed in a human-readable form
  const formatTimeElapsed = (seconds) => {
    if (seconds < 60) {
      return `${Math.floor(seconds)}s`;
    } else if (seconds < 3600) {
      return `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s`;
    } else {
      return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
    }
  };
  
  // Format large numbers with commas
  const formatNumber = (num) => {
    return num ? num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",") : '0';
  };
  
  // Load network data
  const loadNetworkData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Load all data in parallel using Promise.all
      console.log('Loading network data...');
      const [statusRes, peersRes, statsRes, blockchainRes, nodeRes, nodesRes] = await Promise.all([
        networkService.getNetworkStatus(),
        networkService.getNetworkPeers(),
        networkService.getNetworkStats(),
        networkService.getBlockchainInfo(),
        networkService.getNodeInfo(),
        networkService.getKnownNodes()
      ]);
      
      console.log('Network data loaded:', {
        status: statusRes,
        peers: peersRes,
        stats: statsRes,
        blockchain: blockchainRes,
        node: nodeRes,
        nodes: nodesRes
      });
      
      // Debug raw response from known nodes endpoint for troubleshooting
      console.log('Known nodes response:', nodesRes);
      
      setNetworkStatus(statusRes);
      setNetworkPeers(peersRes.peers || []);
      setNetworkStats(statsRes);
      setBlockchainInfo(blockchainRes);
      setNodeInfo(nodeRes);
      setKnownNodes(nodesRes.nodes || []);
      setLastUpdated(new Date());
      
      // Update connection status
      if (statusRes && statusRes.status === 'online') {
        setConnectionStatus('connected');
      }
    } catch (err) {
      console.error('Error loading network data:', err);
      setError('Failed to load network data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Connect to the network
  const connectToNetwork = async () => {
    setIsConnecting(true);
    setConnectionStatus('connecting');
    
    try {
      console.log('Connecting to network...');
      const result = await networkService.connectToNetwork();
      console.log('Network connection result:', result);
      
      if (result.success) {
        setConnectionStatus('connected');
        // Reload network data to show updated state
        await loadNetworkData();
      } else {
        setConnectionStatus('disconnected');
        setError(result.message || 'Failed to connect to the network.');
      }
    } catch (err) {
      console.error('Error connecting to network:', err);
      setConnectionStatus('disconnected');
      setError('Failed to connect to the network. Please try again.');
    } finally {
      setIsConnecting(false);
    }
  };
  
  // Sync with the network
  const syncWithNetwork = async () => {
    setIsSyncing(true);
    
    try {
      console.log('Syncing with network...');
      const result = await networkService.syncWithNetwork();
      console.log('Network sync result:', result);
      
      if (result.success) {
        // Reload network data to show updated state
        await loadNetworkData();
      } else {
        setError(result.message || 'Failed to sync with the network.');
      }
    } catch (err) {
      console.error('Error syncing with network:', err);
      setError('Failed to sync with the network. Please try again.');
    } finally {
      setIsSyncing(false);
    }
  };
  
  // Calculate total nodes (known nodes + dev frontend node)
  const getTotalNodeCount = () => {
    // In development mode, we have existing nodes plus the dev frontend node
    if (!isProduction) {
      // Use known nodes count and add 1 for the frontend node
      const knownNodeCount = knownNodes?.length || 0;
      console.log('Development mode node count calculation:', { 
        knownNodes: knownNodeCount,
        frontendNode: 1,
        total: knownNodeCount + 1
      });
      
      // For development, we should show 5 nodes (4 known nodes + frontend node)
      return (knownNodeCount > 0) ? knownNodeCount + 1 : 5;
    } else if (blockchainInfo) {
      // In production, use the node_count from blockchain info
      return blockchainInfo.node_count || 0;
    } else {
      return 'Unknown';
    }
  };
  
  // Load data on component mount
  useEffect(() => {
    const initializeNetworkPage = async () => {
      // First load current data to see what's available
      await loadNetworkData();
      
      // Connect to the network automatically to ensure we have a node
      // that's part of the network
      await connectToNetwork();
      
      // Sync with the network to get the latest state
      await syncWithNetwork();
      
      // Reload data again to show the updated state
      await loadNetworkData();
    };
    
    initializeNetworkPage();
    
    // Set up polling to refresh data every 30 seconds
    const interval = setInterval(() => {
      loadNetworkData();
    }, 30000);
    
    // Clean up on unmount
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div className="space-y-0">
      <div className="flex flex-col space-y-0 mb-4 px-6">
        <div className="flex items-center justify-between">
          <div className="w-full">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Network Status</h1>
            <div className="text-sm text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Network Mode: <span className="font-medium">{!isProduction ? 'Development' : 'Production'}</span>
              {lastUpdated && (
                <span className="ml-4 inline-flex items-center">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                  <button
                    className="ml-2 text-gray-500 dark:text-gray-400 inline-flex items-center"
                    onClick={loadNetworkData}
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
              className="btn-secondary flex items-center text-xs py-1 px-3 whitespace-nowrap"
              onClick={connectToNetwork}
              disabled={isConnecting || connectionStatus === 'connected'}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              {isConnecting ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Connecting...
                </>
              ) : connectionStatus === 'connected' ? (
                'Connected to Network'
              ) : (
                'Connect to Network'
              )}
            </button>
            
            <button
              className="btn-secondary flex items-center text-xs py-1 px-3 whitespace-nowrap"
              onClick={syncWithNetwork}
              disabled={isSyncing || connectionStatus !== 'connected'}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              {isSyncing ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Syncing...
                </>
              ) : (
                'Sync with Network'
              )}
            </button>
          </div>
        </div>
      </div>
      
      {/* Error Message */}
      {error && (
        <div className="mx-6 border-t border-b border-red-400 text-red-700 px-4 py-3 relative" role="alert">
          <strong className="font-bold" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Error!</strong>
          <span className="block sm:inline" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}> {error}</span>
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
          <strong className="font-bold" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Development Mode:</strong>
          <span className="block sm:inline" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}> Running a node as part of the development network. Your browser is now part of the blockchain network.</span>
        </div>
      )}
      
      {/* Stats Overview */}
      <div className="stats-container">
        {/* Active Nodes */}
        <div className="stats-box">
          <h3 className="stats-title" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Active Nodes</h3>
          <p className="stats-value" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            {isLoading ? 'Loading...' : formatNumber(getTotalNodeCount())}
          </p>
          {!isProduction && (
            <p className="text-xs text-gray-500 mt-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              (Including your browser node)
            </p>
          )}
        </div>
        
        {/* Blockchain Height */}
        <div className="stats-box">
          <h3 className="stats-title" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Blockchain Height</h3>
          <p className="stats-value" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            {isLoading ? 'Loading...' : (
              blockchainInfo ? formatNumber(blockchainInfo.chain_length) : 'Unknown'
            )}
          </p>
        </div>
        
        {/* Network Mode */}
        <div className="stats-box">
          <h3 className="stats-title" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Network Mode</h3>
          <p className="stats-value" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            {isLoading ? 'Loading...' : (
              // In development frontend, always show development mode
              !isProduction ? 'Development' : (networkStatus?.network_mode === 'development' ? 'Development' : 'Production')
            )}
          </p>
        </div>
        
        {/* Current Difficulty */}
        <div className="stats-box">
          <h3 className="stats-title" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Mining Difficulty</h3>
          <p className="stats-value" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            {isLoading ? 'Loading...' : (
              blockchainInfo?.difficulty?.bits ? blockchainInfo.difficulty.bits : 'Unknown'
            )}
          </p>
        </div>
      </div>
      
      {/* Node Status Section */}
      <div className="mt-4 px-6 py-1 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center" style={{ lineHeight: '1' }}>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white inline-flex items-center" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            Your Node Status
            {/* Connection Status Indicator */}
            <span className={`ml-3 inline-block px-2.5 py-0.5 rounded-full text-xs font-medium align-middle ${
              connectionStatus === 'connected' 
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' 
                : connectionStatus === 'connecting'
                  ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
            }`} style={{ fontFamily: 'Helvetica, Arial, sans-serif', position: 'relative', top: '-2px' }}>
              {connectionStatus === 'connected' ? 'Connected' : connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}
            </span>
          </h2>
        </div>
      </div>
      
      <div className="px-6 pt-2 pb-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Connected To */}
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Connected To</h3>
            <p className="mt-1 text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              {isLoading ? 'Loading...' : (
                `${networkPeers.length || 0} Peers`
              )}
            </p>
          </div>
          
          {/* Sync Status */}
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Sync Status</h3>
            <p className="mt-1 text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              {isLoading ? 'Loading...' : 'Synced'}
            </p>
          </div>
          
          {/* P2P Port */}
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>P2P Port</h3>
            <p className="mt-1 text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              {isLoading ? 'Loading...' : (nodeInfo?.p2p_port || 'Unknown')}
            </p>
          </div>
          
          {/* Web Port */}
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Web Port</h3>
            <p className="mt-1 text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              {isLoading ? 'Loading...' : (nodeInfo?.api_port || nodeInfo?.web_port || 'Unknown')}
            </p>
          </div>
          
          {/* Version */}
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Node Version</h3>
            <p className="mt-1 text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              {isLoading ? 'Loading...' : (nodeInfo?.version || 'v1.0.0')}
            </p>
          </div>
          
          {/* Uptime */}
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Uptime</h3>
            <p className="mt-1 text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              {isLoading ? 'Loading...' : (
                networkStatus?.uptime ? formatTimeElapsed(networkStatus.uptime) : 'Unknown'
              )}
            </p>
          </div>
          
          {/* Node Number */}
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Node Number</h3>
            <p className="mt-1 text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              {isLoading ? 'Loading...' : (
                // In development mode, this is node #5 (frontend node) by default
                nodeInfo?.node_number || (!isProduction ? '5' : 'Unknown')
              )}
            </p>
            {!isProduction && (
              <p className="mt-1 text-xs text-gray-500" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                Browser node (joining 4 existing nodes)
              </p>
            )}
          </div>
          
          {/* Node Address */}
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Node Address</h3>
            <p className="mt-1 text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              {isLoading ? 'Loading...' : (networkStatus?.this_node?.address || 'localhost')}
            </p>
          </div>
        </div>
      </div>
      
      {/* Network Peers */}
      <div className="mt-4 px-6 py-2 border-t border-gray-200 dark:border-gray-700 flex justify-between items-center">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Network Peers</h2>
        <button 
          className="btn-secondary text-xs py-1 px-3"
          onClick={loadNetworkData}
          disabled={isLoading}
          style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
        >
          {isLoading ? 'Refreshing...' : 'Refresh Peers'}
        </button>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Node ID</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Address</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Port</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Status</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Last Seen</th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {isLoading ? (
              <tr>
                <td colSpan="5" className="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                  Loading peers...
                </td>
              </tr>
            ) : networkPeers.length === 0 ? (
              <tr>
                <td colSpan="5" className="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                  No peers connected
                </td>
              </tr>
            ) : (
              networkPeers.map((peer, index) => {
                // Determine if peer is active (seen in last 5 minutes)
                const isActive = peer.last_seen < 300;
                
                return (
                  <tr key={peer.node_id || index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      {peer.node_id || `Node ${index + 1}`}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      <span className="text-blue-600 dark:text-blue-400">{peer.address}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      {peer.port}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        isActive 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' 
                          : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
                      }`} style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        {isActive ? 'Online' : 'Offline'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      {formatTimeElapsed(peer.last_seen || 0)} ago
                    </td>
                  </tr>
                );
              })
            )}
            
            {/* Include a row for this frontend node */}
            {!isLoading && !isProduction && (
              <tr className="bg-gray-50 dark:bg-gray-700">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                  {nodeInfo?.node_number ? `localhost:${nodeInfo.p2p_port || 9004}` : 'localhost:9004'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                  <span className="text-blue-600 dark:text-blue-400">localhost</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                  {nodeInfo?.p2p_port || 9004}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                    This Browser Node
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                  0s ago
                </td>
              </tr>
            )}
            
            {/* Known nodes section */}
            {!isLoading && knownNodes.length > 0 && (
              <>
                <tr className="bg-gray-50 dark:bg-gray-700">
                  <td colSpan="5" className="px-6 py-2 text-sm font-medium text-gray-500 dark:text-gray-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                    Known Network Nodes ({knownNodes.length})
                  </td>
                </tr>
                
                {knownNodes.map((node, index) => {
                  // Determine if node is active (default to true in development mode)
                  const isActive = !isProduction || node.connected || (node.last_seen && node.last_seen < 300);
                  
                  return (
                    <tr key={`bootstrap-${index}`} className={isActive ? "bg-green-50 dark:bg-green-900/10" : ""}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        {`${node.address}:${node.p2p_port || '9000'}`}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        <span className="text-blue-600 dark:text-blue-400">{node.address}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        {node.web_port || '8001'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          isActive
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' 
                            : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                        }`} style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                          {isActive ? 'Active' : 'Available'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                        {node.last_seen ? `${formatTimeElapsed(node.last_seen)} ago` : 'N/A'}
                      </td>
                    </tr>
                  );
                })}
              </>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Network;