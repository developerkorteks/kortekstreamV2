#!/bin/bash

# Script untuk memeriksa konfigurasi firewall
# Pastikan script ini dijalankan dari direktori proyek
cd "$(dirname "$0")"

echo "=== Status UFW ==="
sudo ufw status

echo ""
echo "=== Aturan iptables ==="
sudo iptables -L -n

echo ""
echo "=== Port yang Terbuka ==="
sudo netstat -tulpn | grep LISTEN

echo ""
echo "=== Memeriksa Koneksi ke Port 2020 ==="
nc -zv localhost 2020

echo ""
echo "=== Memeriksa Koneksi ke Container Nginx ==="
docker exec kortekstreamv2-nginx-1 curl -I http://localhost:2020 || echo "Gagal terhubung ke Nginx"

echo ""
echo "=== Memeriksa Koneksi ke Container Web ==="
docker exec kortekstreamv2-web-1 curl -I http://localhost:9326 || echo "Gagal terhubung ke Web"

echo ""
echo "=== Pemeriksaan Selesai ==="
echo "Jika port 2020 tidak terbuka, jalankan perintah berikut:"
echo "sudo ufw allow 2020/tcp"
echo "sudo ufw reload"