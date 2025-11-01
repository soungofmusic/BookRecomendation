# Fix Deployment 409 Conflict Error

## Immediate Solution

### Step 1: Cancel Any Running Deployments
1. Go to **Azure Portal**: https://portal.azure.com
2. Search for **"book-recommender-api"**
3. Open your App Service
4. Go to **Deployment Center** (left sidebar)
5. Check for any **in-progress** deployments
6. Cancel them if found

### Step 2: Ensure App Service is Running
1. In Azure Portal → Your App Service
2. Go to **Overview**
3. If status is **"Stopped"**, click **Start**
4. Wait until status shows **"Running"** (green)

### Step 3: Wait 2 Minutes
- Give Azure time to clear any locks or conflicts

### Step 4: Retry Deployment
1. Go to **GitHub**: https://github.com/soungofmusic/BookRecomendation
2. Go to **Actions** tab
3. Find the failed workflow run
4. Click **"Re-run jobs"** → **"Re-run all jobs"**

## Alternative: Manual Fix via Azure CLI

If you have Azure CLI installed:

```bash
# Login
az login

# Find your resource group
az webapp list --query "[?name=='book-recommender-api'].{name:name, resourceGroup:resourceGroup}" --output table

# Stop the app
az webapp stop --name book-recommender-api --resource-group <YOUR_RESOURCE_GROUP>

# Wait a moment
timeout /t 30

# Start the app
az webapp start --name book-recommender-api --resource-group <YOUR_RESOURCE_GROUP>

# Wait for it to be ready
timeout /t 60

# Then retry GitHub Actions deployment
```

## Why This Happens

The 409 conflict error occurs when:
- ✅ Another deployment is running (most common)
- ✅ App Service is restarting
- ✅ App Service has deployment locks
- ✅ Previous deployment didn't complete cleanly

## Prevention

The workflow has been updated to handle this better. Future deployments should avoid this issue.

## Still Having Issues?

1. **Check App Service Logs**:
   - Azure Portal → Your App → **Log stream**
   - Look for deployment errors

2. **Check Deployment History**:
   - Azure Portal → Your App → **Deployment Center** → **Logs**
   - Review recent deployment attempts

3. **Restart App Service**:
   - Azure Portal → Your App → **Overview** → **Restart**
   - Wait 2 minutes, then retry deployment

