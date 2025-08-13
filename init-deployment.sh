#!/bin/bash

# Make script executable
chmod +x init-deployment.sh

# Create necessary directories
mkdir -p logs
mkdir -p media
mkdir -p static
mkdir -p staticfiles

echo "Initializing deployment..."

# Start the services
docker-compose up -d

# Wait for services to start
echo "Waiting for services to start..."
sleep 10

# Initialize the database
docker-compose exec web python manage.py migrate

# Create superuser
echo "Creating superuser..."
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

echo "Deployment initialized successfully!"
echo "Your site should be available at http://kortekstream.online:9326"
echo ""
echo "To view logs, run: docker-compose logs -f"
echo "To stop the environment, run: docker-compose down"