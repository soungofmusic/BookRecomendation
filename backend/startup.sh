# startup.sh
#!/bin/bash
# Force install typing_extensions FIRST to override Azure system version
# Use --no-cache-dir and --ignore-installed to ensure fresh install
pip install --no-cache-dir --ignore-installed --upgrade typing_extensions==4.9.0

# CRITICAL: Override PYTHONPATH to remove /agents/python so our typing_extensions is used
# Azure sets PYTHONPATH with /agents/python first, which breaks imports
export PYTHONPATH=$(echo $PYTHONPATH | tr ':' '\n' | grep -v '/agents/python' | tr '\n' ':' | sed 's/:$//')

# Verify it worked with corrected PYTHONPATH
python -c "
import sys
import os
# Remove /agents/python from sys.path
sys.path = [p for p in sys.path if '/agents/python' not in str(p)]
from typing_extensions import Sentinel
print('typing_extensions Sentinel import successful')
print('PYTHONPATH:', os.environ.get('PYTHONPATH', 'not set'))
"

# Install additional dependencies
pip install numpy==1.24.3 pandas==1.5.3 gunicorn==20.1.0
# Run Gunicorn with configuration
gunicorn --bind=0.0.0.0:$PORT \
         --timeout 1200 \
         --workers 4 \
         --threads 2 \
         --worker-class gthread \
         --max-requests 1000 \
         --max-requests-jitter 50 \
         --log-level info \
         app:app
