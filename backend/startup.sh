#!/bin/bash
# startup.sh - Azure App Service startup script

# Force install typing_extensions to override Azure system version
pip install --no-cache-dir --ignore-installed --upgrade "typing_extensions>=4.10,<5"

# Remove /agents/python from PYTHONPATH (Azure includes it first, breaks imports)
export PYTHONPATH=$(echo $PYTHONPATH | tr ':' '\n' | grep -v '/agents/python' | tr '\n' ':' | sed 's/:$//')

# Find app.py - Oryx may extract to temp directory or /home/site/wwwroot
APP_DIR=""
if [ -f "/home/site/wwwroot/app.py" ]; then
    APP_DIR="/home/site/wwwroot"
elif [ -d "/tmp" ]; then
    # Find temp directory with app.py (Oryx pattern: /tmp/8de...)
    for dir in /tmp/*; do
        if [ -f "$dir/app.py" ]; then
            APP_DIR="$dir"
            break
        fi
    done
fi

# If still not found, try current directory
if [ -z "$APP_DIR" ] && [ -f "app.py" ]; then
    APP_DIR=$(pwd)
fi

# Verify we found app.py
if [ -z "$APP_DIR" ] || [ ! -f "$APP_DIR/app.py" ]; then
    echo "ERROR: app.py not found!"
    echo "Searched in: /home/site/wwwroot, /tmp/*, $(pwd)"
    echo "PYTHONPATH: $PYTHONPATH"
    ls -la /home/site/wwwroot 2>/dev/null || echo "/home/site/wwwroot does not exist"
    exit 1
fi

# Change to app directory
cd "$APP_DIR"
echo "Starting gunicorn from directory: $APP_DIR"
echo "Found app.py: $(ls -la app.py)"

# Ensure app directory is in PYTHONPATH
export PYTHONPATH="$APP_DIR:$PYTHONPATH"

# Run Gunicorn
exec gunicorn --bind=0.0.0.0:$PORT \
              --timeout 1200 \
              --workers 2 \
              --threads 2 \
              --worker-class gthread \
              --log-level info \
              app:app
