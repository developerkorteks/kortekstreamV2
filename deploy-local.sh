#!/bin/bash

# Script untuk menjalankan deployment lokal

echo "Memulai deployment lokal KortekStream..."

# Pastikan docker dan docker-compose terinstall
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker dan/atau Docker Compose tidak terinstall."
    echo "Silakan install terlebih dahulu:"
    echo "  - Docker: https://docs.docker.com/get-docker/"
    echo "  - Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Hentikan container yang mungkin sedang berjalan
echo "Menghentikan container yang mungkin sedang berjalan..."
docker compose -f docker-compose.local.yml down

# Build dan jalankan container
echo "Membangun dan menjalankan container..."
docker compose -f docker-compose.local.yml up -d --build

# Jalankan migrasi database
echo "Menjalankan migrasi database..."
docker compose -f docker-compose.local.yml exec web python manage.py migrate

# Kumpulkan file statis
echo "Mengumpulkan file statis..."
docker compose -f docker-compose.local.yml exec web python manage.py collectstatic --noinput

echo "Deployment lokal selesai!"
echo "Aplikasi dapat diakses di: http://localhost:9000"
echo ""
echo "Untuk melihat log, jalankan: docker compose -f docker-compose.local.yml logs -f"
echo "Untuk menghentikan aplikasi, jalankan: docker compose -f docker-compose.local.yml down"