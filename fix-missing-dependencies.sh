#!/bin/bash

# Script untuk memperbaiki dependensi yang hilang
# Pastikan script ini dijalankan dari direktori proyek
cd "$(dirname "$0")"

echo "Menginstal dependensi yang hilang..."
docker-compose exec web pip install django-htmlmin==0.11.0

echo "Me-restart container web..."
docker-compose restart web

echo "Menunggu container web siap..."
sleep 10

echo "Memeriksa log container web..."
docker-compose logs web

echo "Proses selesai!"
echo "Jika masih ada masalah dengan dependensi, jalankan perintah berikut untuk melihat log secara real-time:"
echo "docker-compose logs -f web"