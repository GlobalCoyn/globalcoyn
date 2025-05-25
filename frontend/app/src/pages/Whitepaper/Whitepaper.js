import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import './WhitepaperPage.css';

const Whitepaper = () => {
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
    
    document.title = "GlobalCoyn Whitepaper";
    
    // Add class to body for page-specific styling
    document.body.classList.add('whitepaper-page');
    return () => {
      document.body.classList.remove('whitepaper-page');
    };
  }, [darkMode]);
  
  // Handle mobile menu
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  return (
    <div className="whitepaper-container">
      {/* Logo and Back button at top left */}
      <div className="whitepaper-header">
        <Link to="/" className="back-to-home">
          <img src="/assets/logo.png" alt="GlobalCoyn" className="whitepaper-logo" />
          <span className="back-arrow">←</span> Back to Home
        </Link>
      </div>
      
      {/* Whitepaper Content */}
      <div className="whitepaper-content">
        <article className="whitepaper">
          <h1>GlobalCoyn: A Neutral Global Trade Currency</h1>
          
          {/* Document Controls moved below title */}
          <div className="whitepaper-actions document-buttons">
            <button className="print-button" onClick={() => window.print()}>
              <span className="icon">🖨️</span>Print
            </button>
            <a href="/whitepaper.pdf" download className="download-button">
              <span className="icon">📥</span><span className="button-text">Download PDF</span>
            </a>
          </div>
          
          <section className="whitepaper-section abstract">
            <h2>Abstract</h2>
            <p>
              GlobalCoyn (GCN) introduces a blockchain-based solution for a neutral global trade currency, independent 
              from any nation's domestic monetary policy. Unlike previous attempts at international monetary standards, 
              GlobalCoyn leverages blockchain technology to create a decentralized currency that reflects global economic 
              activity rather than being tied to any single nation's economic influence. This whitepaper outlines the 
              technical architecture, economic principles, and practical applications of GlobalCoyn as a medium for 
              international trade.
            </p>
          </section>
          
          <section className="whitepaper-section toc">
            <h2>Table of Contents</h2>
            <ul>
              <li><a href="#introduction">1. Introduction: The Need for a Neutral Global Trade Currency</a></li>
              <li><a href="#economic">2. Economic Foundations</a></li>
              <li><a href="#architecture">3. Technical Architecture</a></li>
              <li><a href="#consensus">4. Consensus Mechanism</a></li>
              <li><a href="#network">5. Network Architecture</a></li>
              <li><a href="#wallets">6. Wallet Implementation</a></li>
              <li><a href="#use-cases">7. Use Cases</a></li>
              <li><a href="#governance">8. Governance Structure</a></li>
              <li><a href="#comparison">9. Comparison with Alternative Approaches</a></li>
              <li><a href="#challenges">10. Challenges and Mitigations</a></li>
              <li><a href="#conclusion">11. Conclusion</a></li>
            </ul>
          </section>
          
          <section id="introduction" className="whitepaper-section">
            <h2>1. Introduction: The Need for a Neutral Global Trade Currency</h2>
            <p>
              The international monetary system has historically been dominated by national currencies serving as global 
              reserve currencies—first the British pound, then the US dollar. While convenient, this arrangement creates 
              inherent imbalances:
            </p>
            <ul>
              <li><strong>Exorbitant Privilege:</strong> The issuing nation gains significant economic and geopolitical advantages</li>
              <li><strong>Policy Conflicts:</strong> Domestic monetary policy of the reserve currency nation impacts global trade</li>
              <li><strong>Asymmetric Adjustments:</strong> Non-reserve currency nations bear disproportionate adjustment costs</li>
              <li><strong>Triffin Dilemma:</strong> Reserve currency nations face conflicting short-term domestic and long-term international objectives</li>
            </ul>
            <p>
              Previous attempts to address these issues, such as the gold standard, created different problems. When countries 
              pegged their currencies to gold, they surrendered control over domestic monetary policy, making it difficult to 
              respond to local economic conditions.
            </p>
            <p>
              GlobalCoyn presents a novel solution: a blockchain-based currency specifically designed for international trade 
              that remains independent of any single nation's monetary policy. Unlike gold, countries would not peg their 
              domestic currencies to GlobalCoyn, thus retaining monetary sovereignty while benefiting from a neutral 
              international trade medium.
            </p>
          </section>
          
          <section id="economic" className="whitepaper-section">
            <h2>2. Economic Foundations</h2>
            
            <h3>2.1 Value Stabilization Mechanism</h3>
            <p>
              GlobalCoyn's value derives from its utility in international trade rather than being backed by a single 
              government or commodity. Its value stability mechanisms include:
            </p>
            <ul>
              <li><strong>Supply Algorithm:</strong> The issuance rate follows a predictable halving schedule, similar to Bitcoin but with modifications for trade volume stability</li>
              <li><strong>Network Difficulty:</strong> Mining difficulty adjusts dynamically to maintain predictable block times, with a target block time of 10 minutes</li>
              <li><strong>Transaction Fees:</strong> Market-driven fees create an equilibrium between network usage and transaction costs</li>
            </ul>
            
            <div className="whitepaper-diagram">
              <div className="diagram-container">
                <img src="/assets/supply_curve.svg" alt="GlobalCoyn Supply Emission Curve" className="diagram" style={{maxWidth: '100%', height: 'auto', display: 'block', margin: '0 auto'}} />
              </div>
            </div>
            
            <h3>2.2 Relationship to National Currencies</h3>
            <p>
              GlobalCoyn is designed to coexist with, rather than replace, national currencies:
            </p>
            <ul>
              <li>Countries maintain their domestic currencies for local economies</li>
              <li>GlobalCoyn serves as a neutral medium for international trade</li>
              <li>Domestic inflation/deflation reflects only in the exchange rate between the local currency and GlobalCoyn</li>
            </ul>
            <p>
              For example, if the United States doubled its money supply, the US dollar would likely be worth half as many 
              GlobalCoyn, but this would not directly impact other nations' currencies in relation to GlobalCoyn.
            </p>
          </section>
          
          <section id="architecture" className="whitepaper-section">
            <h2>3. Technical Architecture</h2>
            
            <h3>3.1 Blockchain Core</h3>
            <p>
              The GlobalCoyn blockchain is built with a modular architecture centered around these key components:
            </p>
            
            <div className="component-description">
              <h4>Block Structure</h4>
              <p>
                Each block in the GlobalCoyn blockchain contains:
              </p>
              <ul>
                <li><strong>Block Header:</strong> Contains index, previous block hash, timestamp, merkle root, nonce, and difficulty</li>
                <li><strong>Transactions:</strong> List of validated transactions included in the block</li>
                <li><strong>Merkle Root:</strong> A cryptographic proof of all transactions in the block</li>
              </ul>
              <pre className="code-block">
<span className="code-class">class</span> <span className="code-class">Block</span>:
    <span className="code-string">"""</span>
    <span className="code-comment">Represents a block in the blockchain.</span>
    <span className="code-comment">Includes block header and list of transactions.</span>
    <span className="code-string">"""</span>
    <span className="code-keyword">def</span> <span className="code-function">__init__</span>(<span className="code-variable">self</span>, <span className="code-variable">index</span>, <span className="code-variable">previous_hash</span>, <span className="code-variable">timestamp</span>, 
                 <span className="code-variable">transactions</span>, <span className="code-variable">nonce</span>, <span className="code-variable">difficulty_bits</span>):
        <span className="code-variable">self</span>.<span className="code-variable">index</span> <span className="code-operator">=</span> <span className="code-variable">index</span>
        <span className="code-variable">self</span>.<span className="code-variable">previous_hash</span> <span className="code-operator">=</span> <span className="code-variable">previous_hash</span>
        <span className="code-variable">self</span>.<span className="code-variable">timestamp</span> <span className="code-operator">=</span> <span className="code-variable">timestamp</span>
        <span className="code-variable">self</span>.<span className="code-variable">transactions</span> <span className="code-operator">=</span> <span className="code-variable">transactions</span>
        <span className="code-variable">self</span>.<span className="code-variable">nonce</span> <span className="code-operator">=</span> <span className="code-variable">nonce</span>
        <span className="code-variable">self</span>.<span className="code-variable">difficulty_bits</span> <span className="code-operator">=</span> <span className="code-variable">difficulty_bits</span>
        <span className="code-variable">self</span>.<span className="code-variable">merkle_root</span> <span className="code-operator">=</span> <span className="code-variable">self</span>.<span className="code-function">calculate_merkle_root</span>()
        <span className="code-variable">self</span>.<span className="code-variable">hash</span> <span className="code-operator">=</span> <span className="code-variable">self</span>.<span className="code-function">calculate_hash</span>()
              </pre>
            </div>
            
            <div className="component-description">
              <h4>Transaction Model</h4>
              <p>
                GlobalCoyn implements a UTXO-inspired transaction model with these attributes:
              </p>
              <ul>
                <li><strong>Sender:</strong> The wallet address initiating the transaction</li>
                <li><strong>Recipient:</strong> The destination wallet address</li>
                <li><strong>Amount:</strong> The quantity of GCN to transfer</li>
                <li><strong>Fee:</strong> Transaction fee for miners</li>
                <li><strong>Signature:</strong> Cryptographic proof of authorization</li>
                <li><strong>Timestamp:</strong> Transaction creation time</li>
              </ul>
              <pre className="code-block">
<span className="code-class">class</span> <span className="code-class">Transaction</span>:
    <span className="code-string">"""</span>
    <span className="code-comment">Represents a blockchain transaction for transferring funds between addresses.</span>
    <span className="code-string">"""</span>
    <span className="code-keyword">def</span> <span className="code-function">__init__</span>(<span className="code-variable">self</span>, <span className="code-variable">sender</span>, <span className="code-variable">recipient</span>, <span className="code-variable">amount</span>, <span className="code-variable">fee</span>, <span className="code-variable">signature</span><span className="code-operator">=</span><span className="code-builtin">None</span>):
        <span className="code-variable">self</span>.<span className="code-variable">sender</span> <span className="code-operator">=</span> <span className="code-variable">sender</span>
        <span className="code-variable">self</span>.<span className="code-variable">recipient</span> <span className="code-operator">=</span> <span className="code-variable">recipient</span>
        <span className="code-variable">self</span>.<span className="code-variable">amount</span> <span className="code-operator">=</span> <span className="code-function">float</span>(<span className="code-variable">amount</span>)
        <span className="code-variable">self</span>.<span className="code-variable">fee</span> <span className="code-operator">=</span> <span className="code-function">float</span>(<span className="code-variable">fee</span>)
        <span className="code-variable">self</span>.<span className="code-variable">signature</span> <span className="code-operator">=</span> <span className="code-variable">signature</span>
        <span className="code-variable">self</span>.<span className="code-variable">timestamp</span> <span className="code-operator">=</span> <span className="code-variable">time</span>.<span className="code-function">time</span>()
        <span className="code-variable">self</span>.<span className="code-variable">tx_hash</span> <span className="code-operator">=</span> <span className="code-builtin">None</span>
        <span className="code-variable">self</span>.<span className="code-function">calculate_hash</span>()
              </pre>
            </div>
            
            <div className="whitepaper-diagram">
              <div className="diagram-container">
                <img src="/assets/blockchain_architecture.svg" alt="GlobalCoyn Blockchain Architecture" className="diagram" style={{maxWidth: '100%', height: 'auto', display: 'block', margin: '0 auto'}} />
              </div>
            </div>
            
            <h3>3.2 Mempool Management</h3>
            <p>
              The GlobalCoyn mempool is a crucial component that:
            </p>
            <ul>
              <li>Validates incoming transactions before accepting them</li>
              <li>Prevents double-spending attempts</li>
              <li>Maintains transaction ordering by fee priority</li>
              <li>Manages pending transaction lifecycle</li>
            </ul>
            <p>
              When a new block is mined, transactions are selected from the mempool based primarily on the fee they offer, 
              incentivizing users to include appropriate fees for faster confirmation times.
            </p>
          </section>
          
          <section id="consensus" className="whitepaper-section">
            <h2>4. Consensus Mechanism</h2>
            
            <h3>4.1 Proof-of-Work Design</h3>
            <p>
              GlobalCoyn utilizes a modified proof-of-work consensus mechanism that balances security, decentralization, and 
              energy efficiency:
            </p>
            <ul>
              <li><strong>Hash Algorithm:</strong> Double SHA-256 for block header hashing</li>
              <li><strong>Target Block Time:</strong> 10 minutes average between blocks</li>
              <li><strong>Difficulty Adjustment:</strong> Every 2,016 blocks (approximately 2 weeks)</li>
              <li><strong>Development Mode:</strong> More frequent adjustments during initial network growth</li>
            </ul>
            
            <pre className="code-block">
<span className="code-keyword">def</span> <span className="code-function">mine_block</span>(<span className="code-variable">self</span>, <span className="code-variable">chain</span>, <span className="code-variable">mempool</span>, <span className="code-variable">miner_address</span>, <span className="code-variable">max_tx</span><span className="code-operator">=</span><span className="code-number">100</span>):
    <span className="code-string">"""</span>
    <span className="code-comment">Mine a new block with proof-of-work.</span>
    <span className="code-comment"></span>
    <span className="code-comment">Args:</span>
    <span className="code-comment">    chain: Current blockchain</span>
    <span className="code-comment">    mempool: Transaction mempool</span>
    <span className="code-comment">    miner_address: Address to receive mining reward</span>
    <span className="code-comment">    max_tx: Maximum transactions to include</span>
    <span className="code-comment">    </span>
    <span className="code-comment">Returns:</span>
    <span className="code-comment">    Newly mined block if successful, None otherwise</span>
    <span className="code-string">"""</span>
    <span className="code-comment"># Add mining reward transaction</span>
    <span className="code-variable">reward</span> <span className="code-operator">=</span> <span className="code-variable">self</span>.<span className="code-function">calculate_reward</span>(<span className="code-function">len</span>(<span className="code-variable">chain</span>))
    <span className="code-variable">reward_tx</span> <span className="code-operator">=</span> <span className="code-class">Transaction</span>(<span className="code-string">"0"</span>, <span className="code-variable">miner_address</span>, <span className="code-variable">reward</span>, <span className="code-number">0</span>)
    <span className="code-variable">block_transactions</span> <span className="code-operator">=</span> [<span className="code-variable">reward_tx</span>]
    
    <span className="code-comment"># Add transactions from mempool (sorted by fee)</span>
    <span className="code-variable">mempool_txs</span> <span className="code-operator">=</span> <span className="code-variable">mempool</span>.<span className="code-function">get_transactions</span>(<span className="code-variable">max_tx</span>)
    <span className="code-variable">block_transactions</span>.<span className="code-function">extend</span>(<span className="code-variable">mempool_txs</span>)
    
    <span className="code-comment"># Create new block</span>
    <span className="code-variable">new_block</span> <span className="code-operator">=</span> <span className="code-class">Block</span>(
        <span className="code-variable">index</span><span className="code-operator">=</span><span className="code-function">len</span>(<span className="code-variable">chain</span>),
        <span className="code-variable">previous_hash</span><span className="code-operator">=</span><span className="code-variable">chain</span>[<span className="code-number">-1</span>].<span className="code-function">get</span>(<span className="code-string">"hash"</span>) <span className="code-keyword">if</span> <span className="code-variable">chain</span> <span className="code-keyword">else</span> <span className="code-string">"0"</span> <span className="code-operator">*</span> <span className="code-number">64</span>,
        <span className="code-variable">timestamp</span><span className="code-operator">=</span><span className="code-variable">time</span>.<span className="code-function">time</span>(),
        <span className="code-variable">transactions</span><span className="code-operator">=</span><span className="code-variable">block_transactions</span>,
        <span className="code-variable">nonce</span><span className="code-operator">=</span><span className="code-number">0</span>,
        <span className="code-variable">difficulty_bits</span><span className="code-operator">=</span><span className="code-variable">self</span>.<span className="code-variable">bits</span>
    )
    
    <span className="code-comment"># Proof of work - increment nonce until hash meets difficulty</span>
    <span className="code-keyword">while</span> <span className="code-builtin">True</span>:
        <span className="code-variable">new_block</span>.<span className="code-variable">nonce</span> <span className="code-operator">+=</span> <span className="code-number">1</span>
        <span className="code-variable">new_block</span>.<span className="code-variable">hash</span> <span className="code-operator">=</span> <span className="code-variable">new_block</span>.<span className="code-function">calculate_hash</span>()
        
        <span className="code-comment"># Check if hash meets difficulty requirement</span>
        <span className="code-variable">hash_int</span> <span className="code-operator">=</span> <span className="code-function">int</span>(<span className="code-variable">new_block</span>.<span className="code-variable">hash</span>, <span className="code-number">16</span>)
        <span className="code-keyword">if</span> <span className="code-variable">hash_int</span> <span className="code-operator">=</span> <span className="code-variable">self</span>.<span className="code-variable">target</span>:
            <span className="code-keyword">break</span>
    
    <span className="code-keyword">return</span> <span className="code-variable">new_block</span>
            </pre>
            
            <h3>4.2 Reward Mechanism</h3>
            <p>
              Miners who successfully add blocks to the blockchain receive two types of rewards:
            </p>
            <ul>
              <li><strong>Block Subsidy:</strong> New coins created with each block (starts at 50 GCN, halves every 210,000 blocks)</li>
              <li><strong>Transaction Fees:</strong> Fees from all transactions included in the block</li>
            </ul>
            <p>
              This dual incentive structure ensures miners remain motivated to secure the network even as the block subsidy 
              diminishes over time.
            </p>
            
            <div className="whitepaper-diagram">
              <div className="diagram-container">
                <img src="/assets/difficulty_adjustment.svg" alt="GlobalCoyn Difficulty Adjustment" className="diagram" style={{maxWidth: '100%', height: 'auto', display: 'block', margin: '0 auto'}} />
              </div>
            </div>
          </section>
          
          <section id="network" className="whitepaper-section">
            <h2>5. Network Architecture</h2>
            
            <h3>5.1 Node Types and Roles</h3>
            <p>
              The GlobalCoyn network consists of several node types, each with specific responsibilities:
            </p>
            <ul>
              <li><strong>Bootstrap Nodes:</strong> Always-online nodes that provide reliable entry points to the network</li>
              <li><strong>Full Nodes:</strong> Store the complete blockchain and validate transactions</li>
              <li><strong>Mining Nodes:</strong> Full nodes that also participate in the mining process</li>
              <li><strong>Light Clients:</strong> Connect to full nodes to access blockchain data without storing it locally</li>
            </ul>
            
            <h3>5.2 Node Discovery and Connectivity</h3>
            <p>
              GlobalCoyn implements a robust node discovery protocol:
            </p>
            <ul>
              <li><strong>DNS Seeds:</strong> Hardcoded DNS records for bootstrap node discovery</li>
              <li><strong>Peer Exchange:</strong> Nodes share known peers to improve network connectivity</li>
              <li><strong>Connection Backoff:</strong> Intelligent retry mechanism for failed connections</li>
              <li><strong>Geographical Distribution:</strong> Network topology optimization for global accessibility</li>
            </ul>
            
            <pre className="code-block">
{`class ImprovedNodeDiscovery:
    """Enhanced node discovery with better peer management and resilience"""
    
    def discover_peers(self):
        """
        Discover peers in the network.
        
        Returns:
            List[Dict[str, Any]]: List of discovered peers
        """
        discovered = []
        
        # Try bootstrap nodes first
        for node in self.bootstrap_nodes:
            try:
                host = node.get("host")
                port = node.get("web_port", 8001)
                url = f"http://{host}:{port}/api/network/peers"
                
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'peers' in data:
                        for peer in data['peers']:
                            # Process and store peers
                            # ...
            except Exception as e:
                logger.warning(f"Error discovering peers from {host}:{port}: {str(e)}")
        
        # If we're low on discovered nodes, try asking known peers
        if len(discovered) < 5 and self.known_peers:
            # Query known peers for additional peers
            # ...
        
        return discovered`}
            </pre>
            
            <div className="whitepaper-diagram">
              <div className="diagram-container">
                <img src="/assets/network_topology.svg" alt="GlobalCoyn Network Topology" className="diagram" style={{maxWidth: '100%', height: 'auto', display: 'block', margin: '0 auto'}} />
              </div>
            </div>
            
            <h3>5.3 Data Propagation</h3>
            <p>
              The network propagates two primary types of data:
            </p>
            <ul>
              <li><strong>Transactions:</strong> Broadcast to all connected peers when submitted</li>
              <li><strong>Blocks:</strong> Distributed throughout the network when mined</li>
            </ul>
            <p>
              To optimize network performance, GlobalCoyn implements:
            </p>
            <ul>
              <li>Compact block relay to reduce bandwidth usage</li>
              <li>Efficient transaction verification to minimize processing overhead</li>
              <li>Prioritized message handling for critical updates</li>
            </ul>
          </section>
          
          <section id="wallets" className="whitepaper-section">
            <h2>6. Wallet Implementation</h2>
            
            <h3>6.1 Key Generation and Management</h3>
            <p>
              GlobalCoyn wallets use industry-standard cryptographic primitives:
            </p>
            <ul>
              <li><strong>Key Algorithm:</strong> ECDSA with secp256k1 curve (same as Bitcoin)</li>
              <li><strong>Address Format:</strong> Base58 encoded with version byte and checksum</li>
              <li><strong>Mnemonic Support:</strong> BIP-39 compatible seed phrases for backup</li>
              <li><strong>Encryption:</strong> AES-256 for secure storage of private keys</li>
            </ul>
            
            <pre className="code-block">
{`def _add_key_pair(self, private_key: SigningKey) -> str:
    """
    Add a key pair to the wallet and return the address.
    
    Args:
        private_key: ECDSA signing key
        
    Returns:
        Generated wallet address
    """
    public_key = private_key.get_verifying_key()
    
    # Generate address from public key
    pub_hash = hashlib.sha256(public_key.to_string()).digest()
    ripemd160 = hashlib.new('ripemd160')
    ripemd160.update(pub_hash)
    pub_hash = ripemd160.digest()
    
    # Add version byte (0x00 for mainnet)
    version_pub_hash = b'\\x00' + pub_hash
    
    # Double SHA256 for checksum
    checksum = hashlib.sha256(hashlib.sha256(version_pub_hash).digest()).digest()[:4]
    
    # Combine and encode to base58
    binary_address = version_pub_hash + checksum
    address = base58.b58encode(binary_address).decode('utf-8')
    
    # Store the address and keys
    self.addresses[address] = WalletAddress(private_key, public_key, address)
    
    return address`}
            </pre>
            
            <h3>6.2 Transaction Signing and Verification</h3>
            <p>
              The transaction lifecycle includes these key security steps:
            </p>
            <ol>
              <li><strong>Transaction Creation:</strong> User specifies recipient, amount, and fee</li>
              <li><strong>Transaction Signing:</strong> Private key signs the transaction hash</li>
              <li><strong>Network Broadcast:</strong> Signed transaction is submitted to the network</li>
              <li><strong>Verification:</strong> Nodes verify the signature against the public key</li>
              <li><strong>Confirmation:</strong> Miners include valid transactions in blocks</li>
            </ol>
            
            <h3>6.3 Wallet Interfaces</h3>
            <p>
              GlobalCoyn provides multiple wallet interfaces:
            </p>
            <ul>
              <li><strong>Web Wallet:</strong> Browser-based access for convenience</li>
              <li><strong>Command Line:</strong> Advanced functionality for technical users</li>
              <li><strong>API:</strong> Programmatic access for integrations</li>
            </ul>
            
            <div className="whitepaper-diagram">
              <div className="diagram-container">
                <img src="/assets/wallet_architecture.svg" alt="GlobalCoyn Wallet Architecture" className="diagram" style={{maxWidth: '100%', height: 'auto', display: 'block', margin: '0 auto'}} />
              </div>
            </div>
          </section>
          
          <section id="use-cases" className="whitepaper-section">
            <h2>7. Use Cases</h2>
            
            <h3>7.1 International Trade Settlement</h3>
            <p>
              GlobalCoyn addresses key challenges in international trade:
            </p>
            <ul>
              <li><strong>Reduced Currency Risk:</strong> Parties can settle in a neutral currency, minimizing exposure to third-country exchange rate fluctuations</li>
              <li><strong>Lower Conversion Costs:</strong> Fewer currency conversions result in reduced transaction fees</li>
              <li><strong>Faster Settlement:</strong> Blockchain technology enables near-real-time settlement without intermediaries</li>
              <li><strong>Transparent Pricing:</strong> Single reference point for goods and services globally</li>
            </ul>
            
            <h3>7.2 Commodity Trading</h3>
            <p>
              GlobalCoyn provides advantages for global commodity markets:
            </p>
            <ul>
              <li><strong>Neutral Valuation:</strong> Prices commodities independent of any national currency</li>
              <li><strong>Reduced Volatility:</strong> Less susceptible to individual nations' monetary policies</li>
              <li><strong>Simplified Hedging:</strong> One currency for pricing reduces the complexity of hedging strategies</li>
            </ul>
            
            <h3>7.3 Global Investment</h3>
            <p>
              For capital allocation across borders, GlobalCoyn offers:
            </p>
            <ul>
              <li><strong>Portfolio Diversification:</strong> A currency uncorrelated with national monetary policies</li>
              <li><strong>Valuation Consistency:</strong> Common denominator for asset valuation globally</li>
              <li><strong>Reduced Currency Mismatch:</strong> Match investment currencies with global revenue streams</li>
            </ul>
          </section>
          
          <section id="governance" className="whitepaper-section">
            <h2>8. Governance Structure</h2>
            
            <p>
              GlobalCoyn's governance model combines:
            </p>
            <ol>
              <li><strong>Algorithmic Governance:</strong> Core protocol rules are enforced by code</li>
              <li><strong>Distributed Node Operators:</strong> Decentralized network of independent validators</li>
              <li><strong>Protocol Improvements:</strong> Transparent process for evaluating and implementing upgrades</li>
            </ol>
            <p>
              This structure ensures no single nation, organization, or individual can control the currency, preserving its neutrality.
            </p>
            
            <h3>8.1 Protocol Updates</h3>
            <p>
              The GlobalCoyn improvement process follows these steps:
            </p>
            <ol>
              <li>Proposal submission with technical specification</li>
              <li>Community review and discussion period</li>
              <li>Reference implementation development</li>
              <li>Testnet deployment and verification</li>
              <li>Network-wide activation through node upgrades</li>
            </ol>
          </section>
          
          <section id="comparison" className="whitepaper-section">
            <h2>9. Comparison with Alternative Approaches</h2>
            
            <div className="table-container">
              <table className="comparison-table">
                <thead>
                  <tr>
                    <th>Feature</th>
                    <th>Gold Standard</th>
                    <th>Special Drawing Rights (SDR)</th>
                    <th>GlobalCoyn</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Independence from national currencies</td>
                    <td>High</td>
                    <td>Medium (basket of currencies)</td>
                    <td>High</td>
                  </tr>
                  <tr>
                    <td>Supply flexibility</td>
                    <td>Very Low</td>
                    <td>Medium</td>
                    <td>Medium-High</td>
                  </tr>
                  <tr>
                    <td>Monetary sovereignty preservation</td>
                    <td>Low</td>
                    <td>Medium</td>
                    <td>High</td>
                  </tr>
                  <tr>
                    <td>Transaction efficiency</td>
                    <td>Low</td>
                    <td>Medium</td>
                    <td>High</td>
                  </tr>
                  <tr>
                    <td>Transparency</td>
                    <td>Medium</td>
                    <td>Low</td>
                    <td>High</td>
                  </tr>
                  <tr>
                    <td>Accessibility</td>
                    <td>Low</td>
                    <td>Very Low (limited to central banks)</td>
                    <td>High</td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <h3>9.1 Comparison with Bitcoin</h3>
            <p>
              While GlobalCoyn shares some technical similarities with Bitcoin, there are key differences in purpose and design:
            </p>
            <ul>
              <li><strong>Purpose:</strong> GlobalCoyn is specifically designed for international trade settlement rather than general-purpose value storage</li>
              <li><strong>Economic Model:</strong> GlobalCoyn's supply algorithm is more responsive to global trade indicators</li>
              <li><strong>Network Structure:</strong> GlobalCoyn prioritizes reliable bootstrap nodes for improved global accessibility</li>
              <li><strong>Governance:</strong> GlobalCoyn includes more formal governance processes for protocol evolution</li>
            </ul>
          </section>
          
          {/* Implementation Path section removed */}
          
          <section id="challenges" className="whitepaper-section">
            <h2>10. Challenges and Mitigations</h2>
            
            <h3>10.1 Adoption Barriers</h3>
            <ul>
              <li><strong>Inertia of Existing Systems:</strong> Phased approach focusing on high-friction trade routes first</li>
              <li><strong>Regulatory Uncertainty:</strong> Proactive engagement with regulatory bodies</li>
              <li><strong>Technical Complexity:</strong> Development of simplified interfaces and integration tools</li>
            </ul>
            
            <h3>10.2 Volatility Management</h3>
            <ul>
              <li><strong>Liquidity Pools:</strong> Strategic reserves to manage early-stage price fluctuations</li>
              <li><strong>Circuit Breakers:</strong> Temporary trading limitations during extreme market conditions</li>
              <li><strong>Gradual Transition:</strong> Encouraging partial adoption alongside existing settlement methods initially</li>
            </ul>
            
            <h3>10.3 Security Considerations</h3>
            <ul>
              <li><strong>Network Attacks:</strong> Incentive structures and technical safeguards against common attack vectors</li>
              <li><strong>Smart Contract Risks:</strong> Limited, carefully audited smart contract functionality</li>
              <li><strong>Key Management:</strong> Multiple security levels with appropriate user education</li>
            </ul>
          </section>
          
          <section id="conclusion" className="whitepaper-section">
            <h2>11. Conclusion</h2>
            
            <p>
              GlobalCoyn represents a fundamental reimagining of international trade settlement through a neutral currency 
              that operates independently of national monetary policies. By leveraging blockchain technology, GlobalCoyn can 
              provide the benefits that gold once offered to the international monetary system—neutrality and universality—while 
              avoiding its primary drawback of restricting domestic monetary sovereignty.
            </p>
            <p>
              The technical foundation outlined in this whitepaper demonstrates how GlobalCoyn can function as an efficient, 
              transparent, and fair medium of exchange for international trade, potentially addressing long-standing imbalances 
              in the global economic system.
            </p>
            <p>
              As global trade continues to evolve in an increasingly complex geopolitical landscape, GlobalCoyn offers a path 
              toward a more balanced and efficient system of international exchange—one that works for all nations regardless 
              of size or economic influence.
            </p>
          </section>
          
          <section className="whitepaper-section appendix">
            <h2>Appendix A: Technical Specifications</h2>
            
            <div className="technical-specs">
              <h3>Core Protocol:</h3>
              <ul>
                <li><strong>Consensus:</strong> Proof-of-Work (Double SHA-256)</li>
                <li><strong>Block Time:</strong> 10 minutes (target)</li>
                <li><strong>Block Size:</strong> Dynamic with 1MB initial limit</li>
                <li><strong>Transaction Capacity:</strong> 3-7 transactions per second</li>
                <li><strong>Initial Reward:</strong> 50 GCN per block</li>
                <li><strong>Halving Interval:</strong> 210,000 blocks (approximately 4 years)</li>
                <li><strong>Total Supply:</strong> 21,000,000 GCN (maximum)</li>
                <li><strong>Difficulty Adjustment:</strong> Every 2,016 blocks</li>
              </ul>
              
              <h3>Network Protocol:</h3>
              <ul>
                <li><strong>P2P Protocol:</strong> TCP with custom messaging format</li>
                <li><strong>Default Ports:</strong> 9000 (P2P), 8001 (API)</li>
                <li><strong>Node Discovery:</strong> DNS seeds and peer exchange</li>
                <li><strong>Peer Management:</strong> Up to 8 outbound, 128 inbound connections</li>
                <li><strong>Bootstrap Nodes:</strong> Minimum 2 geographically distributed nodes</li>
              </ul>
              
              <h3>Cryptographic Primitives:</h3>
              <ul>
                <li><strong>Signatures:</strong> ECDSA with secp256k1 curve</li>
                <li><strong>Hashing:</strong> SHA-256, RIPEMD-160</li>
                <li><strong>Encoding:</strong> Base58Check for addresses</li>
                <li><strong>Key Derivation:</strong> BIP-39 compatible</li>
                <li><strong>Encryption:</strong> AES-256-GCM for wallet encryption</li>
              </ul>
            </div>
          </section>
          
          <section className="whitepaper-section references">
            <h2>References</h2>
            
            <ol className="reference-list">
              <li>Triffin, R. (1960). Gold and the Dollar Crisis: The Future of Convertibility. Yale University Press.</li>
              <li>Eichengreen, B. (2011). Exorbitant Privilege: The Rise and Fall of the Dollar and the Future of the International Monetary System. Oxford University Press.</li>
              <li>Nakamoto, S. (2008). Bitcoin: A Peer-to-Peer Electronic Cash System.</li>
              <li>International Monetary Fund. (2019). Special Drawing Right (SDR) Factsheet.</li>
              <li>Zhou, X. (2009). Reform the International Monetary System. BIS Review, 41.</li>
              <li>Buterin, V. (2014). A Next-Generation Smart Contract and Decentralized Application Platform. Ethereum Whitepaper.</li>
              <li>Szabo, N. (2005). Bit Gold. Unenumerated.</li>
              <li>Antonopoulos, A. M. (2017). Mastering Bitcoin: Programming the Open Blockchain. O'Reilly Media.</li>
            </ol>
          </section>
        </article>
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

export default Whitepaper;