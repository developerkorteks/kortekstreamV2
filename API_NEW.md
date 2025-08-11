GET /api/v1/anime-terbaru

Parameter Query
page : Nomor halaman (contoh: 1, 2).
category : Filter konten (pilihan: anime, korean-drama, all).
Contoh URL
http://apigatway.humanmade.my.id:8080/api/v1/anime-terbaru?page=1&category=anime
Struktur Respons
Respons akan berupa objek JSON yang berisi daftar anime.

Contoh:

JSON

{
  "confidence_score": 1,
  "data": [
    {
      "anime_slug": "isekai-mokushiroku-mynoghra",
      "cover": "https://v1.samehadaku.how/...",
      "episode": "6",
      "judul": "Isekai Mokushiroku Mynoghra",
      "rilis": "7 hours yang lalu",
      "uploader": "Azuki",
      "url": "https://v1.samehadaku.how/..."
    }
  ],
  "message": "Data berhasil diambil",
  "sources": ["samehadaku", "gomunime"]
}

GET /api/v1/home

Parameter
Parameter dikirim sebagai query string dalam URL.

Nama	Tipe	Lokasi	Deskripsi
category	string	query	. Filter untuk kategori konten. Nilai yang diterima: anime, korean-drama, all.
Contoh Penggunaan
Berikut adalah contoh cara memanggil API untuk mendapatkan konten halaman utama kategori anime.

URL Lengkap:

http://apigatway.humanmade.my.id:8080/api/v1/home?category=anime
Contoh cURL:

Bash

curl -X 'GET' \
  'http://apigatway.humanmade.my.id:8080/api/v1/home?category=anime' \
  -H 'accept: application/json'
Struktur Respons JSON
Jika permintaan berhasil (kode status 200), API akan mengembalikan objek JSON dengan beberapa bagian data.

Contoh Respons:

JSON

{
  "confidence_score": 1,
  "jadwal_rilis": [
    {
      "Friday": [
        {
          "anime_slug": "dandadan-season-2",
          "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/149001.jpg",
          "genres": ["Action", "Comedy"],
          "release_time": "00:00",
          "score": "8.48",
          "title": "Dandadan Season 2",
          "type": "TV",
          "url": "https://v1.samehadaku.how/anime/dandadan-season-2/"
        }
      ]
    }
  ],
  "movies": [
    {
      "anime_slug": "sidonia-no-kishi-ai-tsumugu-hoshi",
      "cover": "https://v1.samehadaku.how/wp-content/uploads/2025/07/108354.jpg",
      "genres": ["Action", "Sci-Fi"],
      "judul": "Sidonia no Kishi Ai Tsumugu Hoshi",
      "tanggal": "Jun 4, 2021",
      "url": "https://v1.samehadaku.how/anime/sidonia-no-kishi-ai-tsumugu-hoshi/"
    }
  ],
  "new_eps": [
    {
      "anime_slug": "isekai-mokushiroku-mynoghra",
      "cover": "https://v1.samehadaku.how/wp-content/uploads/2025/08/image-2-1.jpg",
      "episode": "6",
      "judul": "Isekai Mokushiroku Mynoghra",
      "rilis": "8 hours yang lalu",
      "url": "https://v1.samehadaku.how/anime/isekai-mokushiroku-mynoghra/"
    }
  ],
  "top10": [
    {
      "anime_slug": "one-piece",
      "cover": "https://v1.samehadaku.how/wp-content/uploads/2020/04/E5RxYkWX0AAwdGH.png.jpg",
      "genres": ["Anime"],
      "judul": "One Piece",
      "rating": "8.73",
      "url": "https://v1.samehadaku.how/anime/one-piece/"
    }
  ],
  "message": "Data berhasil diambil dari multiple sources",
  "sources": ["samehadaku", "winbutv"]
}

GET /api/v1/home

Parameter
Parameter dikirim sebagai query string dalam URL.

Nama	Tipe	Lokasi	Deskripsi
category	string	query	Opsional. Filter untuk kategori konten. Nilai yang diterima: anime, korean-drama, all. Menggunakan all akan mengubah struktur respons.

