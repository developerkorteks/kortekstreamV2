#!/bin/bash

# Script untuk memeriksa status deployment
# Pastikan script ini dijalankan dari direktori proyek
cd "$(dirname "$0")"

echo "=== Status Container ==="
docker-compose ps

echo ""
echo "=== Log Container Web ==="
docker-compose logs --tail=20 web

echo ""
echo "=== Log Container Nginx ==="
docker-compose logs --tail=20 nginx

echo ""
echo "=== Memeriksa Koneksi ke Web ==="
curl -I http://localhost:2020

echo ""
echo "=== Memeriksa Koneksi ke HTTPS ==="
curl -I -k https://localhost:2443

echo ""
echo "=== Memeriksa Sertifikat SSL ==="
docker exec kortekstreamv2-nginx-1 ls -la /etc/letsencrypt/live/kortekstream.online/ 2>/dev/null || echo "Sertifikat belum tersedia"

echo ""
echo "=== Memeriksa Konfigurasi Nginx ==="
docker exec kortekstreamv2-nginx-1 cat /etc/nginx/conf.d/default.conf

echo ""
echo "=== Pemeriksaan Selesai ==="
echo "Jika ada masalah, Anda dapat menjalankan script perbaikan yang sesuai:"
echo "- fix-production-deploy.sh: Untuk perbaikan lengkap deployment"
echo "- fix-certbot-standalone.sh: Untuk mendapatkan sertifikat SSL dengan mode standalone"
echo "- fix-missing-dependencies.sh: Untuk menginstal dependensi yang hilang"
echo "- fix-database-inside-container.sh: Untuk memperbaiki konfigurasi database"