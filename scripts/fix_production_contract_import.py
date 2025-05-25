#!/usr/bin/env python3
"""
Fix production contract import issues
This script ensures the bootstrap nodes have the correct import statements
and that the globalcoyn_blockchain.py file is accessible.
"""

import os
import sys
import subprocess
import shutil

def run_command(cmd, check=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if check and result.returncode != 0:
            print(f"Command failed: {cmd}")
            print(f"Error: {result.stderr}")
            return False
        return result.stdout.strip()
    except Exception as e:
        print(f"Error running command {cmd}: {e}")
        return False

def fix_bootstrap_node_imports():
    """Fix import statements in bootstrap node app.py files"""
    print("Fixing bootstrap node imports...")
    
    # Find bootstrap node directories
    bootstrap_dirs = []
    for root, dirs, files in os.walk("/home/ec2-user"):
        if "app.py" in files and ("bootstrap" in root.lower() or "node" in root.lower()):
            bootstrap_dirs.append(root)
    
    if not bootstrap_dirs:
        print("No bootstrap node directories found")
        return False
    
    for node_dir in bootstrap_dirs:
        app_py_path = os.path.join(node_dir, "app.py")
        print(f"Checking {app_py_path}")
        
        try:
            # Read the current file
            with open(app_py_path, 'r') as f:
                content = f.read()
            
            # Check if it has old blockchain imports
            if "from blockchain import" in content:
                print(f"Updating imports in {app_py_path}")
                
                # Replace old imports with new ones
                content = content.replace("from blockchain import", "from globalcoyn_blockchain import")
                
                # Write back the file
                with open(app_py_path, 'w') as f:
                    f.write(content)
                
                print(f"Updated imports in {app_py_path}")
            else:
                print(f"Imports already correct in {app_py_path}")
                
        except Exception as e:
            print(f"Error updating {app_py_path}: {e}")
            continue
    
    return True

def ensure_core_files():
    """Ensure globalcoyn_blockchain.py exists in the core directories"""
    print("Ensuring core files exist...")
    
    # Find core directories
    core_dirs = []
    for root, dirs, files in os.walk("/home/ec2-user"):
        if "core" in dirs:
            core_path = os.path.join(root, "core")
            if os.path.exists(core_path):
                core_dirs.append(core_path)
    
    for core_dir in core_dirs:
        globalcoyn_blockchain_path = os.path.join(core_dir, "globalcoyn_blockchain.py")
        blockchain_path = os.path.join(core_dir, "blockchain.py")
        
        print(f"Checking core directory: {core_dir}")
        
        # If globalcoyn_blockchain.py doesn't exist but blockchain.py does, copy it
        if not os.path.exists(globalcoyn_blockchain_path) and os.path.exists(blockchain_path):
            try:
                shutil.copy2(blockchain_path, globalcoyn_blockchain_path)
                print(f"Copied blockchain.py to globalcoyn_blockchain.py in {core_dir}")
            except Exception as e:
                print(f"Error copying file in {core_dir}: {e}")
        
        # Check if the file exists now
        if os.path.exists(globalcoyn_blockchain_path):
            print(f"✓ globalcoyn_blockchain.py exists in {core_dir}")
        else:
            print(f"✗ globalcoyn_blockchain.py missing in {core_dir}")

def restart_bootstrap_services():
    """Restart the bootstrap node services"""
    print("Restarting bootstrap services...")
    
    services = ["globalcoyn-bootstrap1", "globalcoyn-bootstrap2"]
    
    for service in services:
        print(f"Restarting {service}...")
        
        # Stop the service
        result = run_command(f"sudo systemctl stop {service}", check=False)
        
        # Start the service
        result = run_command(f"sudo systemctl start {service}", check=False)
        
        # Check status
        result = run_command(f"sudo systemctl is-active {service}", check=False)
        print(f"{service} status: {result}")

def check_python_path():
    """Check and fix Python path issues"""
    print("Checking Python path...")
    
    # Show current Python path
    result = run_command("python3 -c 'import sys; print(\"\\n\".join(sys.path))'")
    if result:
        print("Current Python path:")
        print(result)
    
    # Check if we can import the module
    result = run_command("python3 -c 'from globalcoyn_blockchain import Blockchain; print(\"Import successful\")'", check=False)
    if result:
        print("✓ globalcoyn_blockchain import test successful")
    else:
        print("✗ globalcoyn_blockchain import test failed")

def main():
    """Main function"""
    print("Starting production contract import fix...")
    
    # Check if we're running as root or with appropriate permissions
    if os.geteuid() != 0:
        print("Warning: Not running as root. Some operations may fail.")
    
    # Fix the imports
    fix_bootstrap_node_imports()
    
    # Ensure core files exist
    ensure_core_files()
    
    # Check Python path
    check_python_path()
    
    # Restart services
    restart_bootstrap_services()
    
    print("Production contract import fix completed!")

if __name__ == "__main__":
    main()