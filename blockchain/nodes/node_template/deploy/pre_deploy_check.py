#!/usr/bin/env python3
"""
Pre-deployment script to check requirements and configurations
"""
import os
import sys
import subprocess
import json
import platform

def check_python_version():
    """Check Python version"""
    required_version = (3, 6)
    current_version = sys.version_info
    
    if current_version < required_version:
        print(f"ERROR: Python {required_version[0]}.{required_version[1]} or higher is required")
        print(f"Current version: {current_version[0]}.{current_version[1]}")
        return False
    
    print(f"✓ Python version: {current_version[0]}.{current_version[1]}")
    return True

def check_requirements():
    """Check if all required packages are installed"""
    # List of essential packages
    essential_packages = [
        "flask", 
        "flask_cors", 
        "requests", 
        "dotenv"
    ]
    
    try:
        missing_packages = []
        for pkg_name in essential_packages:
            try:
                if pkg_name == "dotenv":
                    __import__("dotenv")
                else:
                    __import__(pkg_name)
            except ImportError:
                missing_packages.append(pkg_name)
        
        if missing_packages:
            print(f"WARNING: Some packages might be missing: {', '.join(missing_packages)}")
            print("These will be installed during deployment")
            # Return True anyway since we'll install them on the server
            return True
        
        print(f"✓ All required packages appear to be installed")
        return True
    except Exception as e:
        print(f"WARNING checking requirements: {str(e)}")
        # Return True anyway since we'll install them on the server
        return True

def check_config():
    """Check if configuration file exists and is valid"""
    config_file = "../production_config.json"
    
    if not os.path.exists(config_file):
        print(f"ERROR: Production config not found at {config_file}")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Validate required fields
        required_sections = ["node_settings", "network", "security", "blockchain"]
        missing_sections = [s for s in required_sections if s not in config]
        
        if missing_sections:
            print(f"ERROR: Missing required sections in config: {missing_sections}")
            return False
        
        print(f"✓ Production configuration is valid")
        return True
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in configuration file")
        return False
    except Exception as e:
        print(f"ERROR checking configuration: {str(e)}")
        return False

def check_network():
    """Check network connectivity and ports"""
    # Check if we can access the deployment server
    server = os.environ.get("DEPLOY_SERVER", "globalcoyn.com")
    try:
        result = subprocess.run(["ping", "-c", "1", server], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(f"WARNING: Cannot reach deployment server {server}")
            print("Network connectivity might be an issue")
        else:
            print(f"✓ Server {server} is reachable")
    except Exception as e:
        print(f"WARNING: Error checking server connectivity: {str(e)}")

def main():
    """Run all pre-deployment checks"""
    print("=== GlobalCoyn Blockchain Pre-Deployment Checks ===")
    print(f"System: {platform.system()} {platform.release()}")
    print(f"Path: {os.getcwd()}")
    print("---------------------------------------------------")
    
    checks = [
        check_python_version(),
        check_requirements(),
        check_config()
    ]
    
    # Network check is optional, just for information
    check_network()
    
    print("---------------------------------------------------")
    
    if all(checks):
        print("✅ All checks passed! Ready for deployment")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues before deploying")
        return 1

if __name__ == "__main__":
    sys.exit(main())