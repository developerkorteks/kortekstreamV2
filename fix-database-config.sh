#!/bin/bash

# Script untuk memperbaiki konfigurasi database
# Pastikan script ini dijalankan dari direktori proyek
cd "$(dirname "$0")"

echo "Menghentikan container..."
docker-compose down

echo "Membuat backup file settings.py..."
cp mysite/settings.py mysite/settings.py.bak

echo "Memperbaiki konfigurasi database di settings.py..."
sed -i 's/MAX_CONNS.*$/connect_timeout\": 10,/' mysite/settings.py
sed -i '/MIN_CONNS/d' mysite/settings.py

echo "Memulai container..."
docker-compose up -d

echo "Menunggu container siap..."
sleep 10

echo "Menjalankan migrasi database..."
docker-compose exec web python manage.py migrate

echo "Mengumpulkan file statis..."
docker-compose exec web python manage.py collectstatic --noinput

echo "Proses selesai!"
echo "Jika masih ada masalah, periksa log dengan perintah:"
echo "docker-compose logs web"