Ekspor ke Spreadsheet
Contoh Penggunaan (Semua Kategori)
Berikut adalah contoh cara memanggil API untuk mendapatkan konten halaman utama dari semua kategori yang tersedia.

URL Lengkap:

http://apigatway.humanmade.my.id:8080/api/v1/home?category=all
Contoh cURL:

Bash

curl -X 'GET' \
  'http://apigatway.humanmade.my.id:8080/api/v1/home?category=all' \
  -H 'accept: application/json'
Struktur Respons JSON (category=all)
Jika permintaan berhasil, API akan mengembalikan objek JSON dengan data yang terstruktur di dalam data_by_category.

Contoh Respons:

JSON

{
  "categories": [
    "anime"
  ],
  "confidence_score": 1,
  "data_by_category": {
    "anime": {
      "jadwal_rilis": [
        {
          "Monday": [
            {
              "anime_slug": "busamen-gachi-fighter",
              "cover_url": "https://v1.samehadaku.how/...",
              "genres": ["Action", "Adventure"],
              "release_time": "00:00",
              "score": "6.68",
              "title": "Busamen Gachi Fighter",
              "type": "TV",
              "url": "https://v1.samehadaku.how/..."
            }
          ]
        }
      ],
      "movies": [
        {
          "anime_slug": "village-of-the-damned-1960",
          "cover": "https://winbu.tv/wp-content/uploads/2025/08/57064.jpg",
          "genres": ["Action", "Drama", "Thriller"],
          "judul": "Village of the Damned (1960)",
          "tanggal": "8 jam",
          "url": "https://winbu.tv/film/village-of-the-damned-1960/"
        }
      ],
      "new_eps": [
        {
          "anime_slug": "one-piece",
          "cover": "https://winbu.tv/wp-content/uploads/2020/04/E5RxYkWX0AAwdGH.png.jpg",
          "episode": "Episode 1139",
          "judul": "One Piece",
          "rilis": "8 jam",
          "url": "https://winbu.tv/anime/one-piece/"
        }
      ],
      "top10": [
        {
          "anime_slug": "one-piece",
          "cover": "https://winbu.tv/wp-content/uploads/2020/04/E5RxYkWX0AAwdGH.png.jpg",
          "genres": ["Action", "Adventure", "Drama"],
          "judul": "One Piece",
          "rating": "8.71",
          "url": "https://winbu.tv/anime/one-piece/"
        }
      ]
    }
  },
  "message": "Data berhasil diambil dari 1 categories",
  "sources": ["aggregated"]
}

GET /api/v1/jadwal-rilis

Parameter
Parameter dikirim sebagai query string dalam URL.

Nama	Tipe	Lokasi	Deskripsi
category	string	query	. Filter untuk kategori konten. Nilai yang diterima: anime, korean-drama, all.
Contoh Penggunaan
Berikut adalah contoh cara memanggil API untuk mendapatkan jadwal rilis kategori anime.

URL Lengkap:

http://apigatway.humanmade.my.id:8080/api/v1/jadwal-rilis?category=anime
Contoh cURL:

Bash

curl -X 'GET' \
  'http://apigatway.humanmade.my.id:8080/api/v1/jadwal-rilis?category=anime' \
  -H 'accept: application/json'
Struktur Respons JSON
Jika permintaan berhasil (kode status 200), API akan mengembalikan objek JSON dengan struktur berikut.

Contoh Respons:

JSON

{
  "confidence_score": 1,
  "data": {
    "Monday": [
      {
        "anime_slug": "sentai-red-isekai-de-boukensha-ni-naru",
        "cover_url": "https://i0.wp.com/gomunime.co/wp-content/uploads/2025/03/146918.jpg",
        "genres": [
          "Unknown"
        ],
        "release_time": "at 09:11",
        "score": "N/A",
        "title": "Sentai Red Isekai de Boukensha ni Naru",
        "type": "TV",
        "url": "https://gomunime.co/anime/sentai-red-isekai-de-boukensha-ni-naru/"
      }
    ]
  },
  "message": "Data berhasil diambil dari multiple sources",
  "sources": [
    "gomunime",
    "samehadaku",
    "winbutv"
  ]
}


