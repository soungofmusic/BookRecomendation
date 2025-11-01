# Fix: ModuleNotFoundError: No module named 'app'

## The Problem
Azure auto-detected Flask and generated `gunicorn app:app`, but it can't find the `app.py` file because the working directory is wrong.

## Solution: Set Startup Command in Azure Portal

1. **Azure Portal** → **book-recommender-api** → **Configuration**
2. Go to **General settings** tab
3. Find **Startup Command**
4. Set it to:
   ```bash
   cd /home/site/wwwroot && gunicorn --bind 0.0.0.0:8000 --timeout 1200 --workers 4 --threads 2 --worker-class gthread --max-requests 1000 --max-requests-jitter 50 --log-level info app:app
   ```
   **OR** simpler version:
   ```bash
   cd /home/site/wwwroot && gunicorn --bind 0.0.0.0:8000 app:app
   ```
5. Click **Save**
6. Go to **Overview** → Click **Restart**
7. Wait 2-3 minutes for restart

## Why This Happens
Azure Oryx auto-detects Flask but doesn't always set the correct working directory. By explicitly `cd`ing to `/home/site/wwwroot` (where your files are deployed), gunicorn can find `app.py`.

## Verify It Works
After restart, check **Log stream** for:
- `Starting gunicorn`
- `Listening at: http://0.0.0.0:8000`
- No `ModuleNotFoundError`

Then test:
- `https://book-recommender-api-affpgxcqgah8cvah.westus-01.azurewebsites.net/`
- Should return: "Book Recommendation API is running!"

