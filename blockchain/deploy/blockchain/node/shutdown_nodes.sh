#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}GlobalCoyn Node Shutdown Script${NC}"
echo "This script will gracefully shut down all running GlobalCoyn nodes."
echo

# Function to find and kill node processes
find_and_kill_nodes() {
    # Find Python processes running app.py (GlobalCoyn nodes)
    local processes=$(ps aux | grep "python3 -u app.py" | grep -v grep)
    
    if [ -z "$processes" ]; then
        echo -e "${YELLOW}No running GlobalCoyn nodes found.${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}Found the following GlobalCoyn nodes:${NC}"
    echo "$processes" | awk '{print "PID: " $2 ", Command: " $11 " " $12 " " $13}'
    echo
    
    # Extract PIDs
    local pids=$(echo "$processes" | awk '{print $2}')
    
    echo -e "${YELLOW}Shutting down nodes...${NC}"
    
    # Kill each process
    for pid in $pids; do
        echo -ne "Shutting down node with PID $pid..."
        kill $pid 2>/dev/null
        
        # Wait a bit to see if it's terminated gracefully
        sleep 1
        
        # Check if it's still running
        if ps -p $pid > /dev/null; then
            echo -e "${YELLOW}Process did not terminate gracefully, force killing...${NC}"
            kill -9 $pid 2>/dev/null
            sleep 1
        fi
        
        # Final check
        if ps -p $pid > /dev/null; then
            echo -e "${RED}Failed to kill process $pid${NC}"
        else
            echo -e "${GREEN}Successfully terminated${NC}"
        fi
    done
}

# Find and kill processes that might be holding ports
kill_port_processes() {
    local base_ports=("8001" "8002" "8003" "8004" "8005" "9000" "9001" "9002" "9003" "9004" "9005")
    local found=false
    
    echo -e "${YELLOW}Checking for processes using GlobalCoyn ports...${NC}"
    
    for port in "${base_ports[@]}"; do
        local process=$(lsof -i ":$port" 2>/dev/null)
        if [ -n "$process" ]; then
            echo -e "${YELLOW}Found process using port $port:${NC}"
            echo "$process" | head -n2
            
            # Extract PID
            local pid=$(echo "$process" | awk 'NR==2 {print $2}')
            if [ -n "$pid" ]; then
                echo -e "Killing process $pid on port $port..."
                kill -9 $pid 2>/dev/null
                sleep 0.5
                
                # Verify port is now free
                if lsof -i ":$port" >/dev/null 2>&1; then
                    echo -e "${RED}Failed to free port $port${NC}"
                else
                    echo -e "${GREEN}Successfully freed port $port${NC}"
                fi
            fi
            
            found=true
        fi
    done
    
    if [ "$found" = false ]; then
        echo -e "${GREEN}No processes found using GlobalCoyn ports.${NC}"
    fi
}

# Function to clean log files
clean_log_files() {
    echo -e "${YELLOW}Cleaning node log files...${NC}"
    
    # Count log files before deletion
    local log_count=$(ls -1 node_*.log 2>/dev/null | wc -l)
    
    if [ "$log_count" -gt 0 ]; then
        echo -e "Found $log_count node log files to remove."
        
        # Remove all node log files
        rm -f node_*.log
        
        echo -e "${GREEN}All node log files removed.${NC}"
    else
        echo -e "${GREEN}No node log files found.${NC}"
    fi
}

# Function to kill all Python processes related to nodes
kill_all_python_nodes() {
    echo -e "${YELLOW}Looking for any Python processes related to GCN nodes...${NC}"
    
    # Find all Python processes that might be related to GCN nodes
    local python_processes=$(ps aux | grep "python" | grep -E "app\.py|node" | grep -v grep)
    
    if [ -n "$python_processes" ]; then
        echo -e "${YELLOW}Found Python processes that might be related to GCN:${NC}"
        echo "$python_processes"
        
        # Extract PIDs and kill them
        local pids=$(echo "$python_processes" | awk '{print $2}')
        for pid in $pids; do
            echo -e "Killing Python process with PID $pid..."
            kill -9 $pid 2>/dev/null
        done
        
        echo -e "${GREEN}All Python processes killed.${NC}"
    else
        echo -e "${GREEN}No additional Python processes found.${NC}"
    fi
}

# Main execution
echo -e "${YELLOW}Step 1: Killing node processes${NC}"
find_and_kill_nodes

echo
echo -e "${YELLOW}Step 2: Waiting for processes to terminate...${NC}"
sleep 2

echo
echo -e "${YELLOW}Step 3: Killing processes holding ports${NC}"
kill_port_processes

echo
echo -e "${YELLOW}Step 4: Killing any remaining Python processes${NC}"
kill_all_python_nodes

echo
echo -e "${YELLOW}Step 5: Cleaning up log files${NC}"
clean_log_files

echo
echo -e "${GREEN}Node shutdown and cleanup process completed.${NC}"
echo -e "${GREEN}All nodes have been stopped and logs cleared.${NC}"
echo -e "${YELLOW}To start nodes again, use the start_node.sh script.${NC}"
echo