# Fix 404 Error: Route Not Found

## The Problem
Your Flask app returns 404 for `/api/recommend`, which means Azure can't find your `app.py` file or the route isn't being registered.

## Quick Checks

### 1. Verify App is Deployed
- Azure Portal → **book-recommender-api** → **Overview**
- Check **Status** is "Running"
- Check **Deployment Center** → Recent deployments show success

### 2. Check Azure Path Mapping
Azure might be looking for files in the wrong location:

1. Azure Portal → **book-recommender-api** → **Configuration**
2. Go to **Path mappings** (or **General settings** → **Path mappings**)
3. Verify:
   - **Virtual path**: `/`
   - **Physical path**: `/home/site/wwwroot` (default)
4. If different, adjust or restore to default

### 3. Verify Startup Command
1. Azure Portal → **book-recommender-api** → **Configuration**
2. Go to **General settings** tab
3. Check **Startup Command**:
   - Should be **empty** (let Azure auto-detect)
   - OR set to: `gunicorn --bind 0.0.0.0:8000 app:app`
4. Click **Save**
5. **Restart** the app

### 4. Test Root Endpoint
Test if the app is running at all:
```bash
https://book-recommender-api-affpgxcqgah8cvah.westus-01.azurewebsites.net/
```

Should return: "Book Recommendation API is running!"

### 5. Check Log Stream
1. Azure Portal → **book-recommender-api** → **Log stream**
2. Look for:
   - "✓ Successfully pre-loaded typing_extensions"
   - "Starting gunicorn"
   - "Listening at: http://0.0.0.0:8000"
   - Any error messages

### 6. Verify File Structure
The deployment workflow zips `backend/` and unzips to root. Azure expects:
- `/home/site/wwwroot/app.py` (the Flask app)
- `/home/site/wwwroot/requirements.txt`

If files are nested incorrectly, Azure won't find them.

## Manual Fix: Re-deploy

If nothing works, trigger a fresh deployment:
1. GitHub → Your repo → **Actions** tab
2. Find the latest "Build and deploy Python app" workflow
3. Click **Run workflow** → **Run workflow** again
4. Wait for deployment to complete
5. Test again

