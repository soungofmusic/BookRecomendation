# startup.sh
#!/bin/bash

# Install additional dependencies
pip install numpy==1.24.3 pandas==1.5.3 gunicorn==20.1.0 gevent==23.9.1

# Run Gunicorn with configuration
gunicorn --bind=0.0.0.0:$PORT \
         --timeout 600 \
         --workers 4 \
         --threads 4 \        # Increased from 2 to 4 for better I/O handling
         --worker-class gevent \  # Changed from gthread to gevent for better async handling
         --max-requests 1000 \
         --max-requests-jitter 50 \
         --log-level info \
         --keep-alive 5 \     # Added to handle connection reuse
         --graceful-timeout 300 \  # Added for graceful shutdown
         --capture-output \    # Capture stdout/stderr from workers
         app:app
