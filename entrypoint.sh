#!/bin/bash

# Wait for database to be available
echo "Waiting for database..."
while ! timeout 1 bash -c "echo > /dev/tcp/db/5432" 2>/dev/null; do
  echo "Waiting for database connection..."
  sleep 2
done
echo "Database is available"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if needed
echo "Creating superuser if needed..."
python manage.py shell -c "
from django.contrib.auth.models import User
import os
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        'admin', 
        'admin@example.com', 
        os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
    )
    print('Superuser created')
else:
    print('Superuser already exists')
" || true

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:9111 \
    --workers 3 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keep-alive 5 \
    --access-logfile /app/logs/gunicorn_access.log \
    --error-logfile /app/logs/gunicorn_error.log \
    --log-level info \
    mysite.wsgi:application