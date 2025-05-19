import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import './ApiReference.css';

const ApiReference = () => {
  const [darkMode, setDarkMode] = useState(localStorage.getItem('darkMode') === 'true');
  
  // Toggle dark mode
  const toggleDarkMode = () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    localStorage.setItem('darkMode', newDarkMode);
    
    if (newDarkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  };
  
  // Initialize dark mode on load
  useEffect(() => {
    // Set initial dark mode
    if (darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
    
    document.title = "GlobalCoyn API Reference";
    
    // Add class to body for page-specific styling
    document.body.classList.add('api-page');
    return () => {
      document.body.classList.remove('api-page');
    };
  }, [darkMode]);
  
  // Handle mobile menu
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  return (
    <div className="api-container">
      {/* Header */}
      <header className="compact-header">
        <nav>
          <div className="nav-left">
            <div className="logo">
              <Link to="/"><img src="/assets/logo.png" alt="GlobalCoyn" /></Link>
            </div>
            <ul className="nav-links desktop-links">
              <li><Link to="/">Home</Link></li>
              <li><Link to="/#about">About</Link></li>
              <li><Link to="/#features">Features</Link></li>
              <li><Link to="/#documentation">Documentation</Link></li>
              <li><Link to="/#explorer">Explorer</Link></li>
            </ul>
          </div>
          <div className="nav-controls">
            <button 
              className="theme-toggle" 
              aria-label="Toggle dark mode"
              onClick={toggleDarkMode}
            >
              {darkMode ? '☀️' : '🌙'}
            </button>
            <Link to="/app/wallet" className="wallet-button">Wallet</Link>
            <div className="mobile-menu-toggle" onClick={toggleMobileMenu}>
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </nav>
        
        {/* Mobile Menu */}
        <div className={`mobile-menu ${mobileMenuOpen ? 'open' : ''}`}>
          <ul className="mobile-nav-links">
            <li><Link to="/" onClick={() => setMobileMenuOpen(false)}>Home</Link></li>
            <li><Link to="/#about" onClick={() => setMobileMenuOpen(false)}>About</Link></li>
            <li><Link to="/#features" onClick={() => setMobileMenuOpen(false)}>Features</Link></li>
            <li><Link to="/#documentation" onClick={() => setMobileMenuOpen(false)}>Documentation</Link></li>
            <li><Link to="/#explorer" onClick={() => setMobileMenuOpen(false)}>Explorer</Link></li>
            <li><Link to="/app/wallet" onClick={() => setMobileMenuOpen(false)}>Wallet</Link></li>
          </ul>
        </div>
      </header>
      
      {/* API Content */}
      <div className="api-content">
        <div className="api-header">
          <h1>GlobalCoyn API Reference</h1>
          <p className="api-description">
            Complete documentation for interacting with the GlobalCoyn blockchain through our REST API.
          </p>
        </div>
        
        <div className="api-sections">
          <div className="api-section">
            <h2>Getting Started</h2>
            <p>
              The GlobalCoyn API provides programmatic access to the GlobalCoyn blockchain network. 
              You can use it to query blockchain data, create and submit transactions, 
              and interact with the network.
            </p>
            <div className="api-card">
              <h3>Base URL</h3>
              <code className="api-url">https://globalcoyn.com/api</code>
              <p>All API requests should be made to this base URL.</p>
            </div>
            <div className="api-card">
              <h3>Authentication</h3>
              <p>
                Most endpoints require API key authentication. Include your API key in the request header:
              </p>
              <pre className="code-block">
{`Authorization: Bearer YOUR_API_KEY`}
              </pre>
              <p>You can obtain an API key from the <Link to="/app/dashboard">developer dashboard</Link>.</p>
            </div>
          </div>
          
          <div className="api-section">
            <h2>Blockchain Endpoints</h2>
            
            <div className="api-endpoint">
              <div className="endpoint-header">
                <span className="http-method">GET</span>
                <code>/blockchain</code>
              </div>
              <p>Returns current blockchain information including height, latest block hash, and network difficulty.</p>
              <div className="endpoint-details">
                <div className="endpoint-params">
                  <h4>Parameters</h4>
                  <p>None</p>
                </div>
                <div className="endpoint-response">
                  <h4>Response</h4>
                  <pre className="code-block">
{`{
  "chain_length": 64,
  "node_count": 2,
  "latest_block_hash": "000000a7e5f6b6b32c9a4d9dc3582b62e36dede31cc9c6467a9b6a84fa753b0a",
  "difficulty": 3,
  "network_hashrate": "1.2 MH/s"
}`}
                  </pre>
                </div>
              </div>
            </div>
            
            <div className="api-endpoint">
              <div className="endpoint-header">
                <span className="http-method">GET</span>
                <code>/blockchain/block/{`{hash}`}</code>
              </div>
              <p>Returns detailed information about a specific block by hash.</p>
              <div className="endpoint-details">
                <div className="endpoint-params">
                  <h4>Parameters</h4>
                  <table className="params-table">
                    <thead>
                      <tr>
                        <th>Parameter</th>
                        <th>Type</th>
                        <th>Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>hash</td>
                        <td>String</td>
                        <td>The hash of the block to retrieve</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div className="endpoint-response">
                  <h4>Response</h4>
                  <pre className="code-block">
{`{
  "hash": "000000a7e5f6b6b32c9a4d9dc3582b62e36dede31cc9c6467a9b6a84fa753b0a",
  "height": 64,
  "timestamp": 1683562472,
  "previous_block": "00000031a5f9b6a342be931ca7483598214c542a31a5dfcd8a1c31be21336a67",
  "merkle_root": "fc4a5e9a50b4c902ac53b9c79b492b5282f9636b86ed21d848728d40ba48f4d7",
  "difficulty": 3,
  "nonce": 12897,
  "transaction_count": 2,
  "transactions": [
    "3a5e9a5b4c30ac53b49c79b492b5282f9636b86ed21d848728d40ba48f4d7fd1",
    "5f8c7d1e32bf9a46c705b14f8e2d9be37429a0b3a5d1f6429a8f6b1d5e71c202"
  ]
}`}
                  </pre>
                </div>
              </div>
            </div>
          </div>
          
          <div className="api-section">
            <h2>Wallet Endpoints</h2>
            
            <div className="api-endpoint">
              <div className="endpoint-header">
                <span className="http-method">GET</span>
                <code>/wallet/balance/{`{address}`}</code>
              </div>
              <p>Returns the current balance of a wallet address.</p>
              <div className="endpoint-details">
                <div className="endpoint-params">
                  <h4>Parameters</h4>
                  <table className="params-table">
                    <thead>
                      <tr>
                        <th>Parameter</th>
                        <th>Type</th>
                        <th>Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>address</td>
                        <td>String</td>
                        <td>The wallet address to query</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div className="endpoint-response">
                  <h4>Response</h4>
                  <pre className="code-block">
{`{
  "address": "GCN1qyqqxzvV5r6BnUZVJfp4nA2gULy8n2UXZC",
  "balance": 156.25,
  "pending_balance": 0.0,
  "last_updated": 1683562982
}`}
                  </pre>
                </div>
              </div>
            </div>
            
            <div className="api-endpoint">
              <div className="endpoint-header">
                <span className="http-method">POST</span>
                <code>/wallet/send</code>
              </div>
              <p>Creates and broadcasts a new transaction to the network.</p>
              <div className="endpoint-details">
                <div className="endpoint-params">
                  <h4>Parameters</h4>
                  <pre className="code-block">
{`{
  "fromAddress": "GCN1qyqqxzvV5r6BnUZVJfp4nA2gULy8n2UXZC",
  "toAddress": "GCN1w4chZpfZvAqj1TD5G8vjf7Rz34rY4QpkE3",
  "amount": 5.0,
  "fee": 0.001,
  "signature": "c5db6b0e7c7517c6ce0eebfab01c44d8c6f5e7b3de15b7839cc4214e0c340a2d1"
}`}
                  </pre>
                </div>
                <div className="endpoint-response">
                  <h4>Response</h4>
                  <pre className="code-block">
{`{
  "transaction_id": "5f8c7d1e32bf9a46c705b14f8e2d9be37429a0b3a5d1f6429a8f6b1d5e71c202",
  "status": "broadcast",
  "timestamp": 1683562992
}`}
                  </pre>
                </div>
              </div>
            </div>
          </div>
          
          <div className="api-section">
            <h2>Mining Endpoints</h2>
            
            <div className="api-endpoint">
              <div className="endpoint-header">
                <span className="http-method">GET</span>
                <code>/mining/status</code>
              </div>
              <p>Returns the current mining status.</p>
              <div className="endpoint-details">
                <div className="endpoint-params">
                  <h4>Parameters</h4>
                  <p>None</p>
                </div>
                <div className="endpoint-response">
                  <h4>Response</h4>
                  <pre className="code-block">
{`{
  "is_mining": true,
  "hashrate": "1.2 MH/s",
  "threads": 4,
  "cpu_usage": 75,
  "wallet_address": "GCN1qyqqxzvV5r6BnUZVJfp4nA2gULy8n2UXZC",
  "blocks_mined": 3,
  "total_rewards": 150.0
}`}
                  </pre>
                </div>
              </div>
            </div>
            
            <div className="api-endpoint">
              <div className="endpoint-header">
                <span className="http-method">POST</span>
                <code>/mining/start</code>
              </div>
              <p>Starts mining with the specified wallet address and settings.</p>
              <div className="endpoint-details">
                <div className="endpoint-params">
                  <h4>Parameters</h4>
                  <pre className="code-block">
{`{
  "walletAddress": "GCN1qyqqxzvV5r6BnUZVJfp4nA2gULy8n2UXZC",
  "threads": 4,
  "cpuUsage": 75
}`}
                  </pre>
                </div>
                <div className="endpoint-response">
                  <h4>Response</h4>
                  <pre className="code-block">
{`{
  "success": true,
  "message": "Mining started",
  "status": {
    "is_mining": true,
    "hashrate": "0.8 MH/s",
    "threads": 4,
    "cpu_usage": 75,
    "wallet_address": "GCN1qyqqxzvV5r6BnUZVJfp4nA2gULy8n2UXZC"
  }
}`}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Footer */}
      <footer className="slim-footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-logo">
              <img src="/assets/logo.png" alt="GlobalCoyn" />
            </div>
            <div className="footer-links">
              <Link to="/app/explorer">Platform</Link>
              <Link to="/whitepaper">Whitepaper</Link>
              <a href="mailto:global@globalcoyn.com">Contact</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default ApiReference;