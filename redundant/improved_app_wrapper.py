#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GlobalCoyn - Enhanced macOS Desktop Application Wrapper
-----------------------------------------------------
This wrapper properly sets the application name and icon for macOS
with improved error handling and dependency management
"""

import os
import sys
import platform
import logging
import traceback
import subprocess
from pathlib import Path
import time
import datetime

# Set up logging early
LOG_DIR = os.path.expanduser("~/Library/Logs/GlobalCoyn")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "globalcoyn_app.log")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("GlobalCoynApp")
logger.info("Starting GlobalCoyn Application")
logger.info(f"Python version: {platform.python_version()}")
logger.info(f"Operating system: {platform.system()} {platform.release()}")

# Create user data directory
DATA_DIR = os.path.expanduser("~/Documents/GlobalCoyn")
os.makedirs(DATA_DIR, exist_ok=True)
logger.info(f"Data directory: {DATA_DIR}")

# Function to check and install required packages
def check_and_install_packages():
    required_packages = ["PyQt5", "requests", "psutil"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"Package {package} is installed")
        except ImportError:
            logger.warning(f"Package {package} is missing")
            missing_packages.append(package)
    
    if missing_packages:
        logger.info(f"Installing missing packages: {', '.join(missing_packages)}")
        try:
            # Use pip to install missing packages
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            logger.info("Package installation completed successfully")
            
            # Restart the application to use newly installed packages
            logger.info("Restarting application to use newly installed packages")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            error_msg = f"Failed to install required packages: {str(e)}"
            logger.error(error_msg)
            show_error_message("Package Installation Failed", error_msg)
            sys.exit(1)


# Function to show error message (will be replaced with PyQt dialog if available)
def show_error_message(title, message):
    logger.error(f"{title}: {message}")
    try:
        # Try to use PyQt5 for error message
        from PyQt5.QtWidgets import QApplication, QMessageBox
        app = QApplication([])
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setDetailedText(f"Log file: {LOG_FILE}\nData directory: {DATA_DIR}")
        msg_box.exec_()
    except ImportError:
        # Fallback to console error
        print("\n" + "="*80)
        print(f"ERROR: {title}")
        print(message)
        print(f"Log file: {LOG_FILE}")
        print("="*80 + "\n")


# Attempt to install required packages
try:
    check_and_install_packages()
except Exception as e:
    logger.error(f"Failed during package check: {str(e)}")
    show_error_message("Initialization Error", f"Error checking packages: {str(e)}")
    sys.exit(1)

# Now we can import PyQt and other dependencies
try:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QSplashScreen
    from PyQt5.QtGui import QIcon, QPixmap
    from PyQt5.QtCore import Qt, QTimer
except ImportError as e:
    error_msg = f"Failed to import PyQt5 modules: {str(e)}"
    logger.error(error_msg)
    show_error_message("Import Error", error_msg)
    sys.exit(1)

# Check for other core files
try:
    # Check if macos_app.py exists (our main application file)
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "macos_app.py")
    if not os.path.exists(app_path):
        raise FileNotFoundError(f"Main application file not found: {app_path}")
    
    # Check for working_node.sh (required for node operations)
    node_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "working_node.sh")
    if not os.path.exists(node_script):
        raise FileNotFoundError(f"Node script not found: {node_script}")
    
    # Make sure working_node.sh is executable
    if platform.system() == 'Darwin' or platform.system() == 'Linux':
        os.chmod(node_script, 0o755)
except Exception as e:
    error_msg = f"File verification failed: {str(e)}"
    logger.error(error_msg)
    show_error_message("File Verification Error", error_msg)
    sys.exit(1)

try:
    # Import GlobalCoynApp class from the main application file
    from macos_app import GlobalCoynApp
except ImportError as e:
    error_msg = f"Failed to import main application: {str(e)}"
    logger.error(error_msg)
    show_error_message("Application Import Error", error_msg)
    sys.exit(1)

class EnhancedGlobalCoynApp(QApplication):
    """
    Enhanced application class with better error handling
    """
    def __init__(self, argv):
        super().__init__(argv)
        self.setApplicationName("GlobalCoyn")
        self.setOrganizationName("GlobalCoyn Project")
        self.setOrganizationDomain("globalcoyn.com")
        
        # Set application icon
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                "resources", "macapplogo.png")
        if os.path.exists(logo_path):
            app_icon = QIcon(logo_path)
            self.setWindowIcon(app_icon)
        
        # Set up exception handler
        sys.excepthook = self.handle_exception
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Global exception handler for the application"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Handle keyboard interrupt gracefully
            logger.info("Application terminated by keyboard interrupt")
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Log the exception
        logger.error("Uncaught exception", 
                    exc_info=(exc_type, exc_value, exc_traceback))
        
        # Format traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_text = ''.join(tb_lines)
        
        # Show error dialog
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle("Application Error")
        error_box.setText(f"An unexpected error occurred: {str(exc_value)}")
        error_box.setDetailedText(tb_text)
        error_box.setStandardButtons(QMessageBox.Ok)
        error_box.exec_()


def main():
    """Main entry point for the application"""
    try:
        # Set app ID for macOS
        if platform.system() == 'Darwin':
            os.environ['PYQT_MAC_WANTS_LAYER'] = '1'
            try:
                from Foundation import NSBundle
                bundle = NSBundle.mainBundle()
                info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                info['CFBundleName'] = 'GlobalCoyn'  # Set the app name
            except ImportError:
                logger.warning("Foundation framework not available - app name may remain as Python")
        
        # Create application with appropriate name
        app = EnhancedGlobalCoynApp(sys.argv)
        
        # Add a splash screen
        splash_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 "resources", "macapplogo.png")
        if os.path.exists(splash_path):
            splash_pix = QPixmap(splash_path)
            splash = QSplashScreen(splash_pix)
            splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.SplashScreen)
            splash.show()
            app.processEvents()
            
            # Display on splash screen
            splash.showMessage("Loading application...", 
                             Qt.AlignBottom | Qt.AlignCenter, 
                             Qt.white)
            
            # Give the splash screen time to display
            for i in range(5):
                splash.showMessage(f"Loading application... {i+1}/5", 
                                 Qt.AlignBottom | Qt.AlignCenter, 
                                 Qt.white)
                app.processEvents()
                time.sleep(0.3)
        else:
            splash = None
        
        # Create and show the main window
        window = GlobalCoynApp()
        
        # Close splash screen if it exists
        if splash:
            splash.finish(window)
        
        window.show()
        
        # Start the application event loop
        return app.exec_()
    
    except Exception as e:
        logger.error(f"Application initialization failed: {str(e)}", exc_info=True)
        show_error_message("Application Error", 
                         f"Application failed to start: {str(e)}\n\n"
                         f"Please check the log at: {LOG_FILE}")
        return 1


if __name__ == "__main__":
    sys.exit(main())