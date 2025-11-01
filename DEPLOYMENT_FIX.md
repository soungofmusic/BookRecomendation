# Fixing Azure Deployment Conflict (409 Error)

## The Problem
You're getting a "Conflict (CODE: 409)" error when deploying. This happens when:
- Another deployment is already in progress
- The App Service is restarting
- The App Service is in a transitional state

## Quick Fixes

### Option 1: Wait and Retry (Simplest)
1. Wait 2-3 minutes
2. Go to GitHub Actions: https://github.com/soungofmusic/BookRecomendation/actions
3. Find the failed workflow
4. Click "Re-run jobs" → "Re-run all jobs"
5. Wait for it to complete

### Option 2: Stop and Restart in Azure Portal
1. Go to Azure Portal: https://portal.azure.com
2. Search for "book-recommender-api"
3. Open your App Service
4. Click **Stop** (top toolbar)
5. Wait 30 seconds
6. Click **Start**
7. Wait 1-2 minutes for it to fully start
8. Retry the deployment from GitHub Actions

### Option 3: Cancel Running Deployments
1. Go to Azure Portal
2. Navigate to your App Service
3. Go to **Deployment Center** (left sidebar)
4. Check for any running deployments
5. Cancel them if found
6. Retry deployment

### Option 4: Check App Service Status
1. Azure Portal → Your App Service
2. Go to **Overview**
3. Check if status shows:
   - "Running" ✅ (ready for deployment)
   - "Stopped" ⏸️ (start it first)
   - "Restarting" ⏳ (wait for it to finish)

## Why This Happens
- Multiple deployments triggered at once
- Previous deployment didn't complete properly
- App Service is in a transitional state (stopping/starting)

## Prevention
The workflow has been updated to:
- Stop the app before deployment
- Wait a few seconds
- Deploy
- Restart the app

This should prevent conflicts in the future.

## If Still Failing
1. Check GitHub Actions logs for more details
2. Try manual deployment via Azure CLI:
   ```bash
   az webapp deployment source config-zip \
     --resource-group <your-resource-group> \
     --name book-recommender-api \
     --src backend/release.zip
   ```

