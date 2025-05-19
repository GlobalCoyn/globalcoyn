# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for GlobalCoyn macOS application
This creates a self-contained .app bundle with all required dependencies
"""

import os
import sys
from pathlib import Path
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, BUNDLE
from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

# Application version and metadata
APP_NAME = 'GlobalCoyn'
APP_VERSION = '1.0.0'
APP_ICON = 'build/GlobalCoyn/resources/macapplogo.png'
APP_ID = 'com.globalcoyn.app'

# Current directory where we're building from
CURRENT_DIR = os.path.abspath(os.getcwd())
BUILD_DIR = os.path.join(CURRENT_DIR, 'build/GlobalCoyn')

# Define the modules we need to explicitly include (hidden imports)
hidden_imports = [
    'flask',
    'requests',
    'psutil',
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'json',
    'hashlib',
    'time',
    'datetime',
    'random',
    'threading',
    'logging',
    'sqlite3',
    'socket',
    'platform',
    'uuid',
    'subprocess',
]

# Collect all required data for advanced packages
pkg_datas = []
pkg_binaries = []

for pkg in ['PyQt5']:
    pkg_datas_temp, pkg_binaries_temp, hiddenimports_temp = collect_all(pkg)
    pkg_datas.extend(pkg_datas_temp)
    pkg_binaries.extend(pkg_binaries_temp)
    hidden_imports.extend(hiddenimports_temp)

# Define data files to include
datas = [
    (os.path.join(BUILD_DIR, 'resources'), 'resources'),
    (os.path.join(BUILD_DIR, 'working_node.sh'), '.'),
    (os.path.join(BUILD_DIR, 'GlobalCoyn.command'), '.'),
    (os.path.join(BUILD_DIR, 'setup_data_dir.command'), '.'),
    (os.path.join(BUILD_DIR, 'README.txt'), '.'),
    ('get-pip.py', '.'),  # Include get-pip.py for installing pip if needed
]

# Add core modules directory
if os.path.exists(os.path.join(BUILD_DIR, 'core')):
    datas.append((os.path.join(BUILD_DIR, 'core'), 'core'))
else:
    print("WARNING: core directory not found in build dir, searching elsewhere...")
    for search_dir in [CURRENT_DIR, os.path.join(CURRENT_DIR, 'blockchain')]:
        core_dir = os.path.join(search_dir, 'core')
        if os.path.exists(core_dir):
            print(f"Found core directory at {core_dir}")
            datas.append((core_dir, 'core'))
            break

# Add network modules directory
if os.path.exists(os.path.join(BUILD_DIR, 'network')):
    datas.append((os.path.join(BUILD_DIR, 'network'), 'network'))
else:
    print("WARNING: network directory not found in build dir, searching elsewhere...")
    for search_dir in [CURRENT_DIR, os.path.join(CURRENT_DIR, 'blockchain')]:
        network_dir = os.path.join(search_dir, 'network')
        if os.path.exists(network_dir):
            print(f"Found network directory at {network_dir}")
            datas.append((network_dir, 'network'))
            break

# Add optimized modules directory
if os.path.exists(os.path.join(BUILD_DIR, 'optimized')):
    datas.append((os.path.join(BUILD_DIR, 'optimized'), 'optimized'))
else:
    print("WARNING: optimized directory not found in build dir, searching elsewhere...")
    for search_dir in [CURRENT_DIR, os.path.join(CURRENT_DIR, 'blockchain/apps/macos_app')]:
        optimized_dir = os.path.join(search_dir, 'optimized')
        if os.path.exists(optimized_dir):
            print(f"Found optimized directory at {optimized_dir}")
            datas.append((optimized_dir, 'optimized'))
            break

# Check for the main app wrapper
main_script = os.path.join(BUILD_DIR, 'improved_app_wrapper.py')
fallback_script = os.path.join(BUILD_DIR, 'app_wrapper.py')

if not os.path.exists(main_script):
    print(f"WARNING: {main_script} not found, searching for alternatives...")
    if os.path.exists(os.path.join(CURRENT_DIR, 'improved_app_wrapper.py')):
        main_script = os.path.join(CURRENT_DIR, 'improved_app_wrapper.py')
        print(f"Using improved_app_wrapper.py from current directory")
    elif os.path.exists(fallback_script):
        main_script = fallback_script
        print(f"Falling back to standard app_wrapper.py")
    else:
        print(f"ERROR: No suitable app wrapper found. Build will likely fail.")

# Main analysis
a = Analysis(
    [main_script],  # Use the selected wrapper script
    pathex=[CURRENT_DIR, BUILD_DIR],
    binaries=pkg_binaries,
    datas=datas + pkg_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib'],  # Exclude unnecessary large packages
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filter out unnecessary files to reduce size
def filter_binaries(binaries):
    exclude_patterns = [
        'libQt5Designer',
        'libQt5DesignerComponents',
        'libQt5Qml',
        'libQt5Quick',
        'libQt5Location',
        'libQt5Positioning',
        'libQt5Multimedia',
        'libQt5Sensors',
        'libQt5WebEngine',
        'libQt5WebEngineCore',
        'libQt5WebEngineWidgets',
        'QtQuick',
        'QtQml',
        'QtBluetooth',
        'QtLocation',
        'QtMultimedia',
        'QtPositioning',
        'QtSensors',
        'QtWebEngine',
    ]
    
    filtered = []
    for binary in binaries:
        if not any(pattern in binary[0] for pattern in exclude_patterns):
            filtered.append(binary)
    return filtered

a.binaries = filter_binaries(a.binaries)

# Create the executable
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,  # Enable argv emulation for macOS
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=APP_ICON,
)

# Collect all files
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)

# Create the macOS app bundle
app = BUNDLE(
    coll,
    name=f'{APP_NAME}.app',
    icon=APP_ICON,
    bundle_identifier=APP_ID,
    info_plist={
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleExecutable': APP_NAME,
        'CFBundlePackageType': 'APPL',
        'CFBundleIdentifier': APP_ID,
        'NSHighResolutionCapable': True,
        'CFBundleShortVersionString': APP_VERSION,
        'CFBundleVersion': APP_VERSION,
        'NSHumanReadableCopyright': '© 2023-2025 GlobalCoyn Project',
        'LSApplicationCategoryType': 'public.app-category.finance',
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        # Add document types if needed
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'GlobalCoyn Wallet',
                'CFBundleTypeExtensions': ['gcnwallet'],
                'CFBundleTypeRole': 'Editor',
            }
        ],
        # Add URL types if needed
        'CFBundleURLTypes': [
            {
                'CFBundleURLName': 'GlobalCoyn URL',
                'CFBundleURLSchemes': ['globalcoyn'],
            }
        ],
    },
)

# Print summary
print('='*80)
print(f'PyInstaller build specification for {APP_NAME} v{APP_VERSION}')
print(f'App bundle will be created at: dist/{APP_NAME}.app')
print('='*80)