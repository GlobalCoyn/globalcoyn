#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GlobalCoyn - macOS Desktop Application Wrapper
---------------------------------------------
This wrapper properly sets the application name and icon for macOS
"""

import os
import sys
import platform
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# Import the main application
from macos_app import GlobalCoynApp

if __name__ == "__main__":
    # Set app ID for macOS
    if platform.system() == 'Darwin':
        os.environ['PYQT_MAC_WANTS_LAYER'] = '1'
        try:
            from Foundation import NSBundle
            bundle = NSBundle.mainBundle()
            info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
            info['CFBundleName'] = 'GlobalCoyn'  # Set the app name
        except ImportError:
            print("Foundation framework not available - app name may remain as Python")
    
    # Create application with appropriate name
    app = QApplication(sys.argv)
    app.setApplicationName("GlobalCoyn")
    app.setOrganizationName("GlobalCoyn Project")
    app.setOrganizationDomain("globalcoyn.com")
    
    # Set application icon
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "macapplogo.png")
    if os.path.exists(logo_path):
        app_icon = QIcon(logo_path)
        app.setWindowIcon(app_icon)
    
    # Create and show the main window
    window = GlobalCoynApp()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec_())