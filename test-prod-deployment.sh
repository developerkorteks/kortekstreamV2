#!/bin/bash

# Script untuk menguji deployment produksi secara lokal

echo "Menguji deployment produksi KortekStream secara lokal..."

# Pastikan docker dan docker-compose terinstall
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker dan/atau Docker Compose tidak terinstall."
    echo "Silakan install terlebih dahulu."
    exit 1
fi

# Pastikan file .env.prod ada
if [ ! -f .env.prod ]; then
    echo "Error: File .env.prod tidak ditemukan."
    echo "Silakan buat file .env.prod berdasarkan .env.prod.example"
    exit 1
fi

# Salin .env.prod ke .env untuk pengujian
echo "Menyalin .env.prod ke .env untuk pengujian..."
cp .env.prod .env

# Pastikan script deploy-prod.sh sudah executable
if [ ! -x "deploy-prod.sh" ]; then
    echo "Membuat script deploy-prod.sh executable..."
    chmod +x deploy-prod.sh
fi

# Jalankan deployment produksi
echo "Menjalankan deployment produksi secara lokal..."
./deploy-prod.sh

# Tunggu beberapa saat agar semua container siap
echo "Menunggu semua container siap..."
sleep 15

# Uji koneksi ke aplikasi
echo "Menguji koneksi ke aplikasi..."
if curl -s http://localhost:9000 > /dev/null; then
    echo "✅ Aplikasi berhasil diakses di http://localhost:9000"
else
    echo "❌ Gagal mengakses aplikasi di http://localhost:9000"
fi

# Uji health check
echo "Menguji endpoint health check..."
if curl -s http://localhost:9000/health/ > /dev/null; then
    echo "✅ Health check berhasil diakses"
else
    echo "❌ Gagal mengakses health check"
fi

# Tampilkan status container
echo "Status container:"
docker compose -f docker-compose.prod.yml ps

# Tampilkan log singkat
echo "Log terakhir:"
docker compose -f docker-compose.prod.yml logs --tail=20

echo ""
echo "Pengujian selesai. Jika semua tes berhasil, deployment produksi siap digunakan."
echo "Untuk menghentikan aplikasi, jalankan: docker compose -f docker-compose.prod.yml down"