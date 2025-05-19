#!/bin/bash
# Build variables for GlobalCoyn macOS app

# Application settings
export APP_NAME="GlobalCoyn"
export APP_VERSION="1.0.0"
export APP_BUNDLE_ID="com.globalcoyn.app"
export APP_COPYRIGHT="© 2023-2025 GlobalCoyn Project"

# Build directories
export BUILD_DIR="$(pwd)/build"
export DIST_DIR="$(pwd)/dist"
export MACOS_APP_DIR="$(pwd)/blockchain/apps/macos_app"

# Code signing settings
# Replace these with your actual Developer ID if you have one
export DEVELOPER_ID="Developer ID Application: Your Company Name (XXXXXXXXXX)"
export NOTARIZATION_USERNAME="your.email@example.com"
export NOTARIZATION_PASSWORD="@keychain:AC_PASSWORD"

# Bootstrap node settings
export BOOTSTRAP_NODE1="node1.globalcoyn.com:8001"
export BOOTSTRAP_NODE2="node2.globalcoyn.com:8001"
