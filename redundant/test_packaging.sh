#!/bin/bash
# Script to test the packaging scripts

# Exit on error
set -e

echo "Testing packaging scripts..."
echo "----------------------------------------"

# Package bootstrap node 1 (with minimal output)
echo "Packaging bootstrap node 1..."
./package_bootstrap_node.sh 1 > /dev/null
if [ -f "bootstrap_node_1.zip" ]; then
    echo "✓ Bootstrap node 1 packaged successfully"
    # Check the contents of the package
    echo "Checking package contents..."
    unzip -l bootstrap_node_1.zip | grep -q "bootstrap_config.py" && \
    unzip -l bootstrap_node_1.zip | grep -q "setup.sh" && \
    unzip -l bootstrap_node_1.zip | grep -q "README.md" && \
    echo "✓ Package contains required files"
else
    echo "✗ Failed to package bootstrap node 1"
    exit 1
fi

# Create a temporary directory for testing website packaging
TEST_DIR="./website_package_test"
rm -rf $TEST_DIR
mkdir -p $TEST_DIR

# Test website packaging
echo "----------------------------------------"
echo "Testing website packaging..."
cd $TEST_DIR
mkdir -p website/css website/js website/assets website/downloads
echo "<html><body>Test Website</body></html>" > website/index.html
echo "body { color: black; }" > website/css/style.css
echo "console.log('test');" > website/js/script.js
echo "test asset" > website/assets/test.txt

# Create a simple zip file
cd website
zip -r ../website.zip . > /dev/null
cd ..

if [ -f "website.zip" ]; then
    echo "✓ Website packaged successfully"
    # Check the contents of the package
    echo "Checking package contents..."
    unzip -l website.zip | grep -q "index.html" && \
    unzip -l website.zip | grep -q "css/style.css" && \
    unzip -l website.zip | grep -q "js/script.js" && \
    echo "✓ Package contains required files"
else
    echo "✗ Failed to package website"
    exit 1
fi

# Clean up
cd ..
rm -rf $TEST_DIR
rm -f bootstrap_node_1.zip

echo "----------------------------------------"
echo "All packaging tests passed!"
echo "----------------------------------------"