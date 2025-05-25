import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useWallet } from '../../../hooks/wallet/useWallet';
import contractService from '../../../services/api/contractService';

const ContractDetails = () => {
  const { contractAddress } = useParams();
  const navigate = useNavigate();
  const { wallet } = useWallet();
  
  const [contract, setContract] = useState(null);
  const [state, setState] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Token-specific state
  const [transferAmount, setTransferAmount] = useState('');
  const [transferTo, setTransferTo] = useState('');
  const [transferLoading, setTransferLoading] = useState(false);
  const [transferError, setTransferError] = useState('');
  const [transferSuccess, setTransferSuccess] = useState('');
  
  // Crowdfund-specific state
  const [contributeAmount, setContributeAmount] = useState('');
  const [contributeLoading, setContributeLoading] = useState(false);
  const [contributeError, setContributeError] = useState('');
  const [contributeSuccess, setContributeSuccess] = useState('');
  
  // Voting-specific state
  const [selectedOption, setSelectedOption] = useState('');
  const [voteLoading, setVoteLoading] = useState(false);
  const [voteError, setVoteError] = useState('');
  const [voteSuccess, setVoteSuccess] = useState('');
  
  // Get contract details and state
  useEffect(() => {
    const fetchContractDetails = async () => {
      setLoading(true);
      setError('');
      
      try {
        // Get contract details
        const contractDetails = await contractService.getContract(contractAddress);
        setContract(contractDetails);
        
        // Get contract state
        const contractState = await contractService.getContractState(contractAddress);
        setState(contractState);
      } catch (error) {
        console.error('Error fetching contract details:', error);
        setError(error.response?.data?.message || 'Failed to load contract details');
      } finally {
        setLoading(false);
      }
    };
    
    fetchContractDetails();
  }, [contractAddress]);
  
  // Handle token transfer
  const handleTokenTransfer = async (e) => {
    e.preventDefault();
    setTransferLoading(true);
    setTransferError('');
    setTransferSuccess('');
    
    try {
      const result = await contractService.transferTokens(
        contractAddress,
        wallet.address,
        transferTo,
        parseFloat(transferAmount)
      );
      
      if (result.success) {
        setTransferSuccess(`Successfully transferred ${transferAmount} ${contract.symbol} to ${transferTo}`);
        setTransferAmount('');
        setTransferTo('');
        
        // Refresh contract state
        const state = await contractService.getContractState(contractAddress);
        setState(state);
      } else {
        setTransferError(result.message || 'Transfer failed');
      }
    } catch (error) {
      console.error('Token transfer error:', error);
      setTransferError(error.response?.data?.message || 'Transfer failed');
    } finally {
      setTransferLoading(false);
    }
  };
  
  // Handle crowdfund contribution
  const handleContribute = async (e) => {
    e.preventDefault();
    setContributeLoading(true);
    setContributeError('');
    setContributeSuccess('');
    
    try {
      const result = await contractService.executeContract(
        contractAddress,
        'contribute',
        {
          amount: parseFloat(contributeAmount)
        },
        wallet.address
      );
      
      if (result.success) {
        setContributeSuccess(`Successfully contributed ${contributeAmount} GCN to the campaign`);
        setContributeAmount('');
        
        // Refresh contract state
        const state = await contractService.getContractState(contractAddress);
        setState(state);
      } else {
        setContributeError(result.message || 'Contribution failed');
      }
    } catch (error) {
      console.error('Contribution error:', error);
      setContributeError(error.response?.data?.message || 'Contribution failed');
    } finally {
      setContributeLoading(false);
    }
  };
  
  // Handle voting
  const handleVote = async (e) => {
    e.preventDefault();
    setVoteLoading(true);
    setVoteError('');
    setVoteSuccess('');
    
    try {
      const result = await contractService.executeContract(
        contractAddress,
        'vote',
        {
          option: selectedOption
        },
        wallet.address
      );
      
      if (result.success) {
        setVoteSuccess(`Successfully voted for "${selectedOption}"`);
        
        // Refresh contract state
        const state = await contractService.getContractState(contractAddress);
        setState(state);
      } else {
        setVoteError(result.message || 'Vote failed');
      }
    } catch (error) {
      console.error('Voting error:', error);
      setVoteError(error.response?.data?.message || 'Vote failed');
    } finally {
      setVoteLoading(false);
    }
  };
  
  // Render contract details based on type
  const renderContractDetails = () => {
    if (!contract) return null;
    
    switch (contract.type) {
      case 'TOKEN':
        return (
          <div style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            <div className="mb-6">
              <h3 className="text-lg font-medium mb-2 text-gray-900 dark:text-white">Token Information</h3>
              <p><span className="font-medium">Name:</span> {contract.name}</p>
              <p><span className="font-medium">Symbol:</span> {contract.symbol}</p>
              <p><span className="font-medium">Total Supply:</span> {state.total_supply}</p>
              {state.max_supply && (
                <p><span className="font-medium">Max Supply:</span> {state.max_supply}</p>
              )}
              <p><span className="font-medium">Decimals:</span> {state.decimals}</p>
              <p><span className="font-medium">Creator:</span> {contract.creator}</p>
            </div>
            
            {wallet && (
              <>
                <div className="mb-6">
                  <h3 className="text-lg font-medium mb-2 text-gray-900 dark:text-white">Your Balance</h3>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {(state.balances && state.balances[wallet.address]) || 0} {contract.symbol}
                  </p>
                </div>
                
                <div className="mb-6">
                  <h3 className="text-lg font-medium mb-2 text-gray-900 dark:text-white">Transfer Tokens</h3>
                  <form onSubmit={handleTokenTransfer}>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Recipient Address</label>
                        <input
                          type="text"
                          className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
                          value={transferTo}
                          onChange={(e) => setTransferTo(e.target.value)}
                          placeholder="Recipient address"
                          required
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Amount</label>
                        <input
                          type="number"
                          className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
                          value={transferAmount}
                          onChange={(e) => setTransferAmount(e.target.value)}
                          min="0.000001"
                          step="0.000001"
                          placeholder={`Amount in ${contract.symbol}`}
                          required
                        />
                      </div>
                      
                      {transferError && (
                        <div className="p-2 bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200 rounded">
                          {transferError}
                        </div>
                      )}
                      
                      {transferSuccess && (
                        <div className="p-2 bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200 rounded">
                          {transferSuccess}
                        </div>
                      )}
                      
                      <button
                        type="submit"
                        className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-blue-700 dark:hover:bg-blue-800"
                        disabled={transferLoading || !wallet}
                      >
                        {transferLoading ? 'Processing...' : 'Transfer'}
                      </button>
                    </div>
                  </form>
                </div>
              </>
            )}
          </div>
        );
        
      case 'CROWDFUND':
        const now = Math.floor(Date.now() / 1000);
        const isActive = state.deadline > now;
        const goalReached = (state.total_raised || 0) >= (state.goal || 0);
        const canWithdraw = wallet && !isActive && ((goalReached && contract.creator === wallet.address) || (!goalReached && state.contributions && state.contributions[wallet.address]));
        
        return (
          <div style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            <div className="mb-6">
              <h3 className="text-lg font-medium mb-2 text-gray-900 dark:text-white">Campaign Information</h3>
              <p><span className="font-medium">Name:</span> {contract.name}</p>
              <p><span className="font-medium">Description:</span> {state.description || 'No description provided'}</p>
              <p><span className="font-medium">Goal:</span> {state.goal} GCN</p>
              <p><span className="font-medium">Deadline:</span> {new Date(state.deadline * 1000).toLocaleString()}</p>
              <p>
                <span className="font-medium">Status:</span> 
                {isActive ? ' Active' : ' Ended'}
                {!isActive && goalReached ? ' (Goal Reached)' : ''}
                {!isActive && !goalReached ? ' (Goal Not Reached)' : ''}
              </p>
              <p><span className="font-medium">Creator:</span> {contract.creator}</p>
            </div>
            
            <div className="mb-6">
              <h3 className="text-lg font-medium mb-2 text-gray-900 dark:text-white">Funding Progress</h3>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                <div 
                  className="bg-blue-600 dark:bg-blue-500 h-2.5 rounded-full" 
                  style={{ width: `${Math.min(100, ((state.total_raised || 0) / (state.goal || 1)) * 100)}%` }}
                ></div>
              </div>
              <p className="mt-2">
                <span className="font-bold">{state.total_raised || 0}</span> of {state.goal} GCN raised
                ({Math.round(((state.total_raised || 0) / (state.goal || 1)) * 100)}%)
              </p>
              {wallet && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Your contribution: {(state.contributions && state.contributions[wallet.address]) || 0} GCN
                </p>
              )}
            </div>
            
            {wallet && isActive && (
              <div className="mb-6">
                <h3 className="text-lg font-medium mb-2 text-gray-900 dark:text-white">Contribute to Campaign</h3>
                <form onSubmit={handleContribute}>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Amount (GCN)</label>
                      <input
                        type="number"
                        className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
                        value={contributeAmount}
                        onChange={(e) => setContributeAmount(e.target.value)}
                        min="0.01"
                        step="0.01"
                        placeholder="Amount to contribute"
                        required
                      />
                    </div>
                    
                    {contributeError && (
                      <div className="p-2 bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200 rounded">
                        {contributeError}
                      </div>
                    )}
                    
                    {contributeSuccess && (
                      <div className="p-2 bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200 rounded">
                        {contributeSuccess}
                      </div>
                    )}
                    
                    <button
                      type="submit"
                      className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-blue-700 dark:hover:bg-blue-800"
                      disabled={contributeLoading || !wallet}
                    >
                      {contributeLoading ? 'Processing...' : 'Contribute'}
                    </button>
                  </div>
                </form>
              </div>
            )}
            
            {canWithdraw && (
              <div className="mb-6">
                <h3 className="text-lg font-medium mb-2 text-gray-900 dark:text-white">
                  {goalReached ? 'Withdraw Funds (Creator)' : 'Claim Refund'}
                </h3>
                <button
                  onClick={() => {
                    // Implement withdrawal logic
                    alert('Withdrawal feature coming soon!');
                  }}
                  className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 dark:bg-green-700 dark:hover:bg-green-800"
                >
                  {goalReached ? 'Withdraw Funds' : 'Claim Refund'}
                </button>
              </div>
            )}
          </div>
        );
        
      case 'VOTING':
        const voteStarted = state.start_time < Math.floor(Date.now() / 1000);
        const voteEnded = state.end_time < Math.floor(Date.now() / 1000);
        const hasVoted = wallet && state.voters && state.voters[wallet.address];
        
        return (
          <div style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            <div className="mb-6">
              <h3 className="text-lg font-medium mb-2 text-gray-900 dark:text-white">Vote Information</h3>
              <p><span className="font-medium">Name:</span> {contract.name}</p>
              <p><span className="font-medium">Description:</span> {state.description || 'No description provided'}</p>
              <p><span className="font-medium">Start:</span> {new Date(state.start_time * 1000).toLocaleString()}</p>
              <p><span className="font-medium">End:</span> {new Date(state.end_time * 1000).toLocaleString()}</p>
              <p>
                <span className="font-medium">Status:</span> 
                {!voteStarted ? ' Not Started' : voteEnded ? ' Ended' : ' Active'}
              </p>
              <p><span className="font-medium">Creator:</span> {contract.creator}</p>
              {hasVoted && (
                <p><span className="font-medium">Your Vote:</span> {state.voters[wallet.address]}</p>
              )}
            </div>
            
            <div className="mb-6">
              <h3 className="text-lg font-medium mb-2 text-gray-900 dark:text-white">Current Results</h3>
              {state.options && state.options.map(option => {
                const voteCount = (state.votes && state.votes[option]) || 0;
                const totalVotes = Object.values(state.votes || {}).reduce((sum, count) => sum + count, 0);
                const percentage = totalVotes > 0 ? (voteCount / totalVotes) * 100 : 0;
                
                return (
                  <div key={option} className="mb-3">
                    <div className="flex justify-between mb-1">
                      <span>{option}</span>
                      <span>{voteCount} votes ({percentage.toFixed(1)}%)</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                      <div 
                        className="bg-blue-600 dark:bg-blue-500 h-2.5 rounded-full" 
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
            
            {wallet && voteStarted && !voteEnded && !hasVoted && (
              <div className="mb-6">
                <h3 className="text-lg font-medium mb-2 text-gray-900 dark:text-white">Cast Your Vote</h3>
                <form onSubmit={handleVote}>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Select Option</label>
                      <select
                        className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
                        value={selectedOption}
                        onChange={(e) => setSelectedOption(e.target.value)}
                        required
                      >
                        <option value="">-- Select an option --</option>
                        {state.options && state.options.map(option => (
                          <option key={option} value={option}>{option}</option>
                        ))}
                      </select>
                    </div>
                    
                    {voteError && (
                      <div className="p-2 bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200 rounded">
                        {voteError}
                      </div>
                    )}
                    
                    {voteSuccess && (
                      <div className="p-2 bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200 rounded">
                        {voteSuccess}
                      </div>
                    )}
                    
                    <button
                      type="submit"
                      className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-blue-700 dark:hover:bg-blue-800"
                      disabled={voteLoading || !selectedOption || !wallet}
                    >
                      {voteLoading ? 'Processing...' : 'Cast Vote'}
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        );
        
      default:
        return <p style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Contract details not available for this type.</p>;
    }
  };
  
  return (
    <div className="mx-0">
      {/* Header Section with Back Button */}
      <div className="flex flex-col space-y-0 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Contract Details
            </h1>
          </div>
          
          <button
            onClick={() => navigate('/app/contracts')}
            className="py-1 px-3 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
          >
            Back to Contracts
          </button>
        </div>
      </div>

      {/* Border below header */}
      <div className="border-b border-gray-300 dark:border-gray-700 mb-4"></div>

      {/* Contract Details */}
      {loading ? (
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 flex items-center justify-center">
          <p className="text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Loading contract details...</p>
        </div>
      ) : error ? (
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <div className="p-4 bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200 rounded" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            {error}
          </div>
        </div>
      ) : !contract ? (
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 text-center">
          <p className="text-gray-700 dark:text-gray-300 mb-4" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Contract not found.</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>{contract.name}</h2>
          </div>
          
          <div className="border-b border-gray-200 dark:border-gray-700 pb-2 mb-4">
            <p className="text-sm text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Type: {contract.type} • Created: {new Date(contract.creation_time * 1000).toLocaleDateString()}
            </p>
            <p className="text-xs text-orange-500 dark:text-orange-400 mt-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>{contractAddress}</p>
          </div>
          
          {renderContractDetails()}
        </div>
      )}
    </div>
  );
};

export default ContractDetails;