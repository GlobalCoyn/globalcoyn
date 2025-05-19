# GlobalCoyn macOS App Testing Guide

This guide provides instructions for testing the GlobalCoyn macOS app on different machines.

## Building the App

1. Run the macOS app builder script:
   ```bash
   ./macos_app_builder.sh
   ```

2. This will create the following in the `dist` directory:
   - `GlobalCoyn.app` - The app bundle
   - `GlobalCoyn-2.0.1.dmg` - The disk image for distribution (if `hdiutil` is available)
   - `GlobalCoyn-2.0.1.zip` - The zip archive (if DMG cannot be created)

## Testing on Other Machines

1. Copy the DMG or ZIP file to the test machine
2. Open the file on the test machine
3. Drag the GlobalCoyn app to the Applications folder
4. Launch the app from Applications

## Expected Behavior

When launched, the app should:

1. Check for Python installation
   - If Python is not installed, it will prompt to install it
   - If prompted, install Python and restart the app

2. Install Required Packages
   - The app will automatically install any missing Python packages

3. Connect to Bootstrap Nodes
   - The app should connect to the bootstrap nodes at 13.61.79.186
   - You should see log messages indicating successful connections

4. Data Location
   - User data will be stored in `~/Documents/GlobalCoyn/`
   - This includes blockchain data, wallet information, and logs

## Troubleshooting

If issues occur during testing, check the log file:
```
~/Documents/GlobalCoyn/globalcoyn.log
```

Common issues and solutions:

1. **"App can't be opened because it is from an unidentified developer"**
   - Right-click (or Control-click) on the app and select "Open"
   - Click "Open" in the dialog box

2. **Missing Python Modules**
   - The app should automatically install required modules
   - If manual installation is needed, run:
     ```
     pip3 install requests psutil flask
     ```

3. **Connectivity Issues**
   - Ensure the test machine has internet connectivity
   - Check firewall settings that might block outgoing connections
   - Verify that ports 8100 and 8101 are not blocked

4. **Wallet Issues**
   - If wallet doesn't load, check the permissions on the data directory
   - Ensure the user has write permissions to `~/Documents/GlobalCoyn/`

## Deployment to Production

After successful testing, deploy the app to the production website:

```bash
./deploy_macos_app.sh 13.61.79.186 ec2-user ~/path/to/globalcoyn.pem
```

## Testing the Website Download

1. Go to the GlobalCoyn website
2. Navigate to the Downloads section
3. Download the macOS app
4. Verify that the download completes successfully
5. Install and run the app following the steps above

## Reporting Issues

For any issues encountered during testing, please document:
1. The macOS version of the test machine
2. The exact steps that led to the issue
3. Any error messages displayed or found in logs
4. Screenshots if applicable