#!/usr/bin/env python3
"""
GlobalCoyn Blockchain Node Wrapper
---------------------------------
This wrapper helps the node start properly by modifying
the Python path and using direct imports from the core directory.
"""
import os
import sys
import importlib.util
import traceback

# Set up the environment and paths
current_dir = os.path.dirname(os.path.abspath(__file__))
node_dir = os.path.join(current_dir, "node")
core_dir = os.path.join(current_dir, "core")

print(f"Current directory: {current_dir}")
print(f"Node directory: {node_dir}")
print(f"Core directory: {core_dir}")

# Add directories to Python path
sys.path.insert(0, current_dir)  # Main blockchain directory
sys.path.insert(0, node_dir)     # Node directory
sys.path.insert(0, core_dir)     # Core directory

# Create modules directory structure if it doesn't exist
os.makedirs(os.path.join(current_dir, "blockchain"), exist_ok=True)
os.makedirs(os.path.join(current_dir, "blockchain", "core"), exist_ok=True)

# Create __init__.py files if they don't exist
for path in [
    os.path.join(current_dir, "blockchain", "__init__.py"),
    os.path.join(current_dir, "blockchain", "core", "__init__.py"),
]:
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write("# Blockchain module\n")

# Create symbolic links to core modules in blockchain/core/
print("Setting up core module symbolic links...")
for file in os.listdir(core_dir):
    if file.endswith(".py"):
        source = os.path.join(core_dir, file)
        target = os.path.join(current_dir, "blockchain", "core", file)
        if not os.path.exists(target):
            try:
                os.symlink(source, target)
                print(f"Created symlink: {source} -> {target}")
            except Exception as e:
                print(f"Failed to create symlink: {e}")
                # Fallback to copying the file
                try:
                    import shutil
                    shutil.copy2(source, target)
                    print(f"Copied file instead: {source} -> {target}")
                except Exception as e:
                    print(f"Failed to copy file: {e}")

# Modify app.py to use direct imports if necessary
app_path = os.path.join(node_dir, "app.py")
app_backup_path = os.path.join(node_dir, "app.py.backup")

# Backup original app.py if it doesn't already exist
if os.path.exists(app_path) and not os.path.exists(app_backup_path):
    import shutil
    shutil.copy2(app_path, app_backup_path)
    print(f"Created backup of app.py: {app_backup_path}")

# Explicitly import core modules
print("Attempting to import core modules directly...")
try:
    sys.path.insert(0, core_dir)  # Ensure core dir is at the top of the path
    
    # Try direct imports
    print("Attempting direct imports from core directory...")
    from blockchain import Blockchain 
    from transaction import Transaction
    from block import Block
    from wallet import Wallet
    from mempool import Mempool
    from mining import Miner
    from utils import bits_to_target, target_to_bits, validate_address_format
    from coin import Coin, CoinManager
    
    print("Successfully imported core modules directly")
    
    # Now run the app
    print("Starting blockchain node...")
    os.chdir(node_dir)
    exec(open("app.py").read())
    
except ImportError as e:
    print(f"Import error: {e}")
    traceback.print_exc()
    
    # Try looking for the modules in the filesystem
    print("\nSearching for core modules in the filesystem:")
    for path in [core_dir, os.path.join(current_dir, "blockchain", "core")]:
        print(f"Looking in {path}:")
        if os.path.exists(path):
            files = [f for f in os.listdir(path) if f.endswith('.py')]
            for file in files:
                print(f"  Found: {file}")
        else:
            print(f"  Directory doesn't exist")
    
    # Try importing modules directly by loading from filesystem
    print("\nAttempting to load modules from filesystem...")
    try:
        # Get the blockchain.py file path
        blockchain_path = os.path.join(core_dir, "blockchain.py")
        if os.path.exists(blockchain_path):
            # Use importlib to load the module
            spec = importlib.util.spec_from_file_location("blockchain_module", blockchain_path)
            blockchain_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(blockchain_module)
            
            # Extract the Blockchain class
            Blockchain = blockchain_module.Blockchain
            print("Successfully loaded Blockchain class from filesystem")
            
            # Now we can try to load and run app.py with our modules available
            print("Starting blockchain node with loaded modules...")
            os.chdir(node_dir)
            
            # Create globals dict with our imported modules
            globals_dict = {
                "Blockchain": Blockchain,
                # Add other modules here as needed
            }
            
            # Execute app.py with our globals
            with open("app.py") as f:
                exec(f.read(), globals_dict)
        else:
            print(f"blockchain.py not found at: {blockchain_path}")
    except Exception as e:
        print(f"Failed to load module from filesystem: {e}")
        traceback.print_exc()
        sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    traceback.print_exc()
    sys.exit(1)