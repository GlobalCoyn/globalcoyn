import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import contractService from '../../../services/api/contractService';
import walletService from '../../../services/api/walletService';
import { useWallet } from '../../../hooks/wallet/useWallet';

const CreateContract = () => {
  const navigate = useNavigate();
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
  
  // Contract fee in GCN
  const CONTRACT_FEE = 100;
  
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
    
    // Check if wallet has enough balance for the contract fee
    if (wallet.balance < CONTRACT_FEE) {
      setError(`Insufficient balance. Contract deployment requires a fee of ${CONTRACT_FEE} GCN.`);
      setLoading(false);
      return;
    }
    
    try {
      let requestData = {};
      
      // Prepare request data based on contract type
      if (contractType === 'TOKEN') {
        requestData = {
          creator: wallet.address,
          name: tokenName,
          symbol: tokenSymbol,
          initial_supply: parseFloat(initialSupply),
          decimals: parseInt(decimals),
          fee: CONTRACT_FEE // Add contract fee
        };
        
        if (maxSupply) {
          requestData.max_supply = parseFloat(maxSupply);
        }
      }
      else if (contractType === 'CROWDFUND') {
        // Convert deadline to timestamp
        const deadlineDate = new Date(deadline);
        
        requestData = {
          creator: wallet.address,
          name: crowdfundName,
          goal: parseFloat(fundingGoal),
          deadline: Math.floor(deadlineDate.getTime() / 1000),
          description: description,
          fee: CONTRACT_FEE // Add contract fee
        };
      }
      else if (contractType === 'VOTING') {
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
          description: voteDescription,
          fee: CONTRACT_FEE // Add contract fee
        };
      }
      
      // Create a fee callback using wallet service
      const sendFeeCallback = contractService.createWalletServiceFeeCallback(walletService);
      
      // Deploy contract based on type with the fee callback
      let result;
      
      if (contractType === 'TOKEN') {
        result = await contractService.deployTokenContract(requestData, sendFeeCallback);
      } else if (contractType === 'CROWDFUND') {
        result = await contractService.deployCrowdfundContract(requestData, sendFeeCallback);
      } else if (contractType === 'VOTING') {
        result = await contractService.deployVotingContract(requestData, sendFeeCallback);
      }
      
      if (result.success) {
        setSuccess(`Contract deployed at address: ${result.contractAddress}`);
        
        // Navigate to the contract details page after 1.5 seconds
        setTimeout(() => {
          navigate(`/app/contracts/${result.contractAddress}`);
        }, 1500);
      } else {
        setError(result.message || 'Failed to deploy contract');
      }
    } catch (error) {
      console.error('Contract deployment error:', error);
      setError(error.response?.data?.message || error.message || 'Failed to deploy contract');
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
    <div className="container mx-auto px-4">
      {/* Header Section with Back Button */}
      <div className="flex flex-col space-y-0 mb-4 px-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Create New Contract
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

      {!wallet ? (
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 text-center">
          <p className="text-gray-700 dark:text-gray-300 mb-4" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Please connect your wallet to create contracts.</p>
          <button
            onClick={() => navigate('/app/wallet')}
            className="py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-blue-700 dark:hover:bg-blue-800"
            style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
          >
            Go to Wallet
          </button>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          {/* Contract Fee Notice */}
          <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-800 rounded-md">
            <h3 className="font-medium text-blue-800 dark:text-blue-300" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Contract Deployment Fee</h3>
            <p className="text-sm text-blue-600 dark:text-blue-400 mt-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Deploying a contract requires a fee of <span className="font-bold">{CONTRACT_FEE} GCN</span>. This fee is used to cover blockchain resources and prevent spam.
            </p>
            <p className="text-sm text-blue-600 dark:text-blue-400 mt-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Your current balance: <span className="font-bold">{wallet?.balance || 0} GCN</span>
            </p>
            <p className="text-sm text-blue-600 dark:text-blue-400 mt-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              <strong>Note:</strong> The contract fee will be sent as a separate transaction to address <code>1LVkyzYqPBYYhMEjxFm1dLXsFUox2gtdDr</code> after contract deployment.
            </p>
          </div>
      
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
      )}
    </div>
  );
};

export default CreateContract;