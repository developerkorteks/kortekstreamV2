#!/bin/bash

# Script untuk memperbaiki konfigurasi Nginx tanpa SSL
# Pastikan script ini dijalankan dari direktori proyek
cd "$(dirname "$0")"

echo "Membuat konfigurasi Nginx tanpa SSL dan tanpa port 80/443..."
cat > nginx/conf.d/default.conf << 'EOF'
# Konfigurasi untuk port 2020 (HTTP)
server {
    listen 2020;
    server_name kortekstream.online www.kortekstream.online;
    
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

echo "Me-restart Nginx..."
docker-compose restart nginx

echo "Menunggu Nginx siap..."
sleep 5

echo "Status container:"
docker-compose ps nginx

echo "Proses selesai!"
echo "Aplikasi seharusnya tersedia di:"
echo "- http://128.199.109.211:2020"

echo ""
echo "CATATAN: Jika masih ada masalah, coba perbarui docker-compose.yml untuk mengubah port mapping:"
echo "docker-compose down"
echo "sed -i 's/\"2443:443\"/\"2443:2443\"/g' docker-compose.yml"
echo "sed -i 's/\"2020:80\"/\"2020:2020\"/g' docker-compose.yml"
echo "docker-compose up -d"