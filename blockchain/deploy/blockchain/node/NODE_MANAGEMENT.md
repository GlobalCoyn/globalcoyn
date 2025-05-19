# GlobalCoyn Node Management

This document explains how to manage GlobalCoyn blockchain nodes using the provided scripts.

## Starting Nodes

To start a GlobalCoyn node, use the `start_node.sh` script:

```bash
./start_node.sh
```

This will:
1. Automatically find available ports for the P2P network and web API
2. Configure the environment variables correctly
3. Start the node in the background with logging
4. Display connection information

### Node Configuration Options

You can customize node behavior with environment variables:

```bash
# Start node #2 with specific ports
GCN_NODE_NUM=2 GCN_P2P_PORT=9001 GCN_WEB_PORT=8002 ./start_node.sh
```

Available environment variables:
- `GCN_NODE_NUM`: Node number/ID (default: 1)
- `GCN_P2P_PORT`: P2P network port (default: 9000 + NODE_NUM - 1)
- `GCN_WEB_PORT`: Web API port (default: 8000 + NODE_NUM)
- `GCN_DATA_FILE`: Blockchain data file (default: blockchain_data.json)

## Running Multiple Nodes

The start script automatically finds available ports, so you can run multiple nodes concurrently:

```bash
# Start node 1
./start_node.sh

# Start node 2
GCN_NODE_NUM=2 ./start_node.sh

# Start node 3
GCN_NODE_NUM=3 ./start_node.sh
```

Each node will:
- Use a different set of ports
- Log to a different file (node_1.log, node_2.log, etc.)
- Connect to other running nodes automatically

## Shutting Down Nodes

To shut down all running GlobalCoyn nodes:

```bash
./shutdown_nodes.sh
```

This will:
1. Find all running node processes
2. Attempt to gracefully shut them down
3. Force terminate any that don't shut down gracefully
4. Verify that all nodes have been stopped

## Node Logs

Each node logs its activity to a separate file:

- Node 1: `node_1.log`
- Node 2: `node_2.log`
- Node 3: `node_3.log`

You can view the logs in real-time using:

```bash
tail -f node_1.log
```

## Comprehensive Testing

To test all API endpoints of a running node:

```bash
./comprehensive_test.sh [node_url]
```

By default, it tests against http://localhost:8001 (Node 1).

## Troubleshooting

If you encounter port conflicts when starting nodes:
1. Use the shutdown script to stop all nodes
2. Manually check for processes using the ports:
   ```bash
   lsof -i :8001
   lsof -i :9000
   ```
3. Manually kill any processes if needed:
   ```bash
   kill -9 <PID>
   ```
4. Restart the nodes with the start script