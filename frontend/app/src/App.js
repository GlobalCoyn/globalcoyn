import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Import pages
import HomePage from './pages/HomePage';
import Dashboard from './pages/Dashboard';
import Wallet from './pages/Wallet';
import Explorer from './pages/Explorer';
import BlockDetails from './pages/BlockDetails';
import WalletDetails from './pages/WalletDetails';
import TransactionDetails from './pages/TransactionDetails';
import Mining from './pages/Mining';
import Network from './pages/Network';
import Settings from './pages/Settings';
import Whitepaper from './pages/Whitepaper';
import ApiReference from './pages/ApiReference';
import Contracts from './pages/Contracts';
import ContractDetails from './pages/ContractDetails';
import CreateContract from './pages/CreateContract';

// Import components
import Layout from './components/Layout';

function App() {
  return (
    <Router>
      <Routes>
        {/* Home page uses the full-width layout */}
        <Route path="/" element={<HomePage />} />
        
        {/* Whitepaper page with full-width layout */}
        <Route path="/whitepaper" element={<Whitepaper />} />
        
        {/* API Reference page with full-width layout */}
        <Route path="/api-reference" element={<ApiReference />} />
        
        {/* App pages use the app layout with sidebar */}
        <Route path="/app" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="wallet" element={<Wallet />} />
          <Route path="explorer" element={<Explorer />} />
          <Route path="explorer/block/:blockHash" element={<BlockDetails />} />
          <Route path="explorer/address/:walletAddress" element={<WalletDetails />} />
          <Route path="explorer/transaction/:transactionId" element={<TransactionDetails />} />
          <Route path="contracts" element={<Contracts />} />
          <Route path="contracts/create" element={<CreateContract />} />
          <Route path="contracts/:contractAddress" element={<ContractDetails />} />
          <Route path="mining" element={<Mining />} />
          <Route path="network" element={<Network />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;