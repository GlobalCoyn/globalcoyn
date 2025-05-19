# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, BUNDLE

block_cipher = None

a = Analysis(
    ['app_wrapper.py'],
    pathex=[os.path.abspath(os.getcwd())],
    binaries=[],
    datas=[('resources/*.png', 'resources')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GlobalCoyn',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/macapplogo.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GlobalCoyn',
)

app = BUNDLE(
    coll,
    name='GlobalCoyn.app',
    icon='resources/macapplogo.png',
    bundle_identifier='com.globalcoyn.app',
    info_plist={
        'CFBundleDisplayName': 'GlobalCoyn',
        'CFBundleName': 'GlobalCoyn',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': 'True',
        'NSHumanReadableCopyright': '© 2023-2025 GlobalCoyn Project',
    },
)
