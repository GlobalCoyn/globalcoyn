#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GlobalCoyn Dependency Installer
-------------------------------
This script handles automatic detection and installation of required dependencies
for the GlobalCoyn application. It includes fallback mechanisms for different
Python environments and handles various edge cases.
"""

import os
import sys
import platform
import subprocess
import time
import logging
import site
from pathlib import Path
import json
import tempfile
import shutil

# Set up logging
LOG_DIR = os.path.expanduser("~/Library/Logs/GlobalCoyn")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "dependency_installer.log")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("DependencyInstaller")

# Required packages with fallbacks
PACKAGES = [
    {"name": "PyQt5", "alternatives": ["PySide2"], "optional": False},
    {"name": "requests", "alternatives": [], "optional": False},
    {"name": "psutil", "alternatives": [], "optional": True},
    {"name": "flask", "alternatives": [], "optional": False},
]

def is_package_installed(package_name):
    """Check if a Python package is installed."""
    try:
        __import__(package_name)
        logger.info(f"Package {package_name} is installed")
        return True
    except ImportError:
        logger.info(f"Package {package_name} is not installed")
        return False

def get_missing_packages():
    """Get a list of missing required packages."""
    missing = []
    for package in PACKAGES:
        # Check for the main package
        if is_package_installed(package["name"]):
            continue
            
        # Check for alternatives
        found_alternative = False
        for alt in package["alternatives"]:
            if is_package_installed(alt):
                found_alternative = True
                break
                
        # If neither main nor alternatives are found, add to missing list
        if not found_alternative:
            if not package["optional"]:
                missing.append(package["name"])
            else:
                logger.info(f"Optional package {package['name']} is missing but will not be auto-installed")
    
    return missing

def has_pip():
    """Check if pip is installed and available."""
    try:
        # Check for pip using subprocess
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def install_pip():
    """Install pip using get-pip.py."""
    logger.info("Attempting to install pip using get-pip.py")
    
    # First, check if get-pip.py exists in the current directory
    get_pip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "get-pip.py")
    
    if not os.path.exists(get_pip_path):
        # Try to download get-pip.py
        logger.info("get-pip.py not found, attempting to download")
        try:
            import urllib.request
            url = "https://bootstrap.pypa.io/get-pip.py"
            get_pip_path = os.path.join(tempfile.gettempdir(), "get-pip.py")
            urllib.request.urlretrieve(url, get_pip_path)
            logger.info(f"Downloaded get-pip.py to {get_pip_path}")
        except Exception as e:
            logger.error(f"Failed to download get-pip.py: {str(e)}")
            return False
    
    # Run get-pip.py
    try:
        subprocess.run(
            [sys.executable, get_pip_path, "--user"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info("Successfully installed pip")
        
        # Update the PATH to include the user site-packages bin directory
        user_bin_dir = site.USER_BASE
        if platform.system() == "Windows":
            user_bin_dir = os.path.join(user_bin_dir, "Scripts")
        else:
            user_bin_dir = os.path.join(user_bin_dir, "bin")
            
        if user_bin_dir not in os.environ["PATH"].split(os.pathsep):
            os.environ["PATH"] = os.pathsep.join([user_bin_dir, os.environ["PATH"]])
            logger.info(f"Added {user_bin_dir} to PATH")
        
        return True
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to install pip: {str(e)}")
        return False

def install_packages(packages):
    """Install required packages using pip."""
    if not packages:
        logger.info("No packages to install")
        return True
    
    logger.info(f"Installing packages: {', '.join(packages)}")
    
    # Check if pip is available
    if not has_pip():
        logger.warning("pip is not installed")
        if not install_pip():
            logger.error("Failed to install pip, cannot install packages")
            return False
    
    # Install each package
    success = True
    for package in packages:
        logger.info(f"Installing {package}")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user", package],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"Successfully installed {package}")
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to install {package}: {str(e)}")
            if package not in [p["name"] for p in PACKAGES if p["optional"]]:
                success = False
    
    return success

def create_status_file(success):
    """Create a status file to indicate installation result."""
    status_dir = os.path.expanduser("~/Documents/GlobalCoyn")
    os.makedirs(status_dir, exist_ok=True)
    status_file = os.path.join(status_dir, "dependency_status.json")
    
    status = {
        "timestamp": time.time(),
        "success": success,
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "packages": []
    }
    
    # Check and add each required package
    for package in PACKAGES:
        pkg_status = {
            "name": package["name"],
            "installed": is_package_installed(package["name"]),
            "optional": package["optional"]
        }
        
        # Check alternatives if main package is not installed
        if not pkg_status["installed"] and package["alternatives"]:
            for alt in package["alternatives"]:
                if is_package_installed(alt):
                    pkg_status["alternative_installed"] = alt
                    break
        
        status["packages"].append(pkg_status)
    
    # Write status file
    with open(status_file, "w") as f:
        json.dump(status, f, indent=2)
    
    logger.info(f"Created status file at {status_file}")

def main():
    """Main function for dependency installation."""
    logger.info("Starting GlobalCoyn dependency installer")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"Platform: {platform.system()}")
    
    # Check for missing packages
    missing_packages = get_missing_packages()
    
    if not missing_packages:
        logger.info("All required packages are installed")
        create_status_file(True)
        return 0
    
    # Try to install missing packages
    logger.info(f"Missing packages: {', '.join(missing_packages)}")
    success = install_packages(missing_packages)
    
    # Create status file
    create_status_file(success)
    
    # Return appropriate exit code
    if success:
        logger.info("All dependencies installed successfully")
        return 0
    else:
        logger.error("Failed to install all required dependencies")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.exception("Unhandled exception in dependency installer")
        sys.exit(1)