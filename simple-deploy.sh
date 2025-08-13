#!/bin/bash

# Script untuk deployment sederhana tanpa SSL
# Pastikan script ini dijalankan dari direktori proyek
cd "$(dirname "$0")"

echo "=== MEMBERSIHKAN KONFIGURASI LAMA ==="
echo "Menghentikan semua container..."
docker-compose down

echo "Menghapus file konfigurasi lama..."
rm -rf nginx/conf.d/* nginx/nginx.conf certbot

echo "=== MEMBUAT KONFIGURASI BARU ==="
echo "Membuat direktori yang diperlukan..."
mkdir -p nginx/conf.d
mkdir -p static media staticfiles logs

echo "Membuat file .env..."
cat > .env << EOF
DEBUG=False
SECRET_KEY=django-insecure-your-secret-key-here
ALLOWED_HOSTS=128.199.109.211,kortekstream.online,www.kortekstream.online,localhost
CSRF_TRUSTED_ORIGINS=http://128.199.109.211:2020,http://kortekstream.online:2020,http://www.kortekstream.online:2020
DB_NAME=kortekstream
DB_USER=postgres
DB_PASSWORD=KorteksStreamDB2024
DB_HOST=db
DB_PORT=5432
EOF

echo "Membuat docker-compose.yml baru..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  web:
    build: .
    restart: always
    volumes:
      - ./logs:/app/logs
      - ./static:/app/static
      - ./media:/app/media
      - ./staticfiles:/app/staticfiles
    env_file:
      - .env
    expose:
      - "9326"
    depends_on:
      - redis
      - db
    networks:
      - kortekstream_network

  db:
    image: postgres:14
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_DB=${DB_NAME:-kortekstream}
      - POSTGRES_USER=${DB_USER:-postgres}
      - POSTGRES_PASSWORD=${DB_PASSWORD:-KorteksStreamDB2024}
    networks:
      - kortekstream_network

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --port 7453
    volumes:
      - redis_data:/data
    networks:
      - kortekstream_network

  nginx:
    image: nginx:1.23-alpine
    restart: always
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./static:/app/static
      - ./media:/app/media
      - ./staticfiles:/app/staticfiles
    ports:
      - "2020:2020"
    depends_on:
      - web
    networks:
      - kortekstream_network

volumes:
  postgres_data:
  redis_data:

networks:
  kortekstream_network:
    driver: bridge
EOF

echo "Membuat konfigurasi Nginx..."
cat > nginx/conf.d/default.conf << 'EOF'
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

echo "Memperbarui settings.py untuk database..."
cat > fix_settings.py << 'EOF'
#!/usr/bin/env python3
import re

# Baca file settings.py
with open('mysite/settings.py', 'r') as f:
    content = f.read()

# Ganti konfigurasi database yang bermasalah
pattern = r"'OPTIONS': \{\s*'MAX_CONNS': \d+,\s*'MIN_CONNS': \d+,\s*\}"
replacement = "'OPTIONS': {\n                # PostgreSQL specific options\n                'connect_timeout': 10,\n            }"
new_content = re.sub(pattern, replacement, content)

# Tulis kembali file settings.py
with open('mysite/settings.py', 'w') as f:
    f.write(new_content)

print("Konfigurasi database berhasil diperbaiki!")
EOF

chmod +x fix_settings.py
./fix_settings.py

echo "=== MEMULAI DEPLOYMENT ==="
echo "Membangun dan memulai container..."
docker-compose up -d --build

echo "Menunggu container siap..."
sleep 10

echo "Menginstal dependensi yang hilang..."
docker-compose exec web pip install django-htmlmin==0.11.0

echo "Menjalankan migrasi database..."
docker-compose exec web python manage.py migrate

echo "Mengumpulkan file statis..."
docker-compose exec web python manage.py collectstatic --noinput

echo "Status container:"
docker-compose ps

echo "=== DEPLOYMENT SELESAI ==="
echo "Aplikasi seharusnya tersedia di:"
echo "- http://128.199.109.211:2020"

echo ""
echo "Pastikan port 2020 sudah dibuka di firewall:"
echo "sudo ufw allow 2020/tcp"
echo "sudo ufw reload"