#!/bin/bash

# Script untuk menjalankan deployment produksi

echo "Memulai deployment produksi KortekStream..."

# Pastikan docker dan docker-compose terinstall
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker dan/atau Docker Compose tidak terinstall."
    echo "Silakan install terlebih dahulu:"
    echo "  - Docker: https://docs.docker.com/get-docker/"
    echo "  - Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Pastikan file .env.prod ada
if [ ! -f .env.prod ]; then
    echo "Error: File .env.prod tidak ditemukan."
    echo "Silakan buat file .env.prod berdasarkan .env.prod.example"
    exit 1
fi

# Salin .env.prod ke .env
echo "Menyalin .env.prod ke .env..."
cp .env.prod .env

# Hentikan container yang mungkin sedang berjalan
echo "Menghentikan container yang mungkin sedang berjalan..."
docker compose -f docker-compose.prod.yml down

# Build dan jalankan container
echo "Membangun dan menjalankan container..."
docker compose -f docker-compose.prod.yml up -d --build

# Jalankan migrasi database
echo "Menjalankan migrasi database..."
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Kumpulkan file statis
echo "Mengumpulkan file statis..."
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

echo "Deployment produksi selesai!"
echo "Aplikasi dapat diakses di: http://yourdomain.com:9000"
echo ""
echo "Untuk melihat log, jalankan: docker compose -f docker-compose.prod.yml logs -f"
echo "Untuk menghentikan aplikasi, jalankan: docker compose -f docker-compose.prod.yml down"