GET /api/v1/jadwal-rilis/{day}

Parameter
Endpoint ini menerima parameter di dalam path URL dan juga sebagai query string.

Nama	Tipe	Lokasi	Deskripsi
day	string	path	Wajib. Hari dalam seminggu. Nilai yang diterima: senin, selasa, rabu, kamis, jumat, sabtu, minggu.
category	string	query	. Filter untuk kategori konten. Nilai yang diterima: anime, korean-drama, all.
Contoh Penggunaan
Berikut adalah contoh cara memanggil API untuk mendapatkan jadwal rilis pada hari Senin untuk kategori anime.

URL Lengkap:

http://apigatway.humanmade.my.id:8080/api/v1/jadwal-rilis/senin?category=anime
Contoh cURL:

Bash

curl -X 'GET' \
  'http://apigatway.humanmade.my.id:8080/api/v1/jadwal-rilis/senin?category=anime' \
  -H 'accept: application/json'
Struktur Respons JSON
Jika permintaan berhasil (kode status 200), API akan mengembalikan objek JSON yang berisi daftar rilis untuk hari tersebut.

Contoh Respons:

JSON

{
  "confidence_score": 1,
  "data": [
    {
      "anime_slug": "busamen-gachi-fighter",
      "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/150515.jpg",
      "genres": [
        "Action",
        "Adventure"
      ],
      "release_time": "00:00",
      "score": "6.68",
      "title": "Busamen Gachi Fighter",
      "type": "TV",
      "url": "https://v1.samehadaku.how/anime/busamen-gachi-fighter/"
    }
  ],
  "message": "Data berhasil diambil dari multiple sources",
  "sources": [
    "samehadaku",
    "gomunime",
    "winbutv"
  ]
}



GET /api/v1/movie

Parameter
Parameter dikirim sebagai query string dalam URL.

Nama	Tipe	Lokasi	Deskripsi
page	integer	query	Opsional. Nomor halaman untuk paginasi. Digunakan untuk mengambil data di halaman selanjutnya. Contoh: 1, 2.
category	string	query	. Filter untuk kategori konten. Nilai untuk parameter ini akan dimuat secara dinamis dari database.
Contoh Penggunaan
Berikut adalah contoh cara memanggil API ini untuk mendapatkan halaman pertama dari daftar film.

URL Lengkap:

http://apigatway.humanmade.my.id:8080/api/v1/movie?page=1&category=anime
Contoh cURL:

Bash

curl -X 'GET' \
  'http://apigatway.humanmade.my.id:8080/api/v1/movie?page=1&category=anime' \
  -H 'accept: application/json'
Struktur Respons JSON
Jika permintaan berhasil (kode status 200), API akan mengembalikan objek JSON yang berisi daftar film.

Contoh Respons:

JSON

{
  "confidence_score": 1,
  "data": [
    {
      "anime_slug": "sidonia-no-kishi-ai-tsumugu-hoshi",
      "cover": "https://v1.samehadaku.how/wp-content/uploads/2025/07/108354.jpg",
      "genres": [
        "Action",
        "Sci-Fi"
      ],
      "judul": "Sidonia no Kishi Ai Tsumugu Hoshi",
      "sinopsis": "Setelah Bumi dihancurkan oleh alien yang disebut dengan Gauna, sisa manusia yang selamat menyelamatkan diri...",
      "skor": "7.45",
      "status": "Completed",
      "tanggal": "N/A",
      "url": "https://v1.samehadaku.how/anime/sidonia-no-kishi-ai-tsumugu-hoshi/",
      "views": "626013 Views"
    }
  ],
  "message": "Data berhasil diambil dari multiple sources",
  "sources": [
    "samehadaku",
    "winbutv",
    "gomunime"
  ]
}

Tentu, berikut adalah dokumentasi lengkap untuk endpoint /api/v1/search dengan semua field dijelaskan secara rinci.

Dokumentasi API: Pencarian
Endpoint ini digunakan untuk mencari anime, film, atau serial berdasarkan kata kunci. Hasil pencarian dikumpulkan dari berbagai sumber data dan mendukung paginasi.

