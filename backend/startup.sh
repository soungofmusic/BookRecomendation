# startup.sh
#!/bin/bash
# Force install typing_extensions to override Azure system version
pip install --upgrade --force-reinstall typing_extensions==4.9.0
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
