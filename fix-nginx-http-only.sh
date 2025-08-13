#!/bin/bash

# Script untuk memperbaiki Nginx dengan HTTP saja (tanpa SSL)
# Pastikan script ini dijalankan dari direktori proyek
cd "$(dirname "$0")"

echo "Menghentikan container..."
docker-compose down

echo "Membuat backup docker-compose.yml..."
cp docker-compose.yml docker-compose.yml.bak

echo "Memperbarui port mapping di docker-compose.yml..."
sed -i 's/"2443:443"/"2443:2443"/g' docker-compose.yml
sed -i 's/"2020:80"/"2020:2020"/g' docker-compose.yml

# Hapus volume certbot dari nginx
sed -i '/certbot\/conf:\/etc\/letsencrypt/d' docker-compose.yml
sed -i '/certbot\/www:\/var\/www\/certbot/d' docker-compose.yml

# Hapus service certbot
sed -i '/certbot:/,/kortekstream_network/d' docker-compose.yml

echo "Membuat konfigurasi Nginx baru (HTTP only)..."
mkdir -p nginx/conf.d
cat > nginx/conf.d/default.conf << 'EOF'
# Konfigurasi untuk port 2020 (HTTP)
server {
    listen 2020;
    
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

echo "Membuat konfigurasi Nginx global..."
cat > nginx/nginx.conf << 'EOF'
user  nginx;
worker_processes  auto;

error_log  /var/log/nginx/error.log notice;
pid        /var/run/nginx.pid;

events {
    worker_connections  1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;
    #tcp_nopush     on;

    keepalive_timeout  65;

    #gzip  on;

    include /etc/nginx/conf.d/*.conf;
}
EOF

echo "Memulai container..."
docker-compose up -d

echo "Menunggu container siap..."
sleep 10

echo "Status container:"
docker-compose ps

echo "Memeriksa log Nginx..."
docker-compose logs --tail=20 nginx

echo "Proses selesai!"
echo "Aplikasi seharusnya tersedia di:"
echo "- http://128.199.109.211:2020"

echo ""
echo "Jika masih ada masalah, coba periksa firewall dengan perintah:"
echo "sudo ufw status"
echo "sudo iptables -L -n"