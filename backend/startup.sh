S
# startup.sh
#!/bin/bash
# Install additional dependencies
pip install numpy==1.24.3 pandas==1.5.3 gunicorn==20.1.0
# Run Gunicorn with configuration
gunicorn --bind=0.0.0.0:$PORT \
         --timeout 600 \
         --workers 4 \
         --threads 2 \
         --worker-class gthread \
         --max-requests 1000 \
         --max-requests-jitter 50 \
         --log-level info \
         app:app
