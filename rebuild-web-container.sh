#!/bin/bash

# Script untuk membangun ulang container web
# Pastikan script ini dijalankan dari direktori proyek
cd "$(dirname "$0")"

echo "Menghentikan container web..."
docker-compose stop web

echo "Menghapus container web..."
docker-compose rm -f web

echo "Membangun ulang container web..."
docker-compose build web

echo "Memulai container web..."
docker-compose up -d web

echo "Menunggu container siap..."
sleep 10

echo "Menginstal dependensi yang hilang..."
docker-compose exec web pip install django-htmlmin==0.11.0

echo "Menjalankan migrasi database..."
docker-compose exec web python manage.py migrate

echo "Mengumpulkan file statis..."
docker-compose exec web python manage.py collectstatic --noinput

echo "Proses selesai!"
echo "Jika masih ada masalah, periksa log dengan perintah:"
echo "docker-compose logs web"