GET /api/v1/search

Parameter
Parameter dikirim sebagai query string dalam URL.

Nama	Tipe	Lokasi	Deskripsi
q	string	query	Wajib. Kata kunci pencarian. Bisa berupa judul, genre, atau kata kunci lainnya.
page	integer	query	Opsional. Nomor halaman untuk paginasi. Contoh: 1, 2.
category	string	query	. Filter untuk kategori konten. Nilai untuk parameter ini akan dimuat secara dinamis dari database.
Contoh Penggunaan
Berikut adalah contoh cara memanggil API untuk mencari judul dengan kata kunci "a" pada halaman pertama.

URL Lengkap:

http://apigatway.humanmade.my.id:8080/api/v1/search?q=a&page=1&category=anime
Contoh cURL:

Bash

curl -X 'GET' \
  'http://apigatway.humanmade.my.id:8080/api/v1/search?q=a&page=1&category=anime' \
  -H 'accept: application/json'
Struktur Respons JSON
Jika permintaan berhasil (kode status 200), API akan mengembalikan objek JSON yang berisi hasil pencarian.

Contoh Respons:

JSON

{
  "confidence_score": 1,
  "data": [
    {
      "anime_slug": "sakamoto-days-cour-2",
      "cover": "https://v1.samehadaku.how/wp-content/uploads/2025/07/bx184237-OJAksU2fsIPx.jpg",
      "genre": [
        "Action",
        "Adult Cast",
        "Comedy",
        "Organized Crime"
      ],
      "judul": "Sakamoto Days Cour 2",
      "penonton": "4794699 Views",
      "sinopsis": "Lanjutan dari Sakamoto Days",
      "skor": "7.9",
      "status": "Ongoing",
      "tipe": "TV",
      "url": "https://v1.samehadaku.how/anime/sakamoto-days-cour-2/"
    }
  ],
  "message": "Data berhasil diambil dari multiple sources",
  "sources": [
    "samehadaku",
    "gomunime",
    "winbutv"
  ]
}


GET /api/categories/names

Parameter
Endpoint ini tidak memerlukan parameter apapun.

Contoh Penggunaan
Berikut adalah contoh cara memanggil API ini.

URL Lengkap:

http://apigatway.humanmade.my.id:8080/api/categories/names
Contoh cURL:

Bash

curl -X 'GET' \
  'http://apigatway.humanmade.my.id:8080/api/categories/names' \
  -H 'accept: application/json'
Struktur Respons JSON
Jika permintaan berhasil (kode status 200), API akan mengembalikan objek JSON dengan struktur sederhana berikut.

Contoh Respons:

JSON

{
  "data": [
    "anime",
    "all"
  ],
  "status": "success"
}


GET /api/v1/anime-detail

Parameter
Parameter dikirim sebagai query string dalam URL.

Nama	Tipe	Lokasi	Deskripsi
id	string	query	Wajib (alternatif). ID unik untuk judul yang dicari.
slug	string	query	Wajib (alternatif). Slug URL untuk judul yang dicari.
anime_slug	string	query	Wajib (alternatif). Slug URL untuk judul yang dicari.
category	string	query	. Filter untuk kategori konten. Nilai yang diterima: anime, korean-drama, all.
Catatan: Salah satu dari parameter id, slug, atau anime_slug wajib disertakan untuk mengidentifikasi judul yang dicari.

Contoh Penggunaan
Berikut adalah contoh cara memanggil API untuk mendapatkan detail dari sebuah judul.

URL Lengkap:

http://apigatway.humanmade.my.id:8080/api/v1/anime-detail?anime_slug=hunting-daze-2024&category=anime
Contoh cURL:

Bash

curl -X 'GET' \
  'http://apigatway.humanmade.my.id:8080/api/v1/anime-detail?anime_slug=hunting-daze-2024&category=anime' \
  -H 'accept: application/json'
Struktur Respons JSON
Jika permintaan berhasil (kode status 200), API akan mengembalikan objek JSON dengan struktur detail berikut.

Contoh Respons:

JSON

