import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Import pages
import HomePage from './pages/Home/HomePage';
import Dashboard from './pages/Dashboard/Dashboard';
import Wallet from './pages/Wallet/WalletOverview/Wallet';
import Explorer from './pages/Explorer/Explorer';
import BlockDetails from './pages/Explorer/components/BlockDetails';
import WalletDetails from './pages/Wallet/WalletDetails/WalletDetails';
import TransactionDetails from './pages/Explorer/components/TransactionDetails';
import Mining from './pages/Mining/MiningDashboard/Mining';
import Network from './pages/Network/Network';
import Settings from './pages/Settings/Settings';
import Whitepaper from './pages/Whitepaper/Whitepaper';
import ApiReference from './pages/ApiReference/ApiReference';
import Contracts from './pages/Contracts/ContractsOverview/Contracts';
import ContractDetails from './pages/Contracts/ContractDetails/ContractDetails';
import CreateContract from './pages/Contracts/CreateContract/CreateContract';
import Profile from './pages/Profile/Profile';
import DigitalSoul from './pages/DigitalSoul/DigitalSoul';
import CreateDigitalSoul from './pages/DigitalSoul/CreateDigitalSoul/CreateDigitalSoul';
import WorldViewer from './pages/DigitalSoul/WorldViewer/WorldViewer';

// Import components
import Layout from './components/common/Layout/Layout';

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
        
        {/* WorldViewer with full-width layout (no sidebar) */}
        <Route path="/app/soul/:username/world" element={<WorldViewer />} />
        
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
          <Route path="digital-soul" element={<DigitalSoul />} />
          <Route path="create-digital-soul" element={<CreateDigitalSoul />} />
          <Route path="mining" element={<Mining />} />
          <Route path="network" element={<Network />} />
          <Route path="profile" element={<Profile />} />
          <Route path="profile/:address" element={<Profile />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;