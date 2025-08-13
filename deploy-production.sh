#!/bin/bash

# Make script executable
chmod +x deploy-production.sh

# Create necessary directories
mkdir -p logs
mkdir -p media
mkdir -p static
mkdir -p staticfiles
mkdir -p certbot/conf
mkdir -p certbot/www

echo "Starting production deployment..."

# Use production docker-compose file
cp docker-compose.prod.yml docker-compose.yml

# Start Nginx and Certbot for SSL setup
echo "Starting Nginx for SSL setup..."
docker-compose up -d nginx certbot

# Get SSL certificate
echo "Obtaining SSL certificate..."
docker-compose run --rm certbot certonly --webroot -w /var/www/certbot \
    -d kortekstream.online -d www.kortekstream.online \
    --email admin@kortekstream.online --agree-tos --no-eff-email

# Copy production Nginx configuration
echo "Configuring Nginx for production..."
cp nginx/conf.d/production.conf nginx/conf.d/default.conf

# Start all services
echo "Starting all services..."
docker-compose up -d --build

# Wait for services to start
echo "Waiting for services to start..."
sleep 10

# Initialize the database
docker-compose exec web python manage.py migrate

# Create superuser
echo "Creating superuser..."
docker-compose exec -it web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

echo "Production deployment completed successfully!"
echo "Your site should be available at:"
echo "- https://kortekstream.online:2443 (HTTPS)"
echo "- http://kortekstream.online:2020 (redirects to HTTPS)"
echo ""
echo "To view logs, run: docker-compose logs -f"
echo "To stop the environment, run: docker-compose down"