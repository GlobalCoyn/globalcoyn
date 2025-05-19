# GlobalCoyn: A Modern Cryptocurrency

GlobalCoyn is a decentralized cryptocurrency and blockchain platform designed for speed, security, and scalability. This repository contains all the code necessary to run a GlobalCoyn node, use the GlobalCoyn wallet, and interact with the GlobalCoyn network.

## Features

- **Decentralized and Secure**: Built on a proof-of-work consensus mechanism that ensures security and decentralization.
- **Fast Transactions**: Optimized block generation and transaction processing.
- **User-friendly Wallet**: Native macOS application for easy management of your GlobalCoyn.
- **Full Node Support**: Run your own GlobalCoyn node to help secure the network.
- **Developer-friendly API**: RESTful API for easy integration with other applications.

## Getting Started

### Prerequisites

- Python 3.9+
- Flask for running a node
- PyQt5 for the macOS wallet application

### Running a Node

1. Clone this repository:
```
git clone https://github.com/globalcoyn/globalcoyn.git
cd globalcoyn/node
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Run the node:
```
./start_node.sh
```

For more information on running a node, see our [Node Setup Guide](docs/NODE_SETUP.md).

### Using the Wallet

1. Download the latest wallet release from [globalcoyn.com](https://globalcoyn.com)
2. Extract the package and launch the application.
3. Follow the on-screen instructions to create or import a wallet.

For more information on using the wallet, see our [Wallet User Guide](docs/WALLET_GUIDE.md).

## Project Structure

```
blockchain/
├── README.md                     # Project overview and documentation
├── LICENSE                       # Project license
├── .gitignore                    # Git ignore file for the project
├── core/                         # Core blockchain functionality
│   ├── blockchain.py             # Blockchain implementation
│   ├── coin.py                   # Cryptocurrency implementation
│   ├── wallet.py                 # Wallet implementation
│   └── price_oracle.py           # Price oracle implementation
├── network/                      # Network and node synchronization
│   ├── node_sync.py              # Node synchronization logic
│   └── improved_node_sync.py     # Improved synchronization
├── api/                          # API endpoints
│   ├── server.py                 # Main API server
│   └── routes/                   # API routes
│       ├── blockchain_routes.py
│       ├── transaction_routes.py
│       └── network_routes.py
├── apps/                         # Application interfaces
│   ├── macos_app/                # MacOS application
│   │   ├── macos_app.py          # Application code
│   │   └── resources/            # Application resources
│   └── web_dashboard/            # Web dashboard
│       ├── dashboard.py
│       └── static/
├── node/                         # Node template for deployment
│   ├── app.py                    # Node application
│   ├── routes/                   # Node API routes
│   ├── requirements.txt          # Node dependencies
│   └── start_node.sh             # Node startup script
├── scripts/                      # Utility scripts
│   ├── installation/             # Installation scripts
│   └── testing/                  # Testing scripts
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
└── docs/                         # Documentation
    ├── BLOCKCHAIN_API.md
    └── BLOCKCHAIN_ARCHITECTURE.md
```

## Development

To contribute to GlobalCoyn development:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## Documentation

For more detailed information, check the documentation in the `docs` directory:

- [Architecture Overview](docs/BLOCKCHAIN_ARCHITECTURE.md)
- [API Documentation](docs/BLOCKCHAIN_API.md)
- [Development Guide](docs/DEVELOPMENT_GUIDE.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Bitcoin and other cryptocurrencies that paved the way
- The open-source community for their invaluable tools and libraries
- Everyone who has contributed to the GlobalCoyn project