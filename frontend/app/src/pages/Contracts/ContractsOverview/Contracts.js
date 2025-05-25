import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

// Services
import contractService from '../../../services/api/contractService';
import { useWallet } from '../../../hooks/wallet/useWallet';

// Contract List Component
const ContractList = ({ contracts, onContractSelected, filterType = null }) => {
  // Filter contracts by type if a filter is specified
  const filteredContracts = filterType 
    ? contracts.filter(contract => contract.type === filterType)
    : contracts;

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-0">
      {filteredContracts.length === 0 ? (
        <div className="p-6 text-center">
          <p className="text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>No contracts found.</p>
        </div>
      ) : (
        <ul className="divide-y divide-gray-200 dark:divide-gray-700">
          {filteredContracts.map(contract => (
            <li key={contract.address} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer" onClick={() => onContractSelected(contract)}>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>{contract.name}</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                    {contract.type === 'TOKEN' ? `${contract.symbol} • ` : ''}
                    {new Date(contract.creation_time * 1000).toLocaleDateString()}
                  </p>
                  <p className="text-xs text-orange-500 dark:text-orange-400 mt-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>{contract.address}</p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onContractSelected(contract);
                  }}
                  className="py-1 px-3 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                  style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
                >
                  View
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

// Contract Creator Component
const ContractCreator = ({ onContractCreated }) => {
  const { wallet } = useWallet();
  const [contractType, setContractType] = useState('TOKEN');
  const [availableTypes, setAvailableTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Token contract fields
  const [tokenName, setTokenName] = useState('');
  const [tokenSymbol, setTokenSymbol] = useState('');
  const [initialSupply, setInitialSupply] = useState(1000000);
  const [maxSupply, setMaxSupply] = useState('');
  const [decimals, setDecimals] = useState(8);
  
  // Crowdfunding contract fields
  const [crowdfundName, setCrowdfundName] = useState('');
  const [fundingGoal, setFundingGoal] = useState(1000);
  const [deadline, setDeadline] = useState('');
  const [description, setDescription] = useState('');
  
  // Voting contract fields
  const [voteName, setVoteName] = useState('');
  const [voteOptions, setVoteOptions] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [voteDescription, setVoteDescription] = useState('');
  
  // Fetch available contract types
  useEffect(() => {
    const fetchContractTypes = async () => {
      try {
        const contractTypes = await contractService.getContractTypes();
        setAvailableTypes(contractTypes);
      } catch (error) {
        console.error('Failed to fetch contract types:', error);
      }
    };
    
    fetchContractTypes();
  }, []);
  
  // Set default deadlines/times
  useEffect(() => {
    // Set default deadline to 30 days from now
    const thirtyDaysFromNow = new Date();
    thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);
    setDeadline(thirtyDaysFromNow.toISOString().split('T')[0]);
    
    // Set default voting period to start today and end in 7 days
    const today = new Date();
    const sevenDaysFromNow = new Date();
    sevenDaysFromNow.setDate(sevenDaysFromNow.getDate() + 7);
    
    setStartTime(today.toISOString().split('T')[0]);
    setEndTime(sevenDaysFromNow.toISOString().split('T')[0]);
  }, []);
  
  const handleDeployContract = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    
    if (!wallet || !wallet.address) {
      setError('Please connect your wallet first');
      setLoading(false);
      return;
    }
    
    try {
      let endpoint;
      let requestData = {};
      
      // Prepare request data based on contract type
      if (contractType === 'TOKEN') {
        endpoint = '/contracts/templates/token';
        requestData = {
          creator: wallet.address,
          name: tokenName,
          symbol: tokenSymbol,
          initial_supply: parseFloat(initialSupply),
          decimals: parseInt(decimals)
        };
        
        if (maxSupply) {
          requestData.max_supply = parseFloat(maxSupply);
        }
      }
      else if (contractType === 'CROWDFUND') {
        endpoint = '/contracts/templates/crowdfunding';
        // Convert deadline to timestamp
        const deadlineDate = new Date(deadline);
        
        requestData = {
          creator: wallet.address,
          name: crowdfundName,
          goal: parseFloat(fundingGoal),
          deadline: Math.floor(deadlineDate.getTime() / 1000),
          description: description
        };
      }
      else if (contractType === 'VOTING') {
        endpoint = '/contracts/templates/voting';
        // Convert dates to timestamps
        const startDate = new Date(startTime);
        const endDate = new Date(endTime);
        
        // Parse options as comma-separated list
        const options = voteOptions.split(',').map(option => option.trim());
        
        requestData = {
          creator: wallet.address,
          name: voteName,
          options: options,
          start_time: Math.floor(startDate.getTime() / 1000),
          end_time: Math.floor(endDate.getTime() / 1000),
          description: voteDescription
        };
      }
      
      // Deploy contract based on type
      let result;
      
      if (contractType === 'TOKEN') {
        result = await contractService.deployTokenContract(requestData);
      } else if (contractType === 'CROWDFUND') {
        result = await contractService.deployCrowdfundContract(requestData);
      } else if (contractType === 'VOTING') {
        result = await contractService.deployVotingContract(requestData);
      }
      
      if (result.success) {
        setSuccess(`Contract deployed at address: ${result.contractAddress}`);
        
        // Reset form
        setTokenName('');
        setTokenSymbol('');
        setInitialSupply(1000000);
        setMaxSupply('');
        setCrowdfundName('');
        setFundingGoal(1000);
        setDescription('');
        setVoteName('');
        setVoteOptions('');
        setVoteDescription('');
        
        // Notify parent
        if (onContractCreated) {
          onContractCreated();
        }
      } else {
        setError(result.message || 'Failed to deploy contract');
      }
    } catch (error) {
      console.error('Contract deployment error:', error);
      setError(error.response?.data?.message || 'Failed to deploy contract');
    } finally {
      setLoading(false);
    }
  };
  
  // Render form based on contract type
  const renderContractForm = () => {
    switch (contractType) {
      case 'TOKEN':
        return (
          <div className="space-y-4" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Token Name</label>
              <input
                type="text"
                className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
                value={tokenName}
                onChange={(e) => setTokenName(e.target.value)}
                placeholder="e.g. My Token"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Token Symbol</label>
              <input
                type="text"
                className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
                value={tokenSymbol}
                onChange={(e) => setTokenSymbol(e.target.value)}
                placeholder="e.g. MTK"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Initial Supply</label>
              <input
                type="number"
                className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
                value={initialSupply}
                onChange={(e) => setInitialSupply(e.target.value)}
                min="1"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Max Supply (optional)</label>
              <input
                type="number"
                className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
                value={maxSupply}
                onChange={(e) => setMaxSupply(e.target.value)}
                placeholder="Leave empty for unlimited supply"
                min="1"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Decimals</label>
              <input
                type="number"
                className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
                value={decimals}
                onChange={(e) => setDecimals(e.target.value)}
                min="0"
                max="18"
                required
              />
            </div>
          </div>
        );
        
      case 'CROWDFUND':
        return (
          <div className="space-y-4" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Campaign Name</label>
              <input
                type="text"
                className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
                value={crowdfundName}
                onChange={(e) => setCrowdfundName(e.target.value)}
                placeholder="e.g. My Crowdfunding Campaign"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Funding Goal (GCN)</label>
              <input
                type="number"
                className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
                value={fundingGoal}
                onChange={(e) => setFundingGoal(e.target.value)}
                min="0.01"
                step="0.01"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Deadline</label>
              <input
                type="date"
                className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Description</label>
              <textarea
                className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows="3"
                placeholder="Describe your crowdfunding campaign"
              />
            </div>
          </div>
        );
        
      case 'VOTING':
        return (
          <div className="space-y-4" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Vote Name</label>
              <input
                type="text"
                className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
                value={voteName}
                onChange={(e) => setVoteName(e.target.value)}
                placeholder="e.g. Project Direction Vote"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Vote Options (comma-separated)</label>
              <input
                type="text"
                className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
                value={voteOptions}
                onChange={(e) => setVoteOptions(e.target.value)}
                placeholder="e.g. Option A, Option B, Option C"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Start Date</label>
              <input
                type="date"
                className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">End Date</label>
              <input
                type="date"
                className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Description</label>
              <textarea
                className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
                value={voteDescription}
                onChange={(e) => setVoteDescription(e.target.value)}
                rows="3"
                placeholder="Describe the purpose of this vote"
              />
            </div>
          </div>
        );
        
      default:
        return <p style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Select a contract type to continue</p>;
    }
  };
  
  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Create New Contract</h2>
      
      {/* Contract Type Selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Contract Type</label>
        <select
          className="block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 dark:bg-gray-700 dark:text-white"
          value={contractType}
          onChange={(e) => setContractType(e.target.value)}
          style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
        >
          {availableTypes.map(type => (
            <option key={type.type} value={type.type} style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              {type.name} - {type.description}
            </option>
          ))}
        </select>
      </div>
      
      {/* Contract Form */}
      <form onSubmit={handleDeployContract}>
        {renderContractForm()}
        
        {/* Error and Success Messages */}
        {error && (
          <div className="mt-4 p-2 bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200 rounded" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            {error}
          </div>
        )}
        
        {success && (
          <div className="mt-4 p-2 bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200 rounded" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            {success}
          </div>
        )}
        
        {/* Submit Button */}
        <div className="mt-6">
          <button
            type="submit"
            className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-blue-700 dark:hover:bg-blue-800"
            disabled={loading || !wallet}
            style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
          >
            {loading ? 'Deploying...' : 'Deploy Contract'}
          </button>
        </div>
      </form>
    </div>
  );
};

// Contract Details Component
const ContractDetails = ({ contract, onBack }) => {
  const { wallet } = useWallet();
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
  
  // Get contract state
  useEffect(() => {
    const fetchContractState = async () => {
      setLoading(true);
      setError('');
      
      try {
        const state = await contractService.getContractState(contract.address);
        setState(state);
      } catch (error) {
        console.error('Error fetching contract state:', error);
        setError(error.response?.data?.message || 'Failed to load contract state');
      } finally {
        setLoading(false);
      }
    };
    
    fetchContractState();
  }, [contract.address]);
  
  // Handle token transfer
  const handleTokenTransfer = async (e) => {
    e.preventDefault();
    setTransferLoading(true);
    setTransferError('');
    setTransferSuccess('');
    
    try {
      const result = await contractService.transferTokens(
        contract.address,
        wallet.address,
        transferTo,
        parseFloat(transferAmount)
      );
      
      if (result.success) {
        setTransferSuccess(`Successfully transferred ${transferAmount} ${contract.symbol} to ${transferTo}`);
        setTransferAmount('');
        setTransferTo('');
        
        // Refresh contract state
        const state = await contractService.getContractState(contract.address);
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
        contract.address,
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
        const state = await contractService.getContractState(contract.address);
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
        contract.address,
        'vote',
        {
          option: selectedOption
        },
        wallet.address
      );
      
      if (result.success) {
        setVoteSuccess(`Successfully voted for "${selectedOption}"`);
        
        // Refresh contract state
        const state = await contractService.getContractState(contract.address);
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
          </div>
        );
        
      case 'CROWDFUND':
        const now = Math.floor(Date.now() / 1000);
        const isActive = state.deadline > now;
        const goalReached = (state.total_raised || 0) >= (state.goal || 0);
        const canWithdraw = !isActive && ((goalReached && contract.creator === wallet.address) || (!goalReached && state.contributions && state.contributions[wallet.address]));
        
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
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Your contribution: {(state.contributions && state.contributions[wallet.address]) || 0} GCN
              </p>
            </div>
            
            {isActive && (
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
        const hasVoted = state.voters && state.voters[wallet.address];
        
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
            
            {voteStarted && !voteEnded && !hasVoted && (
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
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>{contract.name}</h2>
        <button
          onClick={onBack}
          className="py-1 px-3 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
        >
          Back to List
        </button>
      </div>
      
      <div className="border-b border-gray-200 dark:border-gray-700 pb-2 mb-4">
        <p className="text-sm text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
          Type: {contract.type} • Created: {new Date(contract.creation_time * 1000).toLocaleDateString()}
        </p>
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>{contract.address}</p>
      </div>
      
      {loading ? (
        <div className="py-20 text-center">
          <p className="text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Loading contract data...</p>
        </div>
      ) : error ? (
        <div className="p-4 bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200 rounded" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
          {error}
        </div>
      ) : (
        renderContractDetails()
      )}
    </div>
  );
};

// Main Contracts Page
const Contracts = () => {
  const { wallet } = useWallet();
  const navigate = useNavigate();
  const [contracts, setContracts] = useState([]);
  const [allContracts, setAllContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingAll, setLoadingAll] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('all');
  
  // Fetch all contracts
  const fetchAllContracts = async () => {
    try {
      setLoadingAll(true);
      const contracts = await contractService.getAllContracts();
      setAllContracts(contracts);
    } catch (error) {
      console.error('Error fetching all contracts:', error);
      // Don't set error for missing API endpoint during development
      setAllContracts([]);
    } finally {
      setLoadingAll(false);
    }
  };
  
  // Fetch user's contracts
  const fetchUserContracts = async () => {
    if (!wallet || !wallet.address) {
      setContracts([]);
      setLoading(false);
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const contracts = await contractService.getContractsByCreator(wallet.address);
      setContracts(contracts);
    } catch (error) {
      console.error('Error fetching contracts:', error);
      // Don't set error for missing API endpoint during development
    } finally {
      setLoading(false);
    }
  };
  
  // Fetch contracts on mount and when wallet changes
  useEffect(() => {
    fetchUserContracts();
    fetchAllContracts();
  }, [wallet]);
  
  // Handle contract selection
  const handleContractSelected = (contract) => {
    // Navigate to contract details page
    navigate(`/app/contracts/${contract.address}`);
  };
  

  // Filter contracts by type for the current view
  const getFilteredContracts = () => {
    // For 'your' tab, we always use the user's contracts
    if (activeTab === 'your') {
      return contracts;
    }
    
    // For other tabs, we filter from allContracts
    const contractsToFilter = allContracts;
    
    // Apply type filter
    if (activeTab === 'tokens') {
      return contractsToFilter.filter(c => c.type === 'TOKEN');
    } else if (activeTab === 'crowdfunding') {
      return contractsToFilter.filter(c => c.type === 'CROWDFUND');
    } else if (activeTab === 'voting') {
      return contractsToFilter.filter(c => c.type === 'VOTING');
    }
    
    // Default to all contracts
    return contractsToFilter;
  };

  return (
    <div className="mx-0">
      {/* Header Section with New Contract Button */}
      <div className="flex flex-col space-y-0 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Contracts
            </h1>
          </div>
          
          <button
            onClick={() => navigate('/app/contracts/create')}
            className="py-1 px-3 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800"
            style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
          >
            New Contract
          </button>
        </div>
      </div>

      {/* Border below header */}
      <div className="border-b border-gray-300 dark:border-gray-700 mb-4"></div>

      {/* Tabs for filtering contracts */}
      <div className="flex border-b border-gray-300 dark:border-gray-700 mb-4 overflow-x-auto">
        {['all', 'tokens', 'crowdfunding', 'voting', 'your'].map((tab) => (
          <button
            key={tab}
            className={`py-2 px-4 text-sm font-medium border-b-2 ${
              activeTab === tab
                ? 'border-blue-500 text-blue-600 dark:border-blue-400 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
            onClick={() => setActiveTab(tab)}
            style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Contract List */}
      {!wallet && activeTab === 'your' ? (
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 text-center">
          <p className="text-gray-700 dark:text-gray-300 mb-4" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Please connect your wallet to view your contracts.</p>
          <button
            onClick={() => navigate('/app/wallet')}
            className="py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-blue-700 dark:hover:bg-blue-800"
            style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
          >
            Go to Wallet
          </button>
        </div>
      ) : activeTab === 'your' ? (
        loading ? (
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 flex items-center justify-center">
            <p className="text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Loading your contracts...</p>
          </div>
        ) : error ? (
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <div className="p-4 bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200 rounded" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              {error}
            </div>
          </div>
        ) : (
          <ContractList 
            contracts={contracts} 
            onContractSelected={handleContractSelected} 
          />
        )
      ) : (
        loadingAll ? (
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 flex items-center justify-center">
            <p className="text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Loading contracts...</p>
          </div>
        ) : (
          <ContractList 
            contracts={getFilteredContracts()} 
            onContractSelected={handleContractSelected} 
          />
        )
      )}
    </div>
  );
};

export default Contracts;