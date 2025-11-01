# Final Fix: Azure is Overwriting startup.sh

## The Problem

Azure's **Oryx build system** is auto-generating `/opt/startup/startup.sh` and **overwriting** our custom startup.sh. The logs show:

```
Writing output script to '/opt/startup/startup.sh'
Updated PYTHONPATH to '/agents/python:...'
```

This means:
- ❌ Our `startup.sh` is being ignored
- ❌ Azure sets PYTHONPATH with `/agents/python` FIRST
- ❌ Our path fixes in `app.py` run too late (after PYTHONPATH is set)

## Solutions

### Solution 1: Set PYTHONPATH as Azure Application Setting (RECOMMENDED)

1. **Azure Portal** → Your App → **Configuration**
2. Go to **Application settings** tab
3. Click **+ New application setting**
4. Add:
   - **Name**: `PYTHONPATH`
   - **Value**: `/tmp/8de19215a4ab5f9/antenv/lib/python3.12/site-packages` 
     (This is the site-packages path - Azure uses temp directories)
   - OR leave it **empty** to unset it
5. Click **Save**
6. **Restart** the app

### Solution 2: Override Startup Command in Azure Portal

1. **Azure Portal** → Your App → **Configuration**
2. Go to **General settings** tab
3. Find **Startup Command**
4. Set it to:
   ```bash
   export PYTHONPATH=/tmp/8de19215a4ab5f9/antenv/lib/python3.12/site-packages && gunicorn --bind 0.0.0.0:$PORT app:app
   ```
   **OR** use a script that removes /agents/python:
   ```bash
   export PYTHONPATH=$(echo $PYTHONPATH | tr ':' '\n' | grep -v '/agents/python' | tr '\n' ':' | sed 's/:$//') && gunicorn --bind 0.0.0.0:$PORT app:app
   ```
5. Click **Save**
6. **Restart** the app

### Solution 3: Use App Service Configuration File

We can create a configuration file that Azure respects, but the easiest is Solution 1 or 2 above.

## Why This Happens

Azure App Service uses **Oryx** build system which:
- Auto-detects Flask apps
- Generates its own startup script
- Sets PYTHONPATH automatically
- This happens AFTER deployment, so it overwrites our startup.sh

## Quick Test

After applying Solution 1 or 2:
1. Check Log stream
2. You should see: "✓ Successfully pre-loaded typing_extensions with Sentinel"
3. Backend should start without errors

## Recommended: Solution 1

Setting PYTHONPATH as an application setting is cleanest because:
- ✅ Persists across deployments
- ✅ Can't be overwritten by Oryx
- ✅ Applied before Python starts