{
  "data": {
    "anime_slug": "hunting-daze-2024",
    "confidence_score": 0.95,
    "cover": "https://winbu.tv/wp-content/uploads/2025/08/56898.jpg",
    "details": {
      "Duration": "~120 min",
      "English": "Hunting Daze (2024)",
      "Source": "Original",
      "Status": "Completed"
    },
    "episode_list": [
      {
        "episode": "1",
        "episode_slug": "hunting-daze-2024",
        "release_date": "Unknown",
        "title": "Film",
        "url": "https://winbu.tv/film/hunting-daze-2024/"
      }
    ],
    "genre": ["Mystery"],
    "judul": "Hunting Daze (2024)",
    "penonton": "10,000+ viewers",
    "rating": {
      "score": "5.9",
      "users": "1,234 users"
    },
    "recommendations": [
      {
        "anime_slug": "when-the-light-breaks-2024",
        "cover_url": "https://winbu.tv/wp-content/uploads/2025/08/56760.jpg",
        "title": "When the Light Breaks (2024)",
        "url": "https://winbu.tv/film/when-the-light-breaks-2024/"
      }
    ],
    "sinopsis": "Hunting Daze (2024) Nina, seorang wanita muda yang penuh gejolak...",
    "source": "winbu.tv"
  },
  "_metadata": {
    "source": "winbutv",
    "response_time": "3.312729003s",
    "cache_status": "MISS",
    "timestamp": "2025-08-11T00:53:11Z"
  },
  "success": true
}


GET /api/v1/episode-detail

Parameter
Parameter dikirim sebagai query string dalam URL.

Nama	Tipe	Lokasi	Deskripsi
id	string	query	Wajib (alternatif). ID unik untuk episode yang dicari.
episode_url	string	query	Wajib (alternatif). URL lengkap dari halaman episode.
episode_slug	string	query	Wajib (alternatif). Slug URL dari episode.
category	string	query	. Filter untuk kategori konten. Nilai untuk parameter ini akan dimuat secara dinamis dari database.
Catatan: Salah satu dari parameter id, episode_url, atau episode_slug wajib disertakan untuk mengidentifikasi episode yang dicari.

Contoh Penggunaan
Berikut adalah contoh cara memanggil API untuk mendapatkan detail dari sebuah episode menggunakan episode_slug.

URL Lengkap:

http://apigatway.humanmade.my.id:8080/api/v1/episode-detail?episode_slug=hunting-daze-2024&category=anime
Contoh cURL:

Bash

curl -X 'GET' \
  'http://apigatway.humanmade.my.id:8080/api/v1/episode-detail?episode_slug=hunting-daze-2024&category=anime' \
  -H 'accept: application/json'
Struktur Respons JSON
Jika permintaan berhasil (kode status 200), API akan mengembalikan objek JSON dengan struktur detail berikut.

Contoh Respons:

JSON

{
  "data": {
    "anime_info": {
      "genres": ["Mystery", "Canada"],
      "synopsis": "Hunting Daze (2024) Nina, seorang wanita muda yang penuh gejolak bergabung...",
      "thumbnail_url": "https://winbu.tv/wp-content/uploads/2025/08/56898.jpg",
      "title": "Hunting Daze (2024)"
    },
    "confidence_score": 0.95,
    "download_links": {
      "MP4": {
        "720p": "https://contoh.download/file_720p.mp4"
      }
    },
    "navigation": {},
    "other_episodes": [
      {
        "release_date": "January 2025",
        "thumbnail_url": "https://winbu.tv/wp-content/uploads/2025/08/56898.jpg",
        "title": "Episode 1",
        "url": "https://winbu.tv/film/hunting-daze-2024/"
      }
    ],
    "release_info": "Released on January 2025",
    "streaming_servers": [
      {
        "server_name": "HYDRAX Server",
        "streaming_url": "https://abysscdn.com/?v=aaxeNcVpMe"
      }
    ],
    "title": "Genres"
  },
  "_metadata": {
    "source": "winbutv",
    "response_time": "5.225429625s",
    "cache_status": "MISS",
    "timestamp": "2025-08-11T00:54:47Z"
  },
  "success": true
}

