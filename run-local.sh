#!/bin/bash

echo "Starting local development environment..."

# Create necessary directories
mkdir -p logs
mkdir -p media

# Stop any existing containers
docker-compose down

# Build and start the containers
docker-compose up -d --build

# Wait for services to start
echo "Waiting for services to start..."
sleep 10

# Run migrations
echo "Running migrations..."
docker-compose exec web python manage.py migrate

# Collect static files
echo "Collecting static files..."
docker-compose exec web python manage.py collectstatic --noinput

echo "Local development environment is running!"
echo "You can access the application at http://localhost:9326"
echo ""
echo "To view logs, run: docker-compose logs -f"
echo "To stop the environment, run: docker-compose down"