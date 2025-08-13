# KortekStream

Streaming platform untuk berbagai kategori konten.

## Instruksi Deployment Docker

### Prasyarat

- Docker dan Docker Compose terinstal di server Anda
- Port 9000 sudah dibuka di firewall server Anda (atau port lain jika Anda mengubahnya)

### Deployment Lokal

1. Clone repository:
   ```
   git clone <repository-url> /path/to/kortekstream
   cd /path/to/kortekstream
   ```

2. Jalankan script deployment lokal:
   ```
   chmod +x deploy-local.sh
   ./deploy-local.sh
   ```
   
   Script ini akan:
   - Menghentikan container yang mungkin sedang berjalan
   - Membangun dan menjalankan container
   - Menjalankan migrasi database
   - Mengumpulkan file statis

3. Akses aplikasi di browser:
   ```
   http://localhost:9000
   ```

### Deployment Produksi

1. Salin file `.env.prod` ke `.env` dan sesuaikan konfigurasi:
   ```
   cp .env.prod .env
   nano .env  # Edit sesuai kebutuhan
   ```

2. Jalankan script deployment produksi:
   ```
   chmod +x deploy-prod.sh
   ./deploy-prod.sh
   ```

3. Akses aplikasi di browser:
   ```
   http://yourdomain.com:9000
   ```

### Konfigurasi Zero Trust

Karena Anda menggunakan Zero Trust, Anda tidak memerlukan SSL di level aplikasi. Konfigurasi yang sudah dibuat:

- Nginx berjalan di port 9000 (non-standar)
- Redis berjalan di port 6380 (non-standar)
- SSL dinonaktifkan di konfigurasi Nginx
- Semua header keamanan tetap diaktifkan

Untuk mengintegrasikan dengan Zero Trust:

1. Konfigurasikan tunnel di dashboard Zero Trust Anda
2. Arahkan tunnel ke port 9000 di server Anda
3. Konfigurasikan DNS untuk mengarahkan domain Anda ke tunnel

### Struktur Docker

Deployment menggunakan beberapa container:

- **web**: Aplikasi Django dengan Gunicorn
- **db**: Database PostgreSQL
- **redis**: Cache Redis (port 6380)
- **nginx**: Server web Nginx (port 9000)

### Perintah Berguna

- Untuk melihat log:
  ```
  # Log semua container
  docker compose -f docker-compose.prod.yml logs -f
  
  # Log container tertentu
  docker compose -f docker-compose.prod.yml logs -f web
  ```

- Untuk menghentikan aplikasi:
  ```
  docker compose -f docker-compose.prod.yml down
  ```

- Untuk memulai ulang aplikasi:
  ```
  docker compose -f docker-compose.prod.yml up -d
  ```

- Untuk memperbarui aplikasi setelah perubahan kode:
  ```
  git pull
  docker compose -f docker-compose.prod.yml build web
  docker compose -f docker-compose.prod.yml up -d
  ```

- Untuk backup database:
  ```
  docker compose -f docker-compose.prod.yml exec db pg_dump -U postgres kortekstream > backup.sql
  ```

- Untuk memeriksa status kesehatan aplikasi:
  ```
  curl http://localhost:9000/health/
  ```

## Fitur

- Breadcrumb dinamis yang mendukung berbagai kategori konten
- Desain responsif
- Sistem caching lanjutan
- Pola circuit breaker untuk ketahanan API
- Optimasi SEO
- Deployment berbasis Docker

## Struktur Proyek

- `/templates`: Template HTML
- `/static`: File statis (CSS, JS, gambar)
- `/stream`: Aplikasi Django utama
- `/mysite`: Konfigurasi proyek Django
- `docker-compose.yml`: Konfigurasi Docker Compose untuk lingkungan lokal
- `docker-compose.prod.yml`: Konfigurasi Docker Compose untuk produksi
- `.env`: Konfigurasi lingkungan untuk produksi
- `.env.local`: Konfigurasi lingkungan untuk pengembangan lokal