# KortekStream

Streaming platform untuk berbagai kategori konten.

## Instruksi Deployment

### Prasyarat

- Docker dan Docker Compose terinstal di server VPS Anda
- Domain (kortekstream.online) sudah diarahkan ke alamat IP server VPS Anda
- Port 2443 dan 2020 sudah dibuka di firewall server VPS Anda

### Langkah-langkah Deployment (Siap Pakai)

1. Clone repository ke server VPS Anda:
   ```
   git clone <repository-url> /path/to/kortekstream
   cd /path/to/kortekstream
   ```

2. Jalankan script inisialisasi:
   ```
   ./init-deployment.sh
   ```
   Script ini akan:
   - Membuat direktori yang diperlukan
   - Menjalankan container Docker
   - Menjalankan migrasi database
   - Membuat superuser
   - Mengumpulkan file statis

3. Akses situs Anda di:
   - https://kortekstream.online:2443 (HTTPS)
   - http://kortekstream.online:2020 (HTTP, akan diarahkan ke HTTPS)

### Menggunakan Zero Trust Tunneling

Jika Anda ingin menggunakan Zero Trust untuk tunneling (seperti Cloudflare Zero Trust atau solusi serupa):

1. Konfigurasikan tunnel di dashboard Zero Trust Anda
2. Arahkan tunnel ke port 2443 (HTTPS) dan 2020 (HTTP) di server Anda
3. Konfigurasikan DNS untuk mengarahkan domain Anda ke tunnel

Dengan cara ini, Anda dapat mengakses situs Anda melalui domain tanpa port, sementara di belakang layar, Zero Trust menangani tunneling ke port yang benar.

### Konfigurasi

Semua konfigurasi sudah disiapkan dan siap digunakan:

- File `.env` sudah berisi semua konfigurasi yang diperlukan
- Redis berjalan di port 7453
- Aplikasi berjalan di port 9326
- Database PostgreSQL sudah dikonfigurasi dengan kredensial yang aman
- CSRF dan allowed hosts sudah dikonfigurasi dengan benar

### Perintah Berguna

- Untuk melihat log:
  ```
  docker-compose logs -f
  ```

- Untuk menghentikan aplikasi:
  ```
  docker-compose down
  ```

- Untuk memulai ulang aplikasi:
  ```
  docker-compose up -d
  ```

- Untuk memperbarui aplikasi setelah perubahan kode:
  ```
  git pull
  docker-compose build web
  docker-compose up -d
  ```

- Untuk backup database:
  ```
  docker-compose exec db pg_dump -U postgres kortekstream > backup.sql
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