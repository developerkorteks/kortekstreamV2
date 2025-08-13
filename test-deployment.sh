#!/bin/bash

# Script untuk menguji deployment lokal

echo "Menguji deployment lokal KortekStream..."

# Pastikan docker dan docker-compose terinstall
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker dan/atau Docker Compose tidak terinstall."
    echo "Silakan install terlebih dahulu."
    exit 1
fi

# Pastikan script deploy-local.sh sudah executable
if [ ! -x "deploy-local.sh" ]; then
    echo "Membuat script deploy-local.sh executable..."
    chmod +x deploy-local.sh
fi

# Jalankan deployment lokal
echo "Menjalankan deployment lokal..."
./deploy-local.sh

# Tunggu beberapa saat agar semua container siap
echo "Menunggu semua container siap..."
sleep 10

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
docker compose -f docker-compose.local.yml ps

# Tampilkan log singkat
echo "Log terakhir:"
docker compose -f docker-compose.local.yml logs --tail=20

echo ""
echo "Pengujian selesai. Jika semua tes berhasil, deployment lokal siap digunakan."
echo "Untuk menghentikan aplikasi, jalankan: docker compose -f docker-compose.local.yml down"