#!/bin/bash

# Set default port if not provided
export PORT=${PORT:-10000}

python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Start Gunicorn with explicit port binding
echo "Starting Gunicorn on port $PORT"
gunicorn stroke_response.wsgi:application --bind 0.0.0.0:$PORT --log-level debug
