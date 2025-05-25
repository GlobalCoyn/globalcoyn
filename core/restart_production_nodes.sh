#!/bin/bash
# Production Bootstrap Node Restart Script
# This script fixes import issues and restarts the bootstrap nodes

echo "Starting production bootstrap node restart..."

# Fix any remaining import issues in bootstrap node directories
echo "Fixing import statements..."
find /home/ec2-user -name "app.py" -type f -exec grep -l "from blockchain import" {} \; | while read file; do
    echo "Fixing imports in: $file"
    sed -i 's/from blockchain import/from globalcoyn_blockchain import/g' "$file"
done

# Ensure globalcoyn_blockchain.py exists in all core directories
echo "Ensuring core files exist..."
find /home/ec2-user -type d -name "core" | while read core_dir; do
    if [ -f "$core_dir/blockchain.py" ] && [ ! -f "$core_dir/globalcoyn_blockchain.py" ]; then
        echo "Copying blockchain.py to globalcoyn_blockchain.py in $core_dir"
        cp "$core_dir/blockchain.py" "$core_dir/globalcoyn_blockchain.py"
    fi
done

# Stop and restart bootstrap services
echo "Restarting bootstrap services..."
sudo systemctl stop globalcoyn-bootstrap1 globalcoyn-bootstrap2

# Wait a moment
sleep 2

# Start services
sudo systemctl start globalcoyn-bootstrap1
sudo systemctl start globalcoyn-bootstrap2

# Check status
echo "Checking service status..."
sudo systemctl status globalcoyn-bootstrap1 --no-pager -l
sudo systemctl status globalcoyn-bootstrap2 --no-pager -l

echo "Production bootstrap node restart completed!"