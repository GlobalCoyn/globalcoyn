# GlobalCoyn

A decentralized digital currency for the modern world.

![GlobalCoyn Logo](frontend/public/assets/logo.png)

## Overview

GlobalCoyn is a blockchain-based solution for international trade, independent from any nation's domestic monetary policy. It creates a decentralized currency that reflects global economic activity rather than being tied to any single nation's influence.

## Features

- **Fully Decentralized** - Peer-to-peer network with no central authority
- **Secure and Transparent** - All transactions are cryptographically verified and publicly auditable
- **Modern Web Interface** - Intuitive dashboard and block explorer
- **Wallet Management** - Secure wallet creation and transaction capabilities
- **Network Statistics** - Real-time tracking of blockchain metrics
- **Bootstrap Nodes** - Reliable entry points for network synchronization

## Repository Structure

- `/core` - Core blockchain implementation (blocks, transactions, consensus)
- `/api` - API endpoints for network communication
- `/node` - Node template for running blockchain nodes
- `/frontend` - React-based web interface
- `/docs` - Technical documentation
- `/scripts` - Deployment and utility scripts
- `/.github` - GitHub Actions workflows for CI/CD

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 14+
- React 17+
- Flask 2.0+

### Local Development

#### Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/GlobalCoyn/globalcoyn.git
   cd globalcoyn
   ```

2. Set up a Python virtual environment:
   ```bash
   cd node
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure the node:
   ```bash
   cp production_config.example.json production_config.json
   # Edit production_config.json with your settings
   ```

4. Start the node:
   ```bash
   python app.py
   ```

#### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. The application will be available at http://localhost:3000

### Deployment

#### Setting Up a Node

1. Prepare a server with Python 3.9+ installed
2. Copy the node files to your server
3. Install dependencies: `pip install -r requirements.txt`
4. Configure settings in `production_config.json`
5. Set up as a service using the template in `node/deploy/globalcoyn-node.service`
6. Configure Nginx using the template in `node/deploy/globalcoyn.conf`

#### Deploying the Frontend

1. Build the frontend: 
   ```bash
   cd frontend
   npm run build
   ```
2. Deploy to your web server

#### Automated Deployment with GitHub Actions

This repository includes GitHub Actions workflows for automated deployment. To use them:

1. Fork this repository
2. Set up the following repository secrets:
   - `EC2_HOST`: Your EC2 server's IP address or hostname
   - `EC2_USERNAME`: SSH username (usually `ec2-user` for Amazon Linux)
   - `DEPLOY_KEY`: SSH private key for access to your server
   - `DOWNLOAD_URL`: URL for downloading artifacts

For more details, see the [GitHub Deployment Guide](docs/GITHUB_DEPLOYMENT.md).

## Running Bootstrap Nodes

Bootstrap nodes are critical to the GlobalCoyn network as they provide reliable entry points for other nodes.

1. Configure the bootstrap node:
   ```bash
   cd node
   cp production_config.example.json production_config.json
   # Edit settings in production_config.json
   ```

2. Deploy and run:
   ```bash
   python app.py
   ```

3. For production use, set up as a system service:
   ```bash
   sudo cp deploy/globalcoyn-node.service /etc/systemd/system/
   sudo systemctl enable globalcoyn-node
   sudo systemctl start globalcoyn-node
   ```

## API Documentation

GlobalCoyn provides REST APIs for interacting with the blockchain. See [BLOCKCHAIN_API.md](docs/BLOCKCHAIN_API.md) for detailed API documentation.

## Architecture

For detailed architecture information, see [BLOCKCHAIN_ARCHITECTURE.md](docs/BLOCKCHAIN_ARCHITECTURE.md).

## Contributing

We welcome contributions to GlobalCoyn! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to your branch: `git push origin feature/your-feature-name`
5. Submit a pull request

Please ensure your code follows our style guidelines and includes appropriate tests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- All contributors who have helped build and improve GlobalCoyn
- The blockchain community for inspiration and knowledge sharing