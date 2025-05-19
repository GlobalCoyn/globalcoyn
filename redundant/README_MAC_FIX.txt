GlobalCoyn macOS App Fix Instructions
===============================

The error you're seeing indicates that the Python "requests" library is missing, which is required by the GlobalCoyn app. You have two options to fix this:

Option 1: Run the fix script (recommended)
------------------------------------------

1. Copy the "fix_macos_app_deps.sh" file to the other MacBook
2. Open Terminal on that MacBook
3. Navigate to where you saved the script, for example:
   cd ~/Downloads
4. Make the script executable (if needed):
   chmod +x fix_macos_app_deps.sh
5. Run the script with sudo permissions:
   sudo ./fix_macos_app_deps.sh
6. Enter your password when prompted
7. The script will install the required dependencies and update the launcher

After running the script, you should be able to double-click on GlobalCoyn.command to start the app.

Option 2: Manual installation
----------------------------

If you prefer to install the dependencies manually:

1. Open Terminal
2. Run the following commands:

   # Check which Python version is being used
   /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 --version
   
   # Install the requests module
   /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 -m pip install requests

3. If that doesn't work, try using your system's default Python:
   python3 -m pip install requests

After installing the dependencies, try running the GlobalCoyn app again.

Option 3: Create a virtual environment
-------------------------------------

If the above options don't work, you can try creating a Python virtual environment:

1. Open Terminal
2. Navigate to the GlobalCoyn app directory:
   cd /Applications/GlobalCoyn
3. Create a virtual environment:
   python3 -m venv venv
4. Activate the virtual environment:
   source venv/bin/activate
5. Install the required packages:
   pip install requests
6. Update the GlobalCoyn.command file to use the virtual environment:
   
   # Edit the file
   sudo nano GlobalCoyn.command
   
   # Replace the content with:
   #!/bin/bash
   cd "$(dirname "$0")"
   source venv/bin/activate
   python app_wrapper.py
   
   # Save and exit (Ctrl+O, Enter, Ctrl+X)
   
7. Make it executable:
   chmod +x GlobalCoyn.command

Troubleshooting
--------------

If you're still having issues:

1. Check if Python is installed correctly:
   python3 --version
   
2. Check where Python is installed:
   which python3
   
3. List installed Python packages:
   pip3 list

4. Try upgrading pip:
   python3 -m pip install --upgrade pip

5. Check for any system restrictions that might prevent installing packages

If all else fails, please contact support@globalcoyn.com with details of your macOS version and the error messages you're seeing.