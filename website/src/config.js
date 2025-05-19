/**
 * GlobalCoyn API Configuration
 * ------------------------------
 * 
 * This file contains the configuration for the GlobalCoyn API endpoints.
 * In production, the API endpoints point to globalcoyn.com.
 * In development, they point to localhost with the appropriate port.
 */

// Check if we're in production or development
const isProduction = process.env.NODE_ENV === 'production';

// Base URL for API calls 
const API_BASE_URL = isProduction 
    ? "https://globalcoyn.com/api"
    : "http://localhost:8001/api";

// API endpoints
export const API_ENDPOINTS = {
    BLOCKCHAIN: `${API_BASE_URL}/blockchain`,
    NETWORK: `${API_BASE_URL}/network`,
    WALLET: `${API_BASE_URL}/wallet`,
    MINING: `${API_BASE_URL}/mining`, 
    TRANSACTIONS: `${API_BASE_URL}/transactions`
};

// WebSocket endpoints (if needed)
export const WS_ENDPOINTS = {
    BLOCKCHAIN: isProduction
        ? "wss://globalcoyn.com/ws/blockchain"
        : "ws://localhost:8001/ws/blockchain"
};

// Default values
export const DEFAULT_VALUES = {
    REFRESH_INTERVAL: 10000, // 10 seconds
    TRANSACTION_FEE: 0.001,
    MINING_TIMEOUT: 60000 // 1 minute
};

export default {
    API_ENDPOINTS,
    WS_ENDPOINTS,
    DEFAULT_VALUES,
    isProduction
};