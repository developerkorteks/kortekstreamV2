#!/bin/bash

# Script untuk mendapatkan sertifikat SSL menggunakan mode standalone
# Ini berguna jika mode webroot tidak berfungsi dengan baik

# Pastikan script ini dijalankan dari direktori proyek
cd "$(dirname "$0")"

echo "Menghentikan Nginx untuk sementara..."
docker-compose stop nginx

echo "Mendapatkan sertifikat SSL dari Let's Encrypt menggunakan mode standalone..."
docker-compose run --rm certbot certonly --standalone \
    -d kortekstream.online -d www.kortekstream.online \
    --email admin@kortekstream.online \
    --agree-tos --no-eff-email --force-renewal

echo "Memperbarui konfigurasi Nginx dengan sertifikat Let's Encrypt..."
cat > nginx/conf.d/default.conf << 'EOF'
server {
    listen 80;
    server_name kortekstream.online www.kortekstream.online;
    
    # Redirect HTTP to HTTPS
    location / {
        return 301 https://$host:2443$request_uri;
    }
    
    # Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
}

server {
    listen 443 ssl;
    server_name kortekstream.online www.kortekstream.online;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/kortekstream.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kortekstream.online/privkey.pem;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    
    # Logs
    access_log /var/log/nginx/kortekstream.access.log;
    error_log /var/log/nginx/kortekstream.error.log;
    
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

echo "Memulai Nginx kembali..."
docker-compose start nginx

echo "Proses selesai!"
echo "Situs Anda seharusnya tersedia di:"
echo "- https://kortekstream.online:2443 (HTTPS)"
echo "- http://kortekstream.online:2020 (HTTP, akan diarahkan ke HTTPS)"