#!/bin/bash

# This script should be run on the server to check the status of services

echo "=== GlobalCoyn Server Status Check ==="
echo ""

echo "1. Check if globalcoyn-node service is running:"
sudo systemctl status globalcoyn-node 2>/dev/null || echo "globalcoyn-node service not found"
echo ""

echo "2. Check for running Python processes:"
ps aux | grep -i python | grep -v grep
echo ""

echo "3. Check Nginx configuration:"
echo "Nginx sites enabled:"
ls -la /etc/nginx/conf.d/
echo ""
echo "Nginx configuration:"
cat /etc/nginx/conf.d/globalcoyn.conf
echo ""

echo "4. Check if port 8001 is in use:"
sudo netstat -tuln | grep 8001 || echo "No process using port 8001"
echo ""

echo "5. Check logs:"
echo "Nginx error log:"
sudo tail -n 20 /var/log/nginx/error.log
echo ""

echo "6. Check if blockchain files exist:"
echo "Frontend files:"
ls -la /var/www/globalcoyn/frontend/build 2>/dev/null || echo "Frontend build directory not found"
echo ""
echo "Backend files:"
ls -la /var/www/globalcoyn/blockchain/node 2>/dev/null || echo "Blockchain node directory not found"
echo ""

echo "7. Check firewall status:"
sudo firewall-cmd --list-all 2>/dev/null || sudo ufw status 2>/dev/null || echo "Firewall command not found"
echo ""

echo "=== End of Status Check ==="