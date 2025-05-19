import React, { useState, useEffect } from 'react';

/**
 * Environment Toggle Component
 * This component allows developers to switch between environments for testing
 * It only appears in development mode and can be toggled with a key combination
 */
const EnvironmentToggle = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [currentEnvironment, setCurrentEnvironment] = useState('auto');

  useEffect(() => {
    // Get current environment from localStorage if exists
    const storedEnv = localStorage.getItem('gcn_environment');
    if (storedEnv) {
      setCurrentEnvironment(storedEnv);
    }

    // Listen for keyboard shortcut to toggle visibility (Ctrl+Shift+E)
    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'E') {
        setIsVisible(prev => !prev);
        e.preventDefault();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  // Update environment in localStorage
  const setEnvironment = (env) => {
    if (env === 'auto') {
      localStorage.removeItem('gcn_environment');
      setCurrentEnvironment('auto');
    } else {
      localStorage.setItem('gcn_environment', env);
      setCurrentEnvironment(env);
    }
    
    // Reload to apply changes
    window.location.reload();
  };

  // Only render in development mode and if visible
  if (!isVisible || process.env.NODE_ENV === 'production') {
    return null;
  }

  // Current API endpoint based on environment
  const currentEndpoint = 
    currentEnvironment === 'production' ? 'https://globalcoyn.com/api' : 
    currentEnvironment === 'development' ? 'http://localhost:8001/api' :
    'Auto-detected based on hostname';

  return (
    <div className="fixed bottom-4 left-4 p-4 bg-gray-800 text-white rounded-lg shadow-lg z-50 text-sm">
      <div className="flex flex-col space-y-2">
        <div className="flex justify-between items-center">
          <h3 className="font-bold">Environment Toggle</h3>
          <button 
            className="text-gray-400 hover:text-white"
            onClick={() => setIsVisible(false)}
          >
            ✖
          </button>
        </div>
        
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <input 
              type="radio" 
              id="env-auto" 
              name="environment"
              checked={currentEnvironment === 'auto'}
              onChange={() => setEnvironment('auto')}
            />
            <label htmlFor="env-auto">Auto-detect</label>
          </div>
          
          <div className="flex items-center space-x-2">
            <input 
              type="radio" 
              id="env-dev" 
              name="environment"
              checked={currentEnvironment === 'development'} 
              onChange={() => setEnvironment('development')}
            />
            <label htmlFor="env-dev">Development (localhost)</label>
          </div>
          
          <div className="flex items-center space-x-2">
            <input 
              type="radio" 
              id="env-prod" 
              name="environment"
              checked={currentEnvironment === 'production'} 
              onChange={() => setEnvironment('production')}
            />
            <label htmlFor="env-prod">Production (globalcoyn.com)</label>
          </div>
        </div>
        
        <div className="text-xs text-gray-400 mt-2">
          <div>Current API: {currentEndpoint}</div>
          <div>Press Ctrl+Shift+E to toggle this panel</div>
        </div>
      </div>
    </div>
  );
};

export default EnvironmentToggle;