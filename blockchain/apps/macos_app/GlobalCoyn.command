#!/bin/bash
# GlobalCoyn launcher script

# Find the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to that directory
cd "$DIR"

# Run the Python script
python3 simple_launcher.py