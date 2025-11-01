# Fix 404 Error: Azure Not Starting Flask App

## The Problem
Azure deployed your files successfully, but the Flask app isn't starting, causing 404 errors.

## Solution: Set Startup Command in Azure Portal

Azure Oryx auto-detects Flask apps, but sometimes needs explicit configuration.

### Step 1: Set Startup Command
1. **Azure Portal** → **book-recommender-api** → **Configuration**
2. Go to **General settings** tab
3. Find **Startup Command**
4. Set it to:
   ```bash
   gunicorn --bind 0.0.0.0:8000 --timeout 1200 --workers 4 --threads 2 --worker-class gthread --max-requests 1000 --max-requests-jitter 50 --log-level info app:app
   ```
5. Click **Save**
6. **Restart** the app (Overview → Restart)

### Step 2: Verify App Starts
1. After restart, go to **Log stream**
2. Look for:
   - `Starting gunicorn`
   - `Listening at: http://0.0.0.0:8000`
   - `Booting worker`
3. If you see errors, check them in the logs

### Step 3: Test
- Test root: `https://book-recommender-api-affpgxcqgah8cvah.westus-01.azurewebsites.net/`
- Should return: "Book Recommendation API is running!"
- Test API: `https://book-recommender-api-affpgxcqgah8cvah.westus-01.azurewebsites.net/api/recommend`

## Alternative: Let Azure Auto-Detect (Simpler)
1. **Azure Portal** → **book-recommender-api** → **Configuration**
2. **General settings** → **Startup Command**
3. **Clear the field** (make it empty)
4. Click **Save**
5. **Restart** the app

Azure will auto-detect Flask and run `gunicorn app:app` automatically.

## Why This Happens
Azure Oryx builds your app but sometimes doesn't auto-generate the startup command correctly. Setting it explicitly ensures gunicorn starts with the right configuration.

