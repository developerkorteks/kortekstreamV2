#!/bin/bash

# Script untuk memperbaiki konfigurasi database langsung di dalam container
# Pastikan script ini dijalankan dari direktori proyek
cd "$(dirname "$0")"

echo "Membuat file perbaikan sementara..."
cat > fix_db_config.py << 'EOF'
#!/usr/bin/env python3
import re

# Baca file settings.py
with open('/app/mysite/settings.py', 'r') as f:
    content = f.read()

# Ganti konfigurasi database yang bermasalah
pattern = r"'OPTIONS': \{\s*'MAX_CONNS': \d+,\s*'MIN_CONNS': \d+,\s*\}"
replacement = "'OPTIONS': {\n                # PostgreSQL specific options\n                'connect_timeout': 10,\n            }"
new_content = re.sub(pattern, replacement, content)

# Tulis kembali file settings.py
with open('/app/mysite/settings.py', 'w') as f:
    f.write(new_content)

print("Konfigurasi database berhasil diperbaiki!")
EOF

echo "Menyalin file perbaikan ke container..."
docker cp fix_db_config.py kortekstreamv2-web-1:/app/

echo "Menjalankan script perbaikan di dalam container..."
docker exec kortekstreamv2-web-1 python /app/fix_db_config.py

echo "Menghapus file perbaikan sementara..."
rm fix_db_config.py
docker exec kortekstreamv2-web-1 rm /app/fix_db_config.py

echo "Me-restart container web..."
docker-compose restart web

echo "Menunggu container siap..."
sleep 10

echo "Menjalankan migrasi database..."
docker-compose exec web python manage.py migrate

echo "Mengumpulkan file statis..."
docker-compose exec web python manage.py collectstatic --noinput

echo "Proses selesai!"
echo "Jika masih ada masalah, periksa log dengan perintah:"
echo "docker-compose logs web"