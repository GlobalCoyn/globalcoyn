import React, { useState, useEffect } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import walletService from '../services/walletService';
import EnvironmentToggle from '../components/EnvironmentToggle';

const Wallet = () => {
  const [hasWallet, setHasWallet] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [walletInfo, setWalletInfo] = useState({
    address: '',
    balance: 0,
    transactions: []
  });
  const [seedPhrase, setSeedPhrase] = useState('');
  const [privateKeyWif, setPrivateKeyWif] = useState('');
  const [showSeedPhrase, setShowSeedPhrase] = useState(false);
  const [showPrivateKey, setShowPrivateKey] = useState(false);
  
  // Transaction form state
  const [recipient, setRecipient] = useState('');
  const [amount, setAmount] = useState('');
  const [fee, setFee] = useState('0.001');
  const [isTransactionModalOpen, setIsTransactionModalOpen] = useState(false);
  
  // Import wallet state
  const [importMethod, setImportMethod] = useState('');
  const [importValue, setImportValue] = useState('');
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  
  // Toast notification
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  useEffect(() => {
    // Check if user has a wallet
    checkWalletExists();
  }, []);
  
  const checkWalletExists = async () => {
    try {
      setLoading(true);
      // Check for stored wallet in local storage first (most reliable source)
      const storedWallets = walletService.getStoredWallets();
      
      if (storedWallets && storedWallets.length > 0) {
        // We have wallets in localStorage - use the current one if set
        const currentWallet = walletService.getCurrentWallet();
        const walletToLoad = currentWallet && storedWallets.includes(currentWallet) 
          ? currentWallet 
          : storedWallets[0];
          
        // Load the wallet info (with fallbacks built in)
        await loadWalletInfo(walletToLoad);
        setHasWallet(true);
        setLoading(false);
        return;
      }
      
      // If no wallets in localStorage, try the backend
      try {
        const wallets = await walletService.getWallets();
        if (wallets && wallets.length > 0) {
          await loadWalletInfo(wallets[0]);
          setHasWallet(true);
        } else {
          // No wallets found anywhere
          setHasWallet(false);
        }
      } catch (apiErr) {
        console.warn('API connectivity error, showing wallet creation screen:', apiErr);
        // Show wallet creation screen if API fails
        setHasWallet(false);
      }
    } catch (error) {
      console.error('Error checking wallet:', error);
      // Don't show an error to user, just show wallet creation screen
      setHasWallet(false);
    } finally {
      setLoading(false);
    }
  };
  
  const loadWalletInfo = async (address) => {
    try {
      // Get wallet balance
      const balanceInfo = await walletService.getBalance(address);
      
      // Get transactions
      const txInfo = await walletService.getTransactions(address);
      
      // Update wallet info
      setWalletInfo({
        address,
        balance: balanceInfo.balance,
        transactions: txInfo.transactions || []
      });
      
      // Store as current wallet
      walletService.setCurrentWallet(address);
      
      // If we get here, the wallet is loaded
      return true;
    } catch (error) {
      console.error('Error loading wallet info:', error);
      // Don't set global error - just update wallet with default values
      setWalletInfo({
        address,
        balance: 0,
        transactions: []
      });
      
      // Still store this as current wallet
      walletService.setCurrentWallet(address);
      
      // Return false to indicate failure but don't stop the flow
      return false;
    }
  };

  const createNewWallet = async () => {
    try {
      setLoading(true);
      const result = await walletService.createWallet();
      
      if (result.success) {
        // Set wallet info first so address is visible in the modal
        setWalletInfo({
          ...walletInfo,
          address: result.address
        });
        
        // Ensure we get the seed phrase in the expected format and show it
        console.log('Wallet created with result:', result);
        // Always show seed phrase popup - required for user to secure their wallet!
        if (result.seedPhrase) {
          // First hide the popup if it's already showing (to trigger a re-render)
          setShowSeedPhrase(false);
          
          // Force display the popup in multiple ways
          // 1. Set the state variable
          setSeedPhrase(result.seedPhrase);
          
          // 2. Use setTimeout with increasing delays to ensure it shows
          setTimeout(() => {
            setShowSeedPhrase(true);
            console.log('Seed phrase popup should be visible now (delay 100ms)');
            
            // 3. Directly show the modal using DOM manipulation as a fallback
            const modal = document.getElementById('seed-phrase-modal');
            if (modal) {
              modal.classList.remove('hidden');
              console.log('Forced seed phrase modal to show via DOM');
            }
          }, 100);
          
          // Try again with longer delay as extra safety
          setTimeout(() => {
            if (!showSeedPhrase) {
              setShowSeedPhrase(true);
              console.log('Seed phrase popup retry (delay 500ms)');
              
              const modal = document.getElementById('seed-phrase-modal');
              if (modal) {
                modal.classList.remove('hidden');
                console.log('Forced seed phrase modal again via DOM');
              }
            }
          }, 500);
        } else {
          console.error('No seed phrase returned from wallet creation');
          showToast('Warning: No seed phrase was returned. Please backup your wallet carefully!', 'error');
        }
        
        // Load complete wallet info after showing the seed phrase
        await loadWalletInfo(result.address);
        setHasWallet(true);
        showToast('Wallet created successfully!', 'success');
      }
    } catch (error) {
      console.error('Error creating wallet:', error);
      setError('Failed to create wallet');
      showToast('Failed to create wallet', 'error');
    } finally {
      setLoading(false);
    }
  };
  
  const importWallet = async () => {
    try {
      setLoading(true);
      let result;
      
      if (importMethod === 'seed') {
        result = await walletService.importWalletFromSeed(importValue);
      } else if (importMethod === 'privateKey') {
        result = await walletService.importWalletFromPrivateKey(importValue);
      }
      
      if (result && result.success) {
        await loadWalletInfo(result.address);
        setHasWallet(true);
        setIsImportModalOpen(false);
        setImportValue('');
        
        // Force hide modal using DOM
        const modal = document.getElementById('import-modal');
        if (modal) {
          modal.classList.add('hidden');
          console.log('Forced import modal to hide after successful import');
        }
        
        showToast('Wallet imported successfully!', 'success');
      }
    } catch (error) {
      console.error('Error importing wallet:', error);
      setError('Failed to import wallet');
      showToast('Failed to import wallet', 'error');
    } finally {
      setLoading(false);
    }
  };
  
  const backupWallet = async () => {
    try {
      setLoading(true);
      // Show a message to indicate the process has started
      showToast('Retrieving private key...', 'info');
      
      // Log the wallet address being used
      console.log('Attempting to export private key for wallet:', walletInfo.address);
      
      const result = await walletService.exportPrivateKey(walletInfo.address);
      
      // Debug: Log the API response
      console.log('Export private key API response:', result);
      
      // Check for various possible response formats
      if (result?.privateKey) {
        // Standard format
        setPrivateKeyWif(result.privateKey);
        setShowPrivateKey(true);
      } else if (result?.private_key) {
        // Alternative format with snake_case
        setPrivateKeyWif(result.private_key);
        setShowPrivateKey(true);
      } else if (result?.success && result?.data?.privateKey) {
        // Nested format
        setPrivateKeyWif(result.data.privateKey);
        setShowPrivateKey(true);
      } else if (typeof result === 'string' && result.length > 30) {
        // Direct string response
        setPrivateKeyWif(result);
        setShowPrivateKey(true);
      } else {
        // No recognizable private key format
        console.error('Unrecognized API response format:', result);
        showToast('No private key found in API response. Check console for details.', 'error');
        return;
      }
      
      // If we get here, we have a private key to show
      console.log('Private key retrieved successfully, displaying modal');
      
      // Make sure the modal is displayed
      setTimeout(() => {
        const modal = document.getElementById('private-key-modal');
        if (modal) {
          modal.style.display = 'flex';
          console.log('Private key modal displayed via style');
        } else {
          console.error('Could not find private-key-modal element');
        }
      }, 100);
    } catch (error) {
      console.error('Error backing up wallet:', error);
      setError(null); // Don't set global error
      
      // Try to extract the most useful error message
      let errorMsg = 'Unknown error';
      if (error.response?.data?.error) {
        errorMsg = error.response.data.error;
      } else if (error.response?.data?.message) {
        errorMsg = error.response.data.message;
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      showToast(`Failed to backup wallet: ${errorMsg}`, 'error');
    } finally {
      setLoading(false);
    }
  };
  
  const sendTransaction = async () => {
    try {
      setLoading(true);
      
      // Validate inputs
      if (!recipient || !amount || parseFloat(amount) <= 0) {
        showToast('Please enter valid recipient and amount', 'error');
        return;
      }
      
      // Validate that amount is not greater than balance
      if (parseFloat(amount) > walletInfo.balance) {
        showToast('Insufficient balance for this transaction', 'error');
        return;
      }
      
      // Show sending message
      showToast('Signing and sending transaction...', 'info');
      
      // Send transaction
      const result = await walletService.sendTransaction(
        walletInfo.address,
        recipient,
        parseFloat(amount),
        parseFloat(fee)
      );
      
      if (result && result.transaction_id) {
        setIsTransactionModalOpen(false);
        showToast('Transaction sent successfully!', 'success');
        
        // Clear form fields
        setRecipient('');
        setAmount('');
        
        // Reload wallet info after transaction
        await loadWalletInfo(walletInfo.address);
      } else {
        showToast('Transaction may have failed. Please check your transaction history.', 'warning');
      }
    } catch (error) {
      console.error('Error sending transaction:', error);
      setError(null);  // Clear global error
      
      // Show detailed error message from API if available
      const errorMessage = error.error || error.message || 'Unknown error occurred';
      showToast(`Failed to send transaction: ${errorMessage}`, 'error');
    } finally {
      setLoading(false);
    }
  };
  
  const showToast = (message, type = 'success') => {
    setToast({ show: true, message, type });
    
    // Hide toast after 3 seconds
    setTimeout(() => {
      setToast({ show: false, message: '', type: 'success' });
    }, 3000);
  };
  
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
      .then(() => showToast('Copied to clipboard!', 'success'))
      .catch(err => console.error('Failed to copy:', err));
  };

  // Wallet creation UI
  const WalletCreation = () => (
    <div className="space-y-0">
      <div className="flex flex-col space-y-0 mb-4 px-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Create or Import a Wallet</h1>
            <div className="text-sm text-gray-500 dark:text-gray-400 mt-0">
              Network Mode: <span className="font-medium">{localStorage.getItem('gcn_environment') === 'production' || window.location.hostname === 'globalcoyn.com' ? 'Production' : 'Development'}</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Create New Wallet Section */}
      <div className="border-t border-gray-300 dark:border-gray-700">
        <div className="px-6 py-2 border-b border-gray-200 dark:border-gray-700 mb-0">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>Create New Wallet</h2>
        </div>
        <div className="px-6 py-4">
          <p className="text-gray-600 dark:text-gray-400 mb-4" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            Generate a new GlobalCoyn wallet for sending, receiving, and mining GCN.
          </p>
          <button 
            className="btn-primary"
            onClick={createNewWallet}
            disabled={loading}
            style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
          >
            {loading ? 'Creating...' : 'Create New Wallet'}
          </button>
        </div>
      </div>
      
      {/* Import Wallet Section */}
      <div className="border-t border-gray-300 dark:border-gray-700 mt-4">
        <div className="px-6 py-2 border-b border-gray-200 dark:border-gray-700 mb-0">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>Import Existing Wallet</h2>
        </div>
        <div className="px-6 py-4">
          <p className="text-gray-600 dark:text-gray-400 mb-4" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            Import a wallet from a recovery seed phrase or private key.
          </p>
          <div className="flex space-x-4">
            <button 
              className="btn-secondary text-xs py-1 px-3 whitespace-nowrap"
              onClick={() => {
                setImportMethod('seed');
                setIsImportModalOpen(true);
              }}
              disabled={loading}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              Import with Seed Phrase
            </button>
            <button 
              className="btn-secondary text-xs py-1 px-3 whitespace-nowrap"
              onClick={() => {
                setImportMethod('privateKey');
                setIsImportModalOpen(true);
              }}
              disabled={loading}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              Import with Private Key
            </button>
          </div>
        </div>
      </div>
      
      {/* Import Wallet Modal */}
      <div id="import-modal" className={`fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50 ${isImportModalOpen ? '' : 'hidden'}`}>
        <div className="bg-white dark:bg-gray-800 p-6 border border-gray-300 dark:border-gray-600 shadow-lg max-w-md w-full" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
          <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            Import Wallet {importMethod === 'seed' ? 'from Seed Phrase' : 'from Private Key'}
          </h3>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              {importMethod === 'seed' ? 'Enter your 12-word seed phrase' : 'Enter your private key (WIF format)'}
            </label>
            <textarea
              className="w-full p-2 border border-gray-300 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              rows="3"
              placeholder={importMethod === 'seed' ? 'word1 word2 word3...' : 'GCN_xxxxxxxx...'}
              value={importValue}
              onChange={(e) => setImportValue(e.target.value)}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            />
          </div>
          
          <div className="flex justify-end space-x-3">
            <button 
              className="btn-secondary text-xs py-1 px-3"
              onClick={() => {
                setIsImportModalOpen(false);
                setImportValue('');
                
                // Force hide modal using DOM
                const modal = document.getElementById('import-modal');
                if (modal) {
                  modal.classList.add('hidden');
                  console.log('Forced import modal to hide via DOM');
                }
              }}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              Cancel
            </button>
            <button 
              className="btn-primary text-xs py-1 px-3"
              onClick={importWallet}
              disabled={loading || !importValue}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              {loading ? 'Importing...' : 'Import Wallet'}
            </button>
          </div>
        </div>
      </div>
      
      {/* Seed Phrase Modal - Forced to display when a wallet is created */}
      <div id="seed-phrase-modal" className={`fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50 ${showSeedPhrase ? '' : 'hidden'}`}>
        <div className="bg-white dark:bg-gray-800 p-6 border border-gray-300 dark:border-gray-600 shadow-lg max-w-md w-full">
          <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Wallet Created</h3>
          
          <div className="mb-4">
            <p className="text-gray-900 dark:text-white mb-4" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Your wallet address:<br/>
              <span className="font-mono break-words text-sm text-blue-500 dark:text-blue-400">{walletInfo.address}</span>
            </p>
            
            <p className="text-red-600 font-bold mb-2" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              IMPORTANT: Please write down your recovery seed phrase and keep it safe.
            </p>
            <p className="text-gray-600 dark:text-gray-400 mb-2" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              This is the ONLY way to recover your wallet if you lose access:
            </p>
            
            <div className="bg-gray-100 dark:bg-gray-700 p-4 border border-gray-300 dark:border-gray-600 mb-4">
              <p className="font-mono break-words text-sm text-orange-500 dark:text-orange-400">{seedPhrase || "Loading seed phrase..."}</p>
            </div>
            
            <p className="text-red-600 dark:text-red-400 font-bold" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Never share this seed phrase with anyone!
            </p>
            
            <button
              className="btn-secondary w-full mt-4 mb-4 text-xs py-1 px-3"
              onClick={() => copyToClipboard(seedPhrase)}
              disabled={!seedPhrase}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              Copy to Clipboard
            </button>
          </div>
          
          <div className="flex justify-end">
            <button 
              className="btn-primary text-xs py-1 px-3"
              onClick={() => {
                console.log("Closing seed phrase dialog");
                setShowSeedPhrase(false);
                setSeedPhrase('');
              }}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              I've Saved My Seed Phrase
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // Wallet interface UI
  const WalletInterface = () => (
    <div className="space-y-6">
      {/* Seed Phrase Modal for New Address Creation */}
      <div id="wallet-interface-seed-modal" className={`fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50 ${showSeedPhrase ? '' : 'hidden'}`}>
        <div className="bg-white dark:bg-gray-800 p-6 border border-gray-300 dark:border-gray-600 shadow-lg max-w-md w-full">
          <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>New Address Created</h3>
          
          <div className="mb-4">
            <p className="text-gray-900 dark:text-white mb-4" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Your new wallet address:<br/>
              <span className="font-mono break-words text-sm text-blue-500 dark:text-blue-400">{walletInfo.address}</span>
            </p>
            
            <p className="text-red-600 font-bold mb-2" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              IMPORTANT: Please write down your recovery seed phrase and keep it safe.
            </p>
            <p className="text-gray-600 dark:text-gray-400 mb-2" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              This is the ONLY way to recover your wallet if you lose access:
            </p>
            
            <div className="bg-gray-100 dark:bg-gray-700 p-4 border border-gray-300 dark:border-gray-600 mb-4">
              <p className="font-mono break-words text-sm text-orange-500 dark:text-orange-400">{seedPhrase || "Loading seed phrase..."}</p>
            </div>
            
            <p className="text-red-600 dark:text-red-400 font-bold" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Never share this seed phrase with anyone!
            </p>
            
            <button
              className="btn-secondary w-full mt-4 mb-4 text-xs py-1 px-3"
              onClick={() => copyToClipboard(seedPhrase)}
              disabled={!seedPhrase}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              Copy to Clipboard
            </button>
          </div>
          
          <div className="flex justify-end">
            <button 
              className="btn-primary text-xs py-1 px-3"
              onClick={() => {
                console.log("Closing seed phrase dialog from wallet interface");
                setShowSeedPhrase(false);
                setSeedPhrase('');
              }}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              I've Saved My Seed Phrase
            </button>
          </div>
        </div>
      </div>
      
      <div className="flex flex-col space-y-0 mb-4 px-6">
        <div className="flex items-center justify-between">
          <div className="w-full">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>My Wallet</h1>
            <div className="text-sm text-gray-500 dark:text-gray-400 mt-0" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Network Mode: <span className="font-medium">{localStorage.getItem('gcn_environment') === 'production' || window.location.hostname === 'globalcoyn.com' ? 'Production' : 'Development'}</span>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <button 
              className="btn-primary flex items-center text-xs py-1 px-3 whitespace-nowrap"
              onClick={() => setIsTransactionModalOpen(true)}
              disabled={loading}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              Send
            </button>
            <button 
              className="btn-secondary flex items-center text-xs py-1 px-3 whitespace-nowrap"
              onClick={() => {
                // Show QR code for wallet address
                const modal = document.getElementById('receive-modal');
                if (modal) modal.classList.remove('hidden');
              }}
              disabled={loading}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              Receive
            </button>
            <div className="relative group">
              <button 
                className="btn-secondary flex items-center text-xs py-1 px-3 whitespace-nowrap"
                onClick={() => {
                  const dropdown = document.getElementById('import-dropdown');
                  if (dropdown) dropdown.classList.toggle('hidden');
                }}
                disabled={loading}
                style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
              >
                Import Wallet
              </button>
              <div id="import-dropdown" className="hidden absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 shadow-lg z-10 border border-gray-200 dark:border-gray-700">
                <div className="py-1">
                  <button
                    className="w-full text-left px-4 py-2 text-xs text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                    onClick={() => {
                      // Set method and show modal
                      setImportMethod('seed');
                      setIsImportModalOpen(true);
                      setImportValue('');
                      
                      // Hide dropdown
                      const dropdown = document.getElementById('import-dropdown');
                      if (dropdown) dropdown.classList.add('hidden');
                      
                      // Force show modal using DOM
                      const modal = document.getElementById('import-modal');
                      if (modal) {
                        modal.classList.remove('hidden');
                        console.log('Forced import modal to show via DOM');
                      }
                    }}
                    style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
                  >
                    Import with Seed Phrase
                  </button>
                  <button
                    className="w-full text-left px-4 py-2 text-xs text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                    onClick={() => {
                      // Set method and show modal
                      setImportMethod('privateKey');
                      setIsImportModalOpen(true);
                      setImportValue('');
                      
                      // Hide dropdown
                      const dropdown = document.getElementById('import-dropdown');
                      if (dropdown) dropdown.classList.add('hidden');
                      
                      // Force show modal using DOM
                      const modal = document.getElementById('import-modal');
                      if (modal) {
                        modal.classList.remove('hidden');
                        console.log('Forced import modal to show via DOM');
                      }
                    }}
                    style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
                  >
                    Import with Private Key
                  </button>
                </div>
              </div>
            </div>
            <button 
              className="btn-secondary flex items-center text-xs py-1 px-3 whitespace-nowrap"
              onClick={backupWallet}
              disabled={loading}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              Backup Wallet
            </button>
          </div>
        </div>
      </div>
      
      {/* Wallet Overview Card with Address Selection */}
      <div className="border-t border-gray-300 dark:border-gray-700">
        <div className="px-6 py-3">
          <div className="flex flex-row justify-between items-center">
            {/* Balance Section */}
            <div className="flex flex-col justify-center">
              <h3 className="text-sm text-gray-500 dark:text-gray-400 mb-0" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Balance</h3>
              <p className="text-2xl font-bold text-green-600" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                {loading ? 'Loading...' : `${walletInfo.balance.toFixed(8)} GCN`}
              </p>
            </div>
            
            {/* Address with Selector */}
            <div className="flex flex-col items-end">
              <h3 className="text-sm text-gray-500 dark:text-gray-400 mb-0" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Wallet Address</h3>
              <div className="flex items-center space-x-2">
                <select 
                  className="p-1 border border-gray-300 dark:bg-gray-700 dark:border-gray-600 dark:text-white w-56"
                  value={walletInfo.address || ''}
                  onChange={(e) => {
                    if (e.target.value) {
                      loadWalletInfo(e.target.value);
                    }
                  }}
                  disabled={loading}
                  style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
                >
                  {walletService.getStoredWallets().map(address => (
                    <option key={address} value={address} style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                      {address.substring(0, 10)}...{address.substring(address.length - 8)}
                    </option>
                  ))}
                </select>
                <button
                  className="btn-secondary text-xs py-1 px-2 whitespace-nowrap"
                  onClick={() => copyToClipboard(walletInfo.address)}
                  disabled={!walletInfo.address}
                  style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
                >
                  Copy
                </button>
                <button
                  className="btn-secondary text-xs py-1 px-2 whitespace-nowrap"
                  onClick={async () => {
                    try {
                      setLoading(true);
                      // Create a new address in the current wallet
                      const result = await walletService.createWallet();
                      if (result.success) {
                        // Also show the seed phrase when creating a new address
                        if (result.seedPhrase) {
                          // First hide the popup if it's already showing (to trigger a re-render)
                          setShowSeedPhrase(false);
                          
                          // Force display the popup in multiple ways
                          // 1. Set the state variable
                          setSeedPhrase(result.seedPhrase);
                          
                          // 2. Use setTimeout with increasing delays to ensure it shows
                          setTimeout(() => {
                            setShowSeedPhrase(true);
                            console.log('Seed phrase popup should be visible now (delay 100ms)');
                            
                            // 3. Directly show the modal using DOM manipulation as a fallback
                            const modal = document.getElementById('wallet-interface-seed-modal');
                            if (modal) {
                              modal.classList.remove('hidden');
                              console.log('Forced wallet interface seed modal to show via DOM');
                            }
                          }, 100);
                          
                          // Try again with longer delay as extra safety
                          setTimeout(() => {
                            if (!showSeedPhrase) {
                              setShowSeedPhrase(true);
                              console.log('Seed phrase popup retry (delay 500ms)');
                              
                              const modal = document.getElementById('wallet-interface-seed-modal');
                              if (modal) {
                                modal.classList.remove('hidden');
                                console.log('Forced wallet interface seed modal again via DOM');
                              }
                            }
                          }, 500);
                        }
                        
                        showToast('New wallet address created successfully!', 'success');
                        await loadWalletInfo(result.address);
                      }
                    } catch (error) {
                      console.error('Error creating new address:', error);
                      showToast('Failed to create new address', 'error');
                    } finally {
                      setLoading(false);
                    }
                  }}
                  disabled={loading}
                  style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
                >
                  Create New Address
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Transaction History Card */}
      <div className="border-t border-gray-300 dark:border-gray-700 mt-4">
        <div className="px-6 py-2 border-b border-gray-200 dark:border-gray-700 mb-0">
          <div className="flex items-center">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white text-left mt-4" style={{ fontFamily: 'Helvetica, Arial, sans-serif', marginBottom: '0' }}>Transaction History</h2>
            <span className="text-sm text-gray-500 dark:text-gray-400 ml-2 mt-4" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              ({walletInfo.transactions.length})
            </span>
          </div>
        </div>
        <div className="p-0">
          {loading ? (
            <div className="text-center py-6">
              <p className="text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Loading transactions...</p>
            </div>
          ) : walletInfo.transactions.length === 0 ? (
            <div className="text-center py-6">
              <p className="text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>No transactions yet.</p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                Transactions will appear here once you send or receive GCN.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Time</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Address</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Transaction ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Status</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200 dark:bg-gray-800 dark:divide-gray-700">
                  {walletInfo.transactions.map((tx) => {
                    const isSending = tx.from === walletInfo.address;
                    return (
                      <tr 
                        key={tx.id} 
                        className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
                        onClick={() => {
                          // Only navigate if we have a real transaction ID, not a placeholder
                          if (tx.id && !tx.id.startsWith('tx_') && !tx.id.startsWith('mempool_')) {
                            window.location.href = `/app/explorer/transaction/${tx.id}`;
                          } else {
                            // Show alert for placeholder IDs
                            alert('Transaction details are not available for this transaction. Only transactions with real IDs can be viewed in the explorer.');
                          }
                        }}
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${isSending ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'}`} style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                            {isSending ? 'Sent' : 'Received'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                          {new Date(tx.timestamp).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                          <span className={isSending ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}>
                            {isSending ? '-' : '+'}{tx.amount.toFixed(8)} GCN
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-500 dark:text-blue-400">
                          <div 
                            className="truncate max-w-xs font-mono cursor-pointer hover:underline" 
                            title={isSending ? tx.to : tx.from}
                            onClick={(e) => {
                              // Stop propagation to prevent triggering row click
                              e.stopPropagation();
                              // Navigate to address details in explorer
                              window.location.href = `/app/explorer/address/${isSending ? tx.to : tx.from}`;
                            }}
                          >
                            {isSending ? tx.to : tx.from}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div 
                            className="font-mono text-orange-500 dark:text-orange-400 truncate max-w-xs cursor-pointer hover:underline"
                            title={tx.id}
                            onClick={(e) => {
                              // Stop propagation to prevent triggering row click
                              e.stopPropagation();
                              // Navigate to transaction details in explorer
                              window.location.href = `/app/explorer/transaction/${tx.id}`;
                            }}
                          >
                            {tx.id ? `${tx.id.substring(0, 8)}...${tx.id.substring(tx.id.length - 8)}` : 'Unknown'}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span 
                            className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 cursor-pointer hover:bg-blue-200 dark:hover:bg-blue-800" 
                            style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
                            onClick={(e) => {
                              // Stop propagation to prevent triggering row click
                              e.stopPropagation();
                              // Navigate to transaction details in explorer
                              window.location.href = `/app/explorer/transaction/${tx.id}`;
                            }}
                          >
                            {tx.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Send Transaction Modal */}
      {isTransactionModalOpen && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
          <div className="bg-white dark:bg-gray-800 p-6 border border-gray-300 dark:border-gray-600 shadow-lg max-w-md w-full">
            <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Send GCN</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                  From Address
                </label>
                <input
                  type="text"
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-700 dark:text-white"
                  value={walletInfo.address}
                  disabled
                  style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                  Recipient Address
                </label>
                <input
                  type="text"
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  placeholder="Enter recipient wallet address"
                  value={recipient}
                  onChange={(e) => setRecipient(e.target.value)}
                  style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                  Amount (GCN)
                </label>
                <input
                  type="number"
                  step="0.00000001"
                  min="0.00000001"
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  placeholder="0.00000000"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
                />
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                  Available: {walletInfo.balance.toFixed(8)} GCN
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                  Transaction Fee (GCN)
                </label>
                <input
                  type="number"
                  step="0.00000001"
                  min="0.00000001"
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  value={fee}
                  onChange={(e) => setFee(e.target.value)}
                  style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
                />
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                  Recommended fee: 0.001 GCN
                </p>
              </div>
            </div>
            
            <div className="mt-6 flex justify-end space-x-3">
              <button 
                className="btn-secondary text-xs py-1 px-3"
                onClick={() => setIsTransactionModalOpen(false)}
                style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
              >
                Cancel
              </button>
              <button 
                className="btn-primary text-xs py-1 px-3"
                onClick={sendTransaction}
                disabled={loading || !recipient || !amount || parseFloat(amount) <= 0 || parseFloat(amount) > walletInfo.balance}
                style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
              >
                {loading ? 'Sending...' : 'Send Transaction'}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Receive Modal - QR Code */}
      <div id="receive-modal" className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50 hidden">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg max-w-md w-full">
          <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Receive GCN</h3>
          
          <div className="flex flex-col items-center space-y-4">
            <div className="bg-white p-4 rounded-lg">
              <QRCodeSVG 
                value={walletInfo.address} 
                size={200}
                bgColor={"#FFFFFF"}
                fgColor={"#000000"}
                level={"L"}
                includeMargin={false}
              />
            </div>
            
            <div className="w-full">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Your Wallet Address
              </label>
              <div className="flex">
                <input
                  type="text"
                  className="flex-grow p-2 border rounded-l-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  value={walletInfo.address}
                  readOnly
                />
                <button 
                  className="btn-secondary rounded-l-none"
                  onClick={() => copyToClipboard(walletInfo.address)}
                >
                  Copy
                </button>
              </div>
            </div>
            
            <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
              Share this address to receive GCN from other users.
            </p>
          </div>
          
          <div className="mt-6 flex justify-end">
            <button 
              className="btn-primary"
              onClick={() => {
                const modal = document.getElementById('receive-modal');
                if (modal) modal.classList.add('hidden');
              }}
            >
              Close
            </button>
          </div>
        </div>
      </div>
      
      {/* Import Wallet Modal */}
      <div id="wallet-import-modal" className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50" style={{ display: isImportModalOpen ? 'flex' : 'none' }}>
        <div className="bg-white dark:bg-gray-800 p-6 border border-gray-300 dark:border-gray-600 shadow-lg max-w-md w-full" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
          <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            Import Wallet {importMethod === 'seed' ? 'from Seed Phrase' : 'from Private Key'}
          </h3>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              {importMethod === 'seed' ? 'Enter your 12-word seed phrase' : 'Enter your private key (WIF format)'}
            </label>
            <textarea
              className="w-full p-2 border border-gray-300 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              rows="3"
              placeholder={importMethod === 'seed' ? 'word1 word2 word3...' : 'GCN_xxxxxxxx...'}
              value={importValue}
              onChange={(e) => setImportValue(e.target.value)}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            />
          </div>
          
          <div className="flex justify-end space-x-3">
            <button 
              className="btn-secondary text-xs py-1 px-3"
              onClick={() => {
                setIsImportModalOpen(false);
                setImportValue('');
              }}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              Cancel
            </button>
            <button 
              className="btn-primary text-xs py-1 px-3"
              onClick={importWallet}
              disabled={loading || !importValue}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              {loading ? 'Importing...' : 'Import Wallet'}
            </button>
          </div>
        </div>
      </div>
      
      {/* Private Key Modal */}
      <div id="private-key-modal" className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50" style={{ display: showPrivateKey ? 'flex' : 'none' }}>
        <div className="bg-white dark:bg-gray-800 p-6 border border-gray-300 dark:border-gray-600 shadow-lg max-w-md w-full" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
          <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Your Private Key</h3>
          
          <div className="mb-4">
            <div className="px-4 py-2 bg-red-100 dark:bg-red-900 border-l-4 border-red-500 mb-4">
              <p className="text-red-700 dark:text-red-300 font-bold mb-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                WARNING: Never share your private key with anyone!
              </p>
              <p className="text-red-600 dark:text-red-400 text-sm" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
                Anyone with this key can access and spend your funds.
              </p>
            </div>
            
            <div className="bg-gray-100 dark:bg-gray-700 p-4 border border-gray-300 dark:border-gray-600 mb-4">
              <p className="font-mono break-words text-sm text-orange-500 dark:text-orange-400">{privateKeyWif || "Loading private key..."}</p>
            </div>
            
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              This is your wallet's private key in WIF format. You can use it to recover your wallet on any device. Keep it in a secure place.
            </p>
            
            <button
              className="btn-secondary w-full mb-4 text-xs py-1 px-3"
              onClick={() => copyToClipboard(privateKeyWif)}
              disabled={!privateKeyWif}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              Copy to Clipboard
            </button>
          </div>
          
          <div className="flex justify-end">
            <button 
              className="btn-primary text-xs py-1 px-3"
              onClick={() => {
                setShowPrivateKey(false);
                setPrivateKeyWif('');
              }}
              style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // Toast notification
  const Toast = () => {
    if (!toast.show) return null;
    
    let bgColor;
    switch (toast.type) {
      case 'success':
        bgColor = 'bg-green-500';
        break;
      case 'error':
        bgColor = 'bg-red-500';
        break;
      case 'warning':
        bgColor = 'bg-yellow-500';
        break;
      case 'info':
        bgColor = 'bg-blue-500';
        break;
      default:
        bgColor = 'bg-green-500';
    }
    
    return (
      <div className={`fixed bottom-4 right-4 p-4 rounded-md text-white ${bgColor} shadow-lg z-50`}>
        {toast.message}
      </div>
    );
  };

  // Render loading state or error
  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600 dark:text-red-400">{error}</p>
        <button 
          className="btn-primary mt-4"
          onClick={() => window.location.reload()}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <>
      {loading && !hasWallet ? (
        <div className="text-center py-8">
          <p className="text-gray-600 dark:text-gray-400">Loading wallet...</p>
        </div>
      ) : hasWallet ? (
        <WalletInterface />
      ) : (
        <WalletCreation />
      )}
      
      <Toast />
      <EnvironmentToggle />
    </>
  );
};

export default Wallet;