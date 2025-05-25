# Frontend Structure Guide

## Directory Organization

### 📁 components/
Reusable UI components organized by feature area:

- **common/**: Generic reusable components (Button, Modal, Layout, etc.)
- **blockchain/**: Blockchain-specific components (BlockCard, TransactionList, etc.)
- **contracts/**: Smart contract components (ContractCard, ContractForm, etc.)
- **wallet/**: Wallet-related components (WalletBalance, TransactionForm, etc.)
- **mining/**: Mining-specific components (MiningStatus, HashRateChart, etc.)

### 📁 pages/
Page components organized by feature:

- **Dashboard/**: Main dashboard page
- **Explorer/**: Blockchain explorer pages
- **Contracts/**: Contract-related pages (Create, Deploy, Execute, etc.)
- **Wallet/**: Wallet management pages
- **Mining/**: Mining dashboard and settings
- **Network/**: Network status and peer management
- **Settings/**: Application settings

### 📁 hooks/
Custom React hooks organized by feature:

- **common/**: Generic hooks (useApi, useLocalStorage, etc.)
- **blockchain/**: Blockchain-specific hooks
- **contracts/**: Contract-related hooks
- **wallet/**: Wallet management hooks

### 📁 services/
API and external service integrations:

- **api/**: REST API service modules
- **websocket/**: WebSocket service modules

### 📁 context/
React Context providers for global state management

### 📁 utils/
Utility functions and helpers:

- **constants.js**: App-wide constants
- **helpers.js**: General helper functions
- **formatting.js**: Data formatting utilities
- **validation.js**: Form validation utilities

### 📁 styles/
Global styles and themes:

- **globals.css**: Global CSS variables and resets
- **themes.css**: Theme definitions
- **variables.css**: CSS custom properties

### 📁 assets/
Static assets organized by type

## Component Structure

Each component should have its own folder with:
- `ComponentName.js` - React component
- `ComponentName.css` - Component-specific styles
- `index.js` - Export file (optional)

## Naming Conventions

- **Components**: PascalCase (e.g., `ContractCard`)
- **Files**: PascalCase for components, camelCase for utilities
- **Folders**: PascalCase for components, camelCase for utilities
- **CSS**: Same name as component file