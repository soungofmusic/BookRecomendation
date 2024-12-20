# Install additional dependencies if not already in requirements.txt
pip install numpy==1.24.3 pandas==1.5.3 gunicorn==20.1.0

# Run Gunicorn on the port provided by Azure
gunicorn --bind=0.0.0.0:$PORT --timeout 600 app:app