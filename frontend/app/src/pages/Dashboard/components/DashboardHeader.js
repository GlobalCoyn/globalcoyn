import React from 'react';
import Button from '../../../components/common/Button/Button';
import './DashboardHeader.css';

const DashboardHeader = ({ 
  onSendGCN, 
  onCreateWallet, 
  onImportWallet, 
  hasWallet = false, 
  blockchainInfo, 
  walletBalance, 
  onBack,
  networkStats,
  allTransactions,
  mempoolStats
}) => {
  // Format large numbers with commas
  const formatNumber = (num) => {
    return num ? num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",") : '0';
  };

  // Calculate GCN circulation like HomePage.js does
  const calculateGCNCirculation = () => {
    const chainLength = blockchainInfo?.chain_length || 0;
    return chainLength * 50; // 50 GCN per block
  };

  return (
    <div className="dashboard-header">
      {/* Top Navigation Bar */}
      <div className="dashboard-header__nav">
        <div className="dashboard-header__nav-left">
          <button className="dashboard-header__back-button" onClick={onBack}>
            <BackArrowIcon />
          </button>
          <div className="dashboard-header__title" style={{ paddingLeft: '1rem' }}>
            <h1>Dashboard</h1>
          </div>
        </div>
        
        <div className="dashboard-header__nav-actions">
          {hasWallet ? (
            <Button 
              variant="primary" 
              onClick={onSendGCN}
              icon={<SendIcon />}
              style={{ 
                padding: '0.75rem 1.5rem',
                borderRadius: '0.5rem',
                fontSize: '0.875rem',
                fontWeight: '500'
              }}
            >
              Send GCN
            </Button>
          ) : (
            <div className="dashboard-header__wallet-actions">
              <Button 
                variant="outline" 
                onClick={onImportWallet}
                icon={<ImportIcon />}
                style={{ 
                  padding: '0.75rem 1.5rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem',
                  fontWeight: '500'
                }}
              >
                Import Wallet
              </Button>
              <Button 
                variant="primary" 
                onClick={onCreateWallet}
                icon={<PlusIcon />}
                style={{ 
                  padding: '0.75rem 1.5rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem',
                  fontWeight: '500'
                }}
              >
                Create Wallet
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Main Header Content */}
      <div className="dashboard-header__main">
        <div className="dashboard-header__stats">
          {/* Total GCN Circulation */}
          <div className="bg-purple-50 dark:bg-purple-900 border border-purple-200 dark:border-purple-800 rounded-lg px-4 py-3 text-center">
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              {formatNumber(calculateGCNCirculation())}
            </div>
            <div className="text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider mt-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Total GCN Circulation
            </div>
          </div>
          
          {/* Blockchain Height */}
          <div className="bg-indigo-50 dark:bg-indigo-900 border border-indigo-200 dark:border-indigo-800 rounded-lg px-4 py-3 text-center">
            <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              {formatNumber(blockchainInfo?.chain_length || '0')}
            </div>
            <div className="text-xs font-medium text-indigo-700 dark:text-indigo-300 uppercase tracking-wider mt-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Blockchain Height
            </div>
          </div>
          
          {/* Total Transactions */}
          <div className="bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-800 rounded-lg px-4 py-3 text-center">
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              {formatNumber(allTransactions?.length || networkStats?.total_transactions || '0')}
            </div>
            <div className="text-xs font-medium text-blue-700 dark:text-blue-300 uppercase tracking-wider mt-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Total Transactions
            </div>
          </div>
          
          {/* Pending Transactions */}
          <div className="bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-800 rounded-lg px-4 py-3 text-center">
            <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              {formatNumber(mempoolStats?.pending_count || '0')}
            </div>
            <div className="text-xs font-medium text-yellow-700 dark:text-yellow-300 uppercase tracking-wider mt-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Pending Transactions
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Simple SVG Icons
const BackArrowIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="15,18 9,12 15,6"></polyline>
  </svg>
);

const SendIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="22" y1="2" x2="11" y2="13"></line>
    <polygon points="22,2 15,22 11,13 2,9"></polygon>
  </svg>
);

const ImportIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
    <polyline points="7,10 12,15 17,10"></polyline>
    <line x1="12" y1="15" x2="12" y2="3"></line>
  </svg>
);

const PlusIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="12" y1="5" x2="12" y2="19"></line>
    <line x1="5" y1="12" x2="19" y2="12"></line>
  </svg>
);

export default DashboardHeader;