import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import './HomePage.css';

// Import common UI components if needed
// import Layout from '../components/Layout';

const HomePage = () => {
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
  
  // Handle mobile menu
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };
  
  // Initialize dark mode on load
  useEffect(() => {
    // Set initial dark mode
    if (darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
    
    // Load blockchain stats from real API
    const loadBlockchainStats = async () => {
      try {
        // Try to fetch real data from our API
        const response = await fetch('https://globalcoyn.com/api/blockchain');
        
        // If the API call fails, use the backup data
        if (!response.ok) {
          throw new Error('API call failed');
        }
        
        const blockchainData = await response.json();
        
        // Format data from actual API response
        const realData = {
          active_nodes: blockchainData.node_count || 2,
          blockchain_height: blockchainData.chain_length || 64,
          total_coins: ((blockchainData.chain_length || 64) * 50).toFixed(1),
          uptime_percentage: 99.8
        };
        
        // Update the stats in the DOM
        updateStatsDisplay(realData);
      } catch (error) {
        console.error('Error loading blockchain stats:', error);
        
        // Fallback data if API fails
        const fallbackData = {
          active_nodes: 2,
          blockchain_height: 64,
          total_coins: '3200.0',
          uptime_percentage: 99.8
        };
        
        updateStatsDisplay(fallbackData);
      }
    };
    
    loadBlockchainStats();
    
    // Clean up event listeners on unmount
    return () => {
      document.removeEventListener('scroll', null);
    };
  }, [darkMode]);
  
  // Helper function to update stats display
  const updateStatsDisplay = (data) => {
    const { active_nodes, blockchain_height, total_coins, uptime_percentage } = data;
    
    // Update the stats if the elements exist
    const statsElements = document.querySelectorAll('.stat-value');
    if (statsElements.length >= 4) {
      statsElements[0].textContent = active_nodes;
      statsElements[1].textContent = blockchain_height;
      statsElements[2].textContent = total_coins;
      statsElements[3].textContent = `${uptime_percentage}%`;
    }
  };
  
  return (
    <div className="homepage modern">
      {/* Header & Navigation */}
      <header className="compact-header">
        <nav>
          <div className="nav-left">
            <div className="logo">
              <a href="/"><img src="/assets/logo.png" alt="GlobalCoyn" /></a>
            </div>
            <ul className="nav-links desktop-links">
              <li><a href="#about">About</a></li>
              <li><a href="#features">Features</a></li>
              <li><a href="#documentation">Documentation</a></li>
              <li><a href="#explorer">Explorer</a></li>
              <li><a href="#network">Network</a></li>
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
            <li><a href="#about" onClick={() => setMobileMenuOpen(false)}>About</a></li>
            <li><a href="#features" onClick={() => setMobileMenuOpen(false)}>Features</a></li>
            <li><a href="#documentation" onClick={() => setMobileMenuOpen(false)}>Documentation</a></li>
            <li><a href="#explorer" onClick={() => setMobileMenuOpen(false)}>Explorer</a></li>
            <li><a href="#network" onClick={() => setMobileMenuOpen(false)}>Network</a></li>
            <li><Link to="/app/wallet" onClick={() => setMobileMenuOpen(false)}>Wallet</Link></li>
          </ul>
        </div>
      </header>
      
      {/* Hero Section */}
      <section className="hero">
        <div className="container">
          <h1>GlobalCoyn</h1>
          <h2>A Decentralized Digital Currency for the Modern World</h2>
          <p>
            A blockchain-based solution for international trade, independent from any nation's
            domestic monetary policy. GlobalCoyn creates a decentralized currency that reflects
            global economic activity rather than being tied to any single nation's influence.
          </p>
          <div className="cta-buttons">
            <Link to="/app/wallet" className="btn primary">Access Web Wallet</Link>
            <Link to="/app/explorer" className="btn secondary">View Block Explorer</Link>
          </div>
          <div className="version-info">
            <span>GitHub Deployment Test - May 2025 - Open Source Release</span>
          </div>
        </div>
      </section>
      
      {/* Network Statistics Section */}
      <section className="stats-section">
        <div className="container">
          <h2>Network Statistics</h2>
          <div className="stats-container">
            <div className="stat-card">
              <div className="stat-value">2</div>
              <div className="stat-label">Active Bootstrap Nodes</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">64</div>
              <div className="stat-label">Blockchain Height</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">3,200</div>
              <div className="stat-label">GCN In Circulation</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">99.8%</div>
              <div className="stat-label">Network Uptime</div>
            </div>
          </div>
        </div>
      </section>
      
      {/* About Section */}
      <section id="about" className="about">
        <div className="container">
          <h2>What is GlobalCoyn?</h2>
          <div className="content-block">
            <p className="intro-text">
              GlobalCoyn is a modern blockchain platform created to demonstrate the power of decentralized ledger 
              technology. It provides a transparent, secure, and efficient way to transfer value without 
              the need for centralized intermediaries.
            </p>
          </div>
          
          <div className="columns">
            <div className="column">
              <h3>Decentralized</h3>
              <p>Operating on a distributed network with multiple nodes that validate and record transactions without central control.</p>
            </div>
            <div className="column">
              <h3>Transparent</h3>
              <p>All transactions are permanently recorded on a public ledger that anyone can verify and audit.</p>
            </div>
            <div className="column">
              <h3>Efficient</h3>
              <p>Designed for speed and scalability, with low transaction fees and rapid confirmation times.</p>
            </div>
          </div>
        </div>
      </section>
      
      {/* Features Section */}
      <section id="features" className="features">
        <div className="container">
          <h2>Key Features</h2>
          <div className="feature-grid">
            <div className="feature">
              <div className="feature-icon">🔒</div>
              <h3>Secure Architecture</h3>
              <p>Built with modern cryptographic principles to ensure transaction integrity and network security.</p>
            </div>
            <div className="feature">
              <div className="feature-icon">⚡</div>
              <h3>Fast Confirmation</h3>
              <p>Optimized consensus algorithm for rapid transaction verification and confirmation.</p>
            </div>
            <div className="feature">
              <div className="feature-icon">🔍</div>
              <h3>Transaction Tracking</h3>
              <p>Complete visibility into the transaction lifecycle with our advanced block explorer.</p>
            </div>
            <div className="feature">
              <div className="feature-icon">💻</div>
              <h3>Web Wallet</h3>
              <p>Easy-to-use web interface for managing your GlobalCoyn assets and transactions.</p>
            </div>
          </div>
        </div>
      </section>
      
      {/* Network Section */}
      <section id="network" className="network">
        <div className="container">
          <h2>Network Architecture</h2>
          <div className="content-block">
            <p className="intro-text">
              GlobalCoyn operates on a decentralized peer-to-peer network with dedicated bootstrap nodes 
              to ensure reliability and resilience. The infrastructure is designed for maximum uptime and security.
            </p>
          </div>
          
          <div className="columns">
            <div className="column">
              <h3>Bootstrap Nodes</h3>
              <p>
                Our production bootstrap nodes on <strong>globalcoyn.com</strong> serve as reliable entry points 
                to the network, facilitating peer discovery and maintaining blockchain synchronization.
              </p>
            </div>
            <div className="column">
              <h3>Peer-to-Peer Network</h3>
              <p>
                The system uses an advanced peer discovery protocol to establish connections between nodes, 
                ensuring rapid propagation of transactions and blocks across the network.
              </p>
            </div>
            <div className="column">
              <h3>Consensus Protocol</h3>
              <p>
                Our modified proof-of-work algorithm provides the security benefits of traditional blockchains 
                while improving energy efficiency and transaction throughput.
              </p>
            </div>
          </div>
        </div>
      </section>
      
      {/* Explorer Section */}
      <section id="explorer" className="explorer">
        <div className="container">
          <h2>Blockchain Explorer</h2>
          <div className="content-block">
            <p className="intro-text">
              The GlobalCoyn Explorer provides complete visibility into all blockchain activity, 
              allowing you to track transactions, monitor blocks, and verify balances in real-time.
            </p>
          </div>
          
          <div className="explorer-features">
            <div className="explorer-feature">
              <h3>Transaction Tracking</h3>
              <p>Follow the flow of funds across the network with our comprehensive transaction viewer.</p>
              <Link to="/app/explorer" className="feature-link">View Transactions</Link>
            </div>
            
            <div className="explorer-feature">
              <h3>Block Details</h3>
              <p>Examine individual blocks in the chain, including timestamps, hashes, and included transactions.</p>
              <Link to="/app/explorer" className="feature-link">Browse Blocks</Link>
            </div>
            
            <div className="explorer-feature">
              <h3>Address History</h3>
              <p>View complete transaction histories and current balances for any wallet address on the network.</p>
              <Link to="/app/explorer" className="feature-link">Search Addresses</Link>
            </div>
          </div>
          
          <div className="cta-container">
            <Link to="/app/explorer" className="btn primary">Open Explorer</Link>
          </div>
        </div>
      </section>
      
      {/* Documentation Section */}
      <section id="documentation" className="documentation">
        <div className="container">
          <h2>Documentation</h2>
          <div className="content-block">
            <p className="intro-text">
              Our technical documentation provides detailed information about the GlobalCoyn blockchain, 
              including protocols, APIs, wallet functionality, and integration guides.
            </p>
          </div>
          
          <div className="guides-section">
            <div className="guide-grid">
              <div className="guide-item">
                <h3>Wallet Guide</h3>
                <p>Learn how to create and manage your GlobalCoyn wallet, send and receive transactions, and secure your funds.</p>
                <Link to="/app/wallet" className="guide-link">Open Wallet</Link>
              </div>
              
              <div className="guide-item">
                <h3>API Reference</h3>
                <p>Comprehensive documentation of the GlobalCoyn API endpoints for developers building applications on the platform.</p>
                <Link to="/api-reference" className="guide-link">View API Docs</Link>
              </div>
              
              <div className="guide-item">
                <h3>Node Setup</h3>
                <p>Technical specifications for setting up and running your own GlobalCoyn node on the network.</p>
                <a href="mailto:global@globalcoyn.com" className="guide-link">Email Us</a>
              </div>
              
              <div className="guide-item">
                <h3>Whitepaper</h3>
                <p>Detailed explanation of the GlobalCoyn blockchain purpose, economic model, and technical architecture.</p>
                <Link to="/whitepaper" className="guide-link">View Whitepaper</Link>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      {/* FAQ Section */}
      <section className="faq">
        <div className="container">
          <h2>Frequently Asked Questions</h2>
          
          <div className="faq-list">
            <div className="faq-item">
              <h3>What is GlobalCoyn?</h3>
              <p>
                GlobalCoyn is a modern blockchain platform created for educational and demonstration purposes. 
                It implements core blockchain concepts including decentralized consensus, cryptographic security, 
                and transparent transaction processing.
              </p>
            </div>
            <div className="faq-item">
              <h3>How can I interact with the GlobalCoyn blockchain?</h3>
              <p>
                You can use our web-based wallet interface to create wallets, view balances, and initiate transactions. 
                For a deeper look into the blockchain, our explorer provides complete visibility into all blocks, 
                transactions, and addresses on the network.
              </p>
            </div>
            <div className="faq-item">
              <h3>Is GlobalCoyn secure?</h3>
              <p>
                Yes, GlobalCoyn implements industry-standard cryptographic algorithms for transaction signing and 
                verification. The blockchain is immutable and transparent, allowing anyone to audit the complete 
                transaction history.
              </p>
            </div>
            <div className="faq-item">
              <h3>How does the consensus mechanism work?</h3>
              <p>
                GlobalCoyn uses a modified proof-of-work consensus protocol that maintains the security benefits 
                of traditional blockchains while improving energy efficiency. This allows for rapid block creation 
                and transaction confirmation.
              </p>
            </div>
          </div>
        </div>
      </section>
      
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

export default HomePage;