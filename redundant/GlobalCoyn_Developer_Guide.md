# GlobalCoyn Wallet - Developer Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Application Architecture](#application-architecture)
3. [Development Environment Setup](#development-environment-setup)
4. [Building from Source](#building-from-source)
5. [Signing and Notarization](#signing-and-notarization)
6. [Testing](#testing)
7. [Customization](#customization)
8. [Troubleshooting](#troubleshooting)

## Introduction

This guide provides comprehensive information for developers who want to build, customize, or extend the GlobalCoyn Wallet for macOS. The application is built using Python with PyQt5 for the user interface, and integrates a full GlobalCoyn blockchain node.

## Application Architecture

### Core Components

The GlobalCoyn Wallet application consists of several key components:

1. **Core Blockchain Components**
   - `blockchain.py` - Core blockchain implementation
   - `coin.py` - Cryptocurrency implementation
   - `wallet.py` - Wallet functionality
   - `price_oracle.py` - Price feed integration

2. **Network Components**
   - `improved_node_sync.py` - Blockchain synchronization
   - `node_discovery.py` - Peer discovery
   - `node_manager.py` - Node lifecycle management

3. **UI Components**
   - `app_wrapper.py` - Application startup wrapper
   - `macos_app.py` - Main application UI
   - `GlobalCoyn.command` - Shell launcher

4. **Optimized Components**
   - `rate_limited_logger.py` - Optimized logging
   - `wallet_cache.py` - Wallet data caching
   - `connection_backoff.py` - Connection management
   - `improved_node_sync_optimized.py` - Optimized sync

### Directory Structure

When built, the application has the following structure:

```
GlobalCoyn.app/
├── Contents/
│   ├── Info.plist
│   ├── MacOS/
│   │   └── GlobalCoyn (executable)
│   └── Resources/
│       ├── GlobalCoyn.icns
│       ├── base_library.zip
│       ├── lib/
│       ├── core/
│       │   ├── blockchain.py
│       │   ├── coin.py
│       │   ├── wallet.py
│       │   └── price_oracle.py
│       ├── network/
│       │   └── improved_node_sync.py
│       └── resources/
│           └── macapplogo.png
GlobalCoyn.command
setup_data_dir.command
README.txt
```

### Application Flow

1. User launches `GlobalCoyn.command` or the `.app` bundle
2. The launcher checks dependencies and sets up the environment
3. `app_wrapper.py` starts the application and configures macOS-specific settings
4. `macos_app.py` creates the main application window and UI
5. The application checks for an existing node or sets up a new one
6. Blockchain synchronization begins
7. The UI is populated with blockchain and wallet data

## Development Environment Setup

### Prerequisites

To develop the GlobalCoyn Wallet, you need:

- macOS 10.14+ (Mojave or newer)
- Python 3.8+
- Git (for source control)
- Xcode Command Line Tools

### Setting Up the Environment

1. **Install Xcode Command Line Tools**

```bash
xcode-select --install
```

2. **Install Homebrew**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

3. **Install Python (if not already installed)**

```bash
brew install python
```

4. **Install required tools**

```bash
brew install create-dmg
```

5. **Clone the repository**

```bash
git clone https://github.com/globalcoyn/blockchain.git
cd blockchain
```

6. **Install Python dependencies**

```bash
pip3 install -r requirements.txt
```

7. **Setup build environment**

```bash
./setup_build_env.sh
```

## Building from Source

The build process consists of several steps:

1. **Setup build directory**

```bash
./setup_build_dir.sh
```

This script:
- Creates a clean build directory
- Copies all necessary files
- Sets up the proper directory structure
- Creates launcher scripts with error handling

2. **Run PyInstaller**

```bash
pyinstaller GlobalCoyn.spec
```

This creates the application bundle in `dist/GlobalCoyn.app`.

3. **Create DMG installer**

```bash
./create_signed_dmg.sh
```

This creates a DMG file for distribution in the `dist` directory.

### Build Scripts

The repository contains several scripts to help with the build process:

- `setup_build_env.sh` - Sets up the build environment
- `setup_build_dir.sh` - Creates the build directory structure
- `GlobalCoyn.spec` - PyInstaller specification file
- `create_signed_dmg.sh` - Creates a signed DMG installer

## Signing and Notarization

To distribute the application outside the App Store, you should sign and notarize it:

### Prerequisites for Signing

- Apple Developer account
- Developer ID Application certificate
- App-specific password for your Apple ID

### Code Signing Process

1. **Obtain a Developer ID**

If you don't have a Developer ID certificate:
- Sign in to developer.apple.com
- Go to Certificates, IDs & Profiles
- Create a Developer ID Application certificate

2. **Sign the Application**

Use the `create_signed_dmg.sh` script with your Developer ID:

```bash
./create_signed_dmg.sh --developer-id "Developer ID Application: Your Name (XXXXXXXXXX)"
```

3. **Notarize the Application**

Add notarization parameters to the script:

```bash
./create_signed_dmg.sh \
  --developer-id "Developer ID Application: Your Name (XXXXXXXXXX)" \
  --notarization-username "your.email@example.com" \
  --notarization-password "@keychain:AC_PASSWORD"
```

4. **Staple the Notarization Ticket**

After notarization is approved, staple the ticket to the DMG:

```bash
xcrun stapler staple "dist/GlobalCoyn-1.0.0.dmg"
```

## Testing

### Testing the Build

After building the application, test it thoroughly:

1. Mount the DMG and install the application
2. Verify all components are included
3. Test startup and dependency checks
4. Verify node connection and synchronization
5. Test wallet creation and transactions
6. Test mining functionality
7. Verify blockchain explorer
8. Check all settings and configurations

### Automated Testing

Run the automated test script:

```bash
./test_app_build.sh
```

This script:
- Verifies app bundle structure
- Checks code signatures
- Tests launcher scripts
- Validates key functionality

## Customization

### Customizing the Application

To customize the application:

1. **Modify the build variables**

Edit `build_variables.sh` to change:
- Application name
- Version
- Bundle ID
- Copyright information

2. **Customize the user interface**

Main UI files:
- `macos_app.py` - Main UI implementation
- `resources/` - Icons and resources

3. **Change bootstrap nodes**

Edit `node_discovery.py` to modify the bootstrap nodes list.

4. **Adjust blockchain parameters**

Edit `core/blockchain.py` to modify blockchain parameters:
- Block time
- Mining difficulty
- Block rewards

## Troubleshooting

### Common Build Issues

**Missing Python Modules**

If PyInstaller fails with missing modules:
- Check the hidden imports in `GlobalCoyn.spec`
- Add missing imports to the `hidden_imports` list

**Code Signing Failures**

If code signing fails:
- Verify your Developer ID certificate is valid
- Check that certificate permissions are correct
- Ensure the bundle ID matches your certificate

**Application Crashes on Launch**

If the built application crashes:
- Check the logs at `~/Library/Logs/GlobalCoyn/`
- Verify all required files are in the build
- Make sure all dependencies are included

**DMG Creation Failures**

If DMG creation fails:
- Check that create-dmg is installed
- Verify file permissions
- Check for enough disk space

### Build Logs

Important logs for debugging build issues:

- PyInstaller build log: `build/GlobalCoyn/build.log`
- Code signing log: `build/GlobalCoyn/sign.log`
- Application logs: `~/Library/Logs/GlobalCoyn/`

---

This developer guide provides the information needed to build, customize, and troubleshoot the GlobalCoyn Wallet application. For further assistance, contact the development team or refer to the GitHub repository documentation.