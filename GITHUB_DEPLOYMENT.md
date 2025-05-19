# GitHub Deployment Guide for GlobalCoyn

This document explains how to use the GitHub repository for GlobalCoyn to manage development and deployment to the production AWS EC2 server.

## Overview

The GlobalCoyn blockchain project is now hosted on GitHub, enabling collaborative development and automated deployment. This setup allows you to:

1. Make changes in a controlled environment
2. Review code through pull requests
3. Automatically deploy changes to production
4. Maintain version history and rollback capabilities

## GitHub Repository Structure

The repository mirrors the project structure:

```
/blockchain           - Core blockchain code
  /core               - Blockchain implementation
  /api                - API endpoints
  /clean_bootstrap_nodes - Bootstrap node templates
  /website            - Web interface
/docs                 - Documentation
```

## GitHub Actions Workflows

We've set up several GitHub Actions workflows for different deployment scenarios:

### 1. Update Frontend (`update-frontend.yml`)

This workflow is triggered when changes are made to the website code. It:
- Builds the frontend
- Deploys only the website files to the EC2 server
- Does not affect bootstrap nodes or blockchain data

### 2. Update Core (`update-core.yml`)

This workflow is triggered when changes are made to the core blockchain code. It:
- Creates a package of core updates
- Deploys these updates to the bootstrap nodes
- Does not restart services or affect blockchain data

### 3. Full Deployment (`full-deployment.yml`)

This is a manual workflow triggered through the GitHub Actions UI. It allows you to:
- Choose whether to deploy frontend, core, or both
- Choose whether to restart bootstrap nodes (with caution)
- Perform a complete deployment with service restarts if needed

**CAUTION:** Restarting bootstrap nodes can potentially cause data loss if not done carefully.

## How to Deploy Changes

### For Frontend Changes:

1. Make changes to files in the `blockchain/website` directory
2. Commit and push to GitHub
3. The `update-frontend.yml` workflow will automatically deploy the changes

### For Core Blockchain Changes:

1. Make changes to files in the `blockchain/core` or `blockchain/api` directories
2. Commit and push to GitHub
3. The `update-core.yml` workflow will automatically deploy the changes

### For Complete Deployment:

1. Go to GitHub Actions tab in the repository
2. Select the "Full Deployment" workflow
3. Click "Run workflow"
4. Choose the deployment options:
   - Deploy frontend: Yes/No
   - Deploy core: Yes/No
   - Restart nodes: Yes/No (use with caution)
5. Click "Run workflow"

## Required GitHub Secrets

For the deployment workflows to function, the following secrets must be set up in the GitHub repository:

- `EC2_HOST`: The IP address or hostname of your EC2 server
- `EC2_USERNAME`: The SSH username (usually `ec2-user` for Amazon Linux)
- `DEPLOY_KEY`: The SSH private key that has access to your EC2 server
- `GITHUB_DOWNLOAD_URL`: The base URL for downloading artifacts from GitHub Actions

## Setting Up a New EC2 Server

If you need to set up a completely new EC2 server:

1. Provision an Amazon Linux EC2 instance
2. Set up SSH access for GitHub Actions:
   ```bash
   # Generate an SSH key for deployment
   ssh-keygen -t ed25519 -C "github-deploy-key" -f ~/.ssh/globalcoyn_deploy
   
   # Add public key to EC2 authorized_keys
   cat ~/.ssh/globalcoyn_deploy.pub | ssh ec2-user@your-ec2-server "cat >> ~/.ssh/authorized_keys"
   
   # Add private key as DEPLOY_KEY in GitHub secrets
   cat ~/.ssh/globalcoyn_deploy
   ```

3. Run the full deployment workflow with the "restart nodes" option set to "true"

## Emergency Rollback

If a deployment causes issues:

1. SSH into the EC2 server
2. Navigate to the backups directory:
   ```bash
   cd ~/backups
   ls -la
   ```
   
3. Find the most recent successful backup:
   ```bash
   cd 20250519123456  # Use the appropriate timestamp
   ```
   
4. Restore the necessary files:
   ```bash
   # For frontend rollback
   sudo cp -r website /var/www/globalcoyn/
   
   # For core rollback
   sudo cp -r core/* /var/www/globalcoyn/clean_bootstrap_nodes/node1/core/
   sudo cp -r core/* /var/www/globalcoyn/clean_bootstrap_nodes/node2/core/
   
   # For blockchain data rollback (use with extreme caution)
   sudo cp blockchain_data.json /var/www/globalcoyn/clean_bootstrap_nodes/node1/
   ```

## Best Practices

1. **Test changes locally** before pushing to GitHub
2. Use **feature branches** and **pull requests** for significant changes
3. **Document changes** in commit messages and pull request descriptions
4. **Monitor deployments** in the GitHub Actions tab
5. **Back up blockchain data** regularly using the server's backup mechanism
6. Avoid restarting bootstrap nodes unless absolutely necessary