# GlobalCoyn macOS App Build System

This build system creates a standalone macOS application for GlobalCoyn cryptocurrency. The application includes:

- Complete GlobalCoyn node with blockchain synchronization
- Wallet functionality for sending and receiving GCN
- Mining capability
- Blockchain explorer
- Network statistics dashboard

## Quick Start

To build the GlobalCoyn macOS app:

```bash
# 1. Make all scripts executable
chmod +x *.sh

# 2. Run the master build script
./build_macos_app.sh
```

This will:
- Set up the build environment
- Create the build directory with all necessary files
- Build the app using PyInstaller
- Create a DMG installer
- Run build verification tests

The resulting application will be available in the `dist/` directory.

## Build Options

You can customize the build process with various options:

```bash
./build_macos_app.sh --help
```

Common options:
- `--skip-env-setup`: Skip environment setup step
- `--skip-signing`: Skip code signing
- `--skip-dmg`: Skip DMG creation
- `--app-version VERSION`: Set the app version (default: 1.0.0)
- `--developer-id ID`: Set Developer ID for code signing

For code signing and notarization:
```bash
./build_macos_app.sh \
  --developer-id "Developer ID Application: Your Name (XXXXXXXXXX)" \
  --notarization-username "your.email@example.com" \
  --notarization-password "@keychain:AC_PASSWORD"
```

## Build Components

The build system consists of several components:

1. **Setup Scripts**
   - `setup_build_env.sh`: Sets up the build environment
   - `setup_build_dir.sh`: Creates the build directory structure

2. **Core Components**
   - `improved_app_wrapper.py`: Enhanced application wrapper
   - `enhanced_node_script.sh`: Node startup script with better error handling
   - `dependency_installer.py`: Automatic dependency installation

3. **Build Scripts**
   - `GlobalCoyn.spec`: PyInstaller specification file
   - `create_signed_dmg.sh`: DMG creation with signing support
   - `test_app_build.sh`: Build verification tests

4. **Documentation**
   - `GlobalCoyn_User_Guide.md`: User documentation
   - `GlobalCoyn_Developer_Guide.md`: Developer documentation

## Prerequisites

- macOS 10.14+ (Mojave or newer)
- Python 3.8+
- Homebrew (for installing dependencies)
- Xcode Command Line Tools (for code signing)
- Apple Developer ID (for code signing and notarization)

## Installation

To install the built application:

1. Mount the DMG file (`dist/GlobalCoyn-[version].dmg`)
2. Drag the GlobalCoyn app to the Applications folder
3. Launch from Applications

## Developer Information

For detailed information on the app architecture, customization options, and development workflow, see `GlobalCoyn_Developer_Guide.md`.

## Troubleshooting

If you encounter issues with the build process:

1. Check the logs in the `test_output/` directory
2. Verify that all required dependencies are installed
3. Make sure all scripts are executable
4. If code signing fails, verify your Developer ID

For app-specific issues, refer to `GlobalCoyn_User_Guide.md` and check the logs at `~/Library/Logs/GlobalCoyn/`.

## License

See the LICENSE file for details.

## Contact

For support, visit globalcoyn.com or contact the developer team.