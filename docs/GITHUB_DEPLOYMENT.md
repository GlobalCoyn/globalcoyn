# GitHub Deployment Guide for GlobalCoyn

This document explains how to use the GitHub repository for GlobalCoyn to manage development and deployment to production servers.

## Overview

The GlobalCoyn blockchain project uses GitHub Actions for automated deployment. This setup allows you to:

1. Make changes in a controlled environment
2. Review code through pull requests
3. Automatically deploy changes to production
4. Maintain version history and rollback capabilities

## GitHub Actions Workflows

We've set up several GitHub Actions workflows for different deployment scenarios:

### 1. Update Frontend (`update-frontend.yml`)

This workflow is triggered when changes are made to the website code. It:
- Builds the frontend
- Deploys only the website files to the server
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

## Required GitHub Secrets

For the deployment workflows to function, the following secrets must be set up in your GitHub repository:

- `EC2_HOST`: The IP address or hostname of your server
- `EC2_USERNAME`: The SSH username (usually `ec2-user` for Amazon Linux)
- `DEPLOY_KEY`: The SSH private key that has access to your server
- `DOWNLOAD_URL`: The base URL for downloading artifacts from GitHub Actions

### Setting Up GitHub Secrets

1. Generate an SSH key for deployment:
   ```bash
   ssh-keygen -t ed25519 -C "github-deploy-key" -f ~/.ssh/globalcoyn_deploy
   ```

2. Add the public key to your server's authorized_keys:
   ```bash
   cat ~/.ssh/globalcoyn_deploy.pub | ssh [your-username]@[your-server] "cat >> ~/.ssh/authorized_keys"
   ```

3. Add the private key as a secret in your GitHub repository:
   - Go to your GitHub repository → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `DEPLOY_KEY`
   - Value: Copy the entire content of `~/.ssh/globalcoyn_deploy`

4. Add the other required secrets:
   - `EC2_HOST`: Your server's IP address or hostname
   - `EC2_USERNAME`: Your SSH username
   - `DOWNLOAD_URL`: URL for downloading artifacts (use a service like nightly.link)

## How to Deploy Changes

### For Frontend Changes:

1. Make changes to files in the `frontend` directory
2. Commit and push to GitHub
3. The `update-frontend.yml` workflow will automatically deploy the changes

### For Core Blockchain Changes:

1. Make changes to files in the `core` or `api` directories
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

## Setting Up a New Server

If you need to set up a completely new server:

1. Provision a server with your preferred cloud provider
2. Set up SSH access as described in the "Setting Up GitHub Secrets" section
3. Install required dependencies:
   ```bash
   # For Amazon Linux
   sudo yum update -y
   sudo yum install -y python39 python39-pip nginx git
   ```
4. Configure Nginx using the template in `node/deploy/globalcoyn.conf`
5. Run the full deployment workflow with the "restart nodes" option set to "true"

## Emergency Rollback

If a deployment causes issues:

1. SSH into the server
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
   sudo cp -r html /var/www/globalcoyn/
   
   # For core rollback
   sudo cp -r core/* /path/to/node/core/
   ```

## Best Practices

1. **Test changes locally** before pushing to GitHub
2. Use **feature branches** and **pull requests** for significant changes
3. **Document changes** in commit messages and pull request descriptions
4. **Monitor deployments** in the GitHub Actions tab
5. **Back up blockchain data** regularly using the server's backup mechanism
6. Avoid restarting bootstrap nodes unless absolutely necessary