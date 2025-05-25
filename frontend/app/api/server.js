const express = require('express');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const path = require('path');

// Import route modules
const blockchainRoutes = require('./routes/blockchain');
const walletRoutes = require('./routes/wallet');
const networkRoutes = require('./routes/network');
const miningRoutes = require('./routes/mining');
const contractRoutes = require('./routes/contract');
const profileRoutes = require('./routes/profile');

// Create Express app
const app = express();
const PORT = process.env.PORT || 5000;

// Apply middleware with explicit CORS configuration
app.use(cors({
  origin: ['http://localhost:3000', 'http://127.0.0.1:3000'],
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true
}));
app.use(express.json());

// Apply rate limiting
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per window
  standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
  legacyHeaders: false, // Disable the `X-RateLimit-*` headers
  message: {
    status: 429,
    message: 'Too many requests, please try again later.'
  }
});

// Apply rate limiting to API routes
app.use('/api', apiLimiter);

// Define routes
app.use('/api/blockchain', blockchainRoutes);
app.use('/api/wallet', walletRoutes);
app.use('/api/network', networkRoutes);
app.use('/api/mining', miningRoutes);
app.use('/api/contracts', contractRoutes);
app.use('/api/profiles', profileRoutes);

// Health check endpoint
app.get('/api/status', (req, res) => {
  res.json({
    status: 'online',
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// Serve static assets in production
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, '../build')));

  app.get('*', (req, res) => {
    res.sendFile(path.resolve(__dirname, '../build', 'index.html'));
  });
}

// Start the server
app.listen(PORT, () => {
  console.log(`API server running on port ${PORT}`);
});

module.exports = app; // For testing