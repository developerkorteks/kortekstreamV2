#!/bin/bash

# Script untuk deployment KortekStream

# Pastikan script berhenti jika ada error
set -e

# Warna untuk output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Memulai deployment KortekStream ===${NC}"

# Pastikan file .env ada
if [ ! -f .env ]; then
    echo -e "${RED}File .env tidak ditemukan!${NC}"
    echo -e "${YELLOW}Menyalin dari .env.example...${NC}"
    cp .env.example .env
    echo -e "${RED}Silakan edit file .env dengan konfigurasi yang benar, lalu jalankan script ini lagi.${NC}"
    exit 1
fi

# Pastikan direktori logs ada
echo -e "${YELLOW}Membuat direktori logs jika belum ada...${NC}"
mkdir -p logs

# Build Tailwind CSS
echo -e "${YELLOW}Building Tailwind CSS...${NC}"
cd static
npx tailwindcss -i ./css/input.css -o ./css/output.css --minify
cd ..

# Pastikan ALLOWED_HOSTS dan CSRF_TRUSTED_ORIGINS sudah benar
echo -e "${YELLOW}Memeriksa konfigurasi ALLOWED_HOSTS dan CSRF_TRUSTED_ORIGINS...${NC}"
if ! grep -q "128.199.109.211" .env; then
    echo -e "${RED}IP 128.199.109.211 tidak ditemukan dalam file .env!${NC}"
    echo -e "${YELLOW}Pastikan ALLOWED_HOSTS dan CSRF_TRUSTED_ORIGINS sudah benar.${NC}"
    echo -e "${YELLOW}Contoh:${NC}"
    echo -e "ALLOWED_HOSTS=kortekstream.online,www.kortekstream.online,128.199.109.211,localhost,127.0.0.1"
    echo -e "CSRF_TRUSTED_ORIGINS=https://kortekstream.online,https://www.kortekstream.online,https://128.199.109.211,http://localhost,http://127.0.0.1"
    read -p "Lanjutkan deployment? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Deployment dibatalkan.${NC}"
        exit 1
    fi
fi

# Build dan jalankan container
echo -e "${YELLOW}Building dan menjalankan container Docker...${NC}"
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Tampilkan status container
echo -e "${YELLOW}Status container:${NC}"
docker compose -f docker-compose.prod.yml ps

echo -e "${GREEN}=== Deployment selesai! ===${NC}"
echo -e "${GREEN}Aplikasi sekarang berjalan di port 9111${NC}"
echo -e "${YELLOW}Pastikan port 9111 terbuka di firewall server Anda.${NC}"
echo -e "${YELLOW}Anda dapat mengakses aplikasi di:${NC}"
echo -e "${GREEN}https://kortekstream.online${NC}"
echo -e "${GREEN}https://128.199.109.211:9111${NC}"