import React, { useState } from 'react';

const Settings = () => {
  const [settings, setSettings] = useState({
    walletLock: true,
    theme: 'system',
    currency: 'GCN',
  });

  // Handle settings change
  const handleSettingChange = (setting, value) => {
    setSettings({
      ...settings,
      [setting]: value
    });
  };

  return (
    <div className="space-y-0">
      <div className="flex flex-col space-y-0 mb-4 px-6">
        <div className="flex items-center justify-between">
          <div className="w-full">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Settings</h1>
            <div className="text-sm text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Configure your wallet, application, and node settings
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <button className="btn-primary flex items-center text-xs py-1 px-3 whitespace-nowrap" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Save Settings
            </button>
            <button className="btn-secondary flex items-center text-xs py-1 px-3 whitespace-nowrap" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Reset to Defaults
            </button>
          </div>
        </div>
      </div>
      
      {/* Wallet Settings */}
      <div className="px-6 py-2 border-t border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Wallet Settings</h2>
      </div>
      
      <div className="px-6 py-2 border-b border-gray-200 dark:border-gray-700">
        {/* Auto-lock wallet */}
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-0" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Auto-lock Wallet</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Automatically lock your wallet after 15 minutes of inactivity
            </p>
          </div>
          <div className="flex items-center h-6">
            <button 
              type="button"
              className={`${settings.walletLock ? 'bg-green-600' : 'bg-gray-300'} relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full transition-colors duration-200 ease-in-out`}
              onClick={() => handleSettingChange('walletLock', !settings.walletLock)}
            >
              <span 
                className={`${settings.walletLock ? 'translate-x-5' : 'translate-x-1'} inline-block h-4 w-4 transform rounded-full bg-white transition duration-200 ease-in-out mt-1`} 
              />
            </button>
          </div>
        </div>
        
        {/* Backup Wallet */}
        <div className="mb-3">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Backup Options</h3>
          <div className="space-x-3">
            <button className="btn-primary text-xs py-1 px-3" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Backup Wallet</button>
            <button className="btn-secondary text-xs py-1 px-3" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Show Recovery Phrase</button>
          </div>
        </div>
        
        {/* Delete Wallet */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-red-600 mb-0" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Danger Zone</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
              Permanently delete your wallet from this device. Make sure you have a backup.
            </p>
          </div>
          <button className="bg-red-600 text-white font-medium text-xs py-1 px-3 rounded-md hover:bg-red-700 transition-colors" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>
            Delete Wallet
          </button>
        </div>
      </div>
      
      {/* Application Settings */}
      <div className="px-6 py-2">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white text-left" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Application Settings</h2>
      </div>
      
      <div className="px-6 py-2 border-b border-gray-200 dark:border-gray-700">
        {/* Theme Selection */}
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-0" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Theme</h3>
        <select
          id="theme"
          name="theme"
          className="block w-full pl-3 pr-10 py-1 text-base border-gray-300 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white mb-3"
          value={settings.theme}
          onChange={(e) => handleSettingChange('theme', e.target.value)}
          style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
        >
          <option value="system" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>System Default</option>
          <option value="light" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Light</option>
          <option value="dark" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Dark</option>
        </select>
        
        {/* Currency Display */}
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-0" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>Currency Display</h3>
        <select
          id="currency"
          name="currency"
          className="block w-full pl-3 pr-10 py-1 text-base border-gray-300 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          value={settings.currency}
          onChange={(e) => handleSettingChange('currency', e.target.value)}
          style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}
        >
          <option value="GCN" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>GCN Only</option>
          <option value="USD" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>GCN & USD</option>
          <option value="EUR" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>GCN & EUR</option>
          <option value="GBP" style={{ fontFamily: 'Helvetica, Arial, sans-serif' }}>GCN & GBP</option>
        </select>
      </div>
      
    </div>
  );
};

export default Settings;