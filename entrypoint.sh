#!/bin/bash

# Tunggu database siap
echo "Menunggu database..."
while ! nc -z db 5432; do
  sleep 0.5
done
echo "Database siap!"

# Tunggu Redis siap
echo "Menunggu Redis..."
while ! nc -z redis 7453; do
  sleep 0.5
done
echo "Redis siap!"

# Jalankan migrasi database
echo "Menjalankan migrasi database..."
python manage.py migrate

# Buat direktori statis jika belum ada
mkdir -p /app/staticfiles /app/media

# Kumpulkan file statis
echo "Mengumpulkan file statis..."
python manage.py collectstatic --noinput --clear

# Jalankan perintah yang diberikan
exec "$@"