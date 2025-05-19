#!/usr/bin/env python3
"""
GlobalCoyn - Simple Launcher
---------------------------
This script launches the GlobalCoyn app directly, bypassing the app bundle process
which can be useful for testing or if the app bundle doesn't work properly.
"""

import os
import sys
import subprocess

# Find the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Move to that directory
os.chdir(script_dir)

# Run the app
try:
    print("Starting GlobalCoyn application...")
    result = subprocess.run([sys.executable, "app_wrapper.py"], 
                           check=True, text=True, 
                           stderr=subprocess.PIPE)
    print("Application exited successfully.")
except subprocess.CalledProcessError as e:
    print(f"Error running the application: {e}")
    print(f"Error details: {e.stderr}")
    
    # Keep terminal window open on error
    input("Press Enter to close this window...")