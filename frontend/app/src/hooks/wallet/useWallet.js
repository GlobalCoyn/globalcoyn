import { useState, useEffect } from 'react';
import walletService from '../../services/api/walletService';

export const useWallet = () => {
  const [wallet, setWallet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
      } else {
        // No wallets found
        setWallet(null);
      }
    } catch (error) {
      console.error('Error checking wallet:', error);
      setError('Failed to check wallet status');
      setWallet(null);
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
      const walletData = {
        address,
        balance: balanceInfo.balance,
        transactions: txInfo.transactions || []
      };

      setWallet(walletData);
      
      // Store as current wallet
      walletService.setCurrentWallet(address);
      
      // If we get here, the wallet is loaded
      return true;
    } catch (error) {
      console.error('Error loading wallet info:', error);
      
      // Set wallet with default values
      setWallet({
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

  const createWallet = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await walletService.createWallet();
      
      if (result.success) {
        // Load the wallet info to get balance and transactions
        await loadWalletInfo(result.address);
        return result;
      } else {
        throw new Error('Failed to create wallet');
      }
    } catch (error) {
      console.error('Error creating wallet:', error);
      setError('Failed to create wallet');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const importWalletFromSeed = async (seedPhrase) => {
    try {
      setLoading(true);
      setError(null);
      const result = await walletService.importWalletFromSeed(seedPhrase);
      
      if (result.success) {
        // Load the wallet info to get balance and transactions
        await loadWalletInfo(result.address);
        return result;
      } else {
        throw new Error('Failed to import wallet');
      }
    } catch (error) {
      console.error('Error importing wallet:', error);
      setError('Failed to import wallet');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const importWalletFromPrivateKey = async (privateKey) => {
    try {
      setLoading(true);
      setError(null);
      const result = await walletService.importWalletFromPrivateKey(privateKey);
      
      if (result.success) {
        // Load the wallet info to get balance and transactions
        await loadWalletInfo(result.address);
        return result;
      } else {
        throw new Error('Failed to import wallet');
      }
    } catch (error) {
      console.error('Error importing wallet:', error);
      setError('Failed to import wallet');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const clearWallet = () => {
    walletService.clearWalletData();
    setWallet(null);
  };

  const refreshWallet = async () => {
    if (wallet && wallet.address) {
      return loadWalletInfo(wallet.address);
    }
    return false;
  };

  return {
    wallet,
    loading,
    error,
    createWallet,
    importWalletFromSeed,
    importWalletFromPrivateKey,
    clearWallet,
    refreshWallet
  };
};