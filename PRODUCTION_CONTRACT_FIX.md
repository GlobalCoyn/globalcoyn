# Production Contract Functionality Fix

## Issue
Contract deployment fails on production with error: "Contract functionality is not available on this node"

## Root Cause
Bootstrap nodes on production are not loading the updated contract-enabled blockchain code.

## Solution
Use the new `restart_with_contracts_production.sh` script to restart bootstrap nodes with proper contract support.

## Deployment Steps

### 1. The script is now in the repository
- `node/restart_with_contracts_production.sh` - Production restart script
- This will be automatically deployed to production via GitHub Actions

### 2. On Production Server
```bash
# SSH to production
ssh -i ~/Downloads/globalcoyn.pem ec2-user@13.61.79.186

# Navigate to the bootstrap node directory (GitHub Actions deploys here)
cd /home/ec2-user/bootstrap_node_1

# Run the contract-enabled restart script
./restart_with_contracts_production.sh
```

### 3. Expected Output
```
=== GlobalCoyn Production Contract Restart ===
Restarting Bootstrap Node 1...
Restarting Bootstrap Node 2...
✅ Bootstrap Node 1: SUCCESS (contracts working)
✅ Bootstrap Node 2: SUCCESS (contracts working)
🎉 SUCCESS: At least one node has working contract functionality!
```

### 4. Test Contract Deployment
```bash
# Test token contract deployment
curl -X POST http://localhost:8001/api/contracts/templates/token \
  -H "Content-Type: application/json" \
  -d '{
    "creator": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    "name": "ProductionTestToken",
    "symbol": "PTT",
    "initial_supply": 1000000,
    "fee": 100
  }'

# Expected response:
# {"status":"success","message":"Token contract ProductionTestToken (PTT) deployed successfully","contract_address":"ct_..."}
```

### 5. Alternative: Manual Bootstrap Node Restart
If the script doesn't work, manually restart each node:

```bash
# Stop systemd services
sudo systemctl stop globalcoyn-bootstrap1.service globalcoyn-bootstrap2.service

# Restart Node 1
cd /home/ec2-user/bootstrap_node_1
export PYTHONPATH="/home/ec2-user/bootstrap_node_1:/home/ec2-user/bootstrap_node_1/core:$PYTHONPATH"
export GCN_NODE_NUM=1 GCN_P2P_PORT=9000 GCN_WEB_PORT=8001 GCN_ENV="production"
nohup python3 app.py > contract_restart.log 2>&1 &

# Restart Node 2  
cd /home/ec2-user/bootstrap_node_2
export PYTHONPATH="/home/ec2-user/bootstrap_node_2:/home/ec2-user/bootstrap_node_2/core:$PYTHONPATH"
export GCN_NODE_NUM=2 GCN_P2P_PORT=9001 GCN_WEB_PORT=8002 GCN_ENV="production"
nohup python3 app.py > contract_restart.log 2>&1 &
```

## Files Changed
- `core/blockchain.py` → `core/globalcoyn_blockchain.py` (renamed to avoid import conflicts)
- `node/app.py` (updated imports to use `globalcoyn_blockchain`)
- `node/routes/contract_routes.py` (updated imports)
- `node/restart_with_contracts_production.sh` (new production restart script)

## Verification
After deployment, both production endpoints should work:
- `https://globalcoyn.com/api/contracts/types` ✅
- `https://globalcoyn.com/api/contracts/templates/token` ✅ (for contract deployment)