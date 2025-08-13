#!/bin/bash

# Make script executable
chmod +x run-local-ssl.sh

# Create necessary directories
mkdir -p logs
mkdir -p media
mkdir -p static
mkdir -p staticfiles
mkdir -p nginx/ssl

# Generate self-signed SSL certificate for local testing
if [ ! -f nginx/ssl/localhost.crt ]; then
    echo "Generating self-signed SSL certificate for local testing..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/localhost.key -out nginx/ssl/localhost.crt \
        -subj "/C=ID/ST=Jakarta/L=Jakarta/O=KortekStream/CN=localhost"
fi

# Create local Nginx configuration for SSL
cat > nginx/conf.d/default.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    
    # Redirect HTTP to HTTPS
    location / {
        return 301 https://$host:2443$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name localhost;
    
    # SSL configuration
    ssl_certificate /etc/nginx/ssl/localhost.crt;
    ssl_certificate_key /etc/nginx/ssl/localhost.key;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    
    # Logs
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;
    
    # Static files
    location /static/ {
        alias /app/static/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    location /media/ {
        alias /app/media/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    # Proxy to Django
    location / {
        proxy_pass http://web:9326;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

echo "Starting local development environment with SSL..."

# Use local SSL docker-compose file
cp docker-compose.local-ssl.yml docker-compose.yml

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

echo "Local development environment with SSL is running!"
echo "You can access the application at:"
echo "- https://localhost:2443 (HTTPS)"
echo "- http://localhost:2020 (HTTP, redirects to HTTPS)"
echo ""
echo "Note: Since this is using a self-signed certificate, you will need to accept the security warning in your browser."
echo ""
echo "To view logs, run: docker-compose logs -f"
echo "To stop the environment, run: docker-compose down"