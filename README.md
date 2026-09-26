# 🎬 Multi-Content Studio Uploader

Aplikasi bot dan dashboard visual untuk mengelola dan mengunggah konten media sosial (**TikTok, Instagram, dan Facebook**) secara otomatis dalam satu tempat. 

Tidak perlu lagi login bolak-balik atau upload manual satu per satu di tiap platform. Cukup siapkan konten di dashboard, atur caption atau jadwalnya, dan biarkan bot yang bekerja!

---

## ✨ Apa Saja yang Bisa Dilakukan?

- 🚀 **1-Klik Upload ke 3 Platform Sekaligus**  
  Konten Anda otomatis diunggah berurutan ke **TikTok Studio**, **Instagram (Reels / Feed)**, dan **Facebook Fanspage (Reels / Foto)**.

- ⏰ **Upload Massal & Penjadwalan Otomatis dengan Jeda Waktu**  
  Punya banyak video untuk tayang hari ini? Cukup atur jam mulai pertama kali dan tentukan jeda waktunya (misalnya tiap 30 menit atau 1 jam sekali). Antrean berikutnya akan dijadwalkan otomatis dan diposting sendiri di latar belakang via auto-scheduler.

- 🛒 **Dukungan Keranjang Kuning (TikTok Shop)**  
  Tinggal aktifkan switch keranjang kuning, cari nama produk dari tokomu, pilih produk yang cocok, dan beri nama label keranjang kuning yang pas untuk videomu. Bot akan otomatis menautkannya saat upload!

- ✍️ **Bikin Caption Otomatis Pakai AI**  
  Bingung mau nulis caption apa? Ada tombol **AI Caption** yang bisa menganalisis isi video atau gambarmu dan membuatkan caption yang pas beserta hashtag yang relevan (maksimal 4 hashtag agar tetap rapi).

- 🔗 **Ambil Link Postingan Otomatis (Siap Kirim ke WhatsApp)**  
  Setelah konten berhasil diposting, bot bisa langsung mencari dan mengambil link publik video di TikTok, Instagram, dan Facebook. Formatnya sudah dirapikan, tinggal sekali klik tombol **Salin Semua Format** untuk dikirim ke chat WhatsApp atau laporan klien.

- 🔀 **Atur Urutan Antrean dengan Mudah**  
  Urutan postingan bisa diubah sesuka hati. Cukup seret (drag-and-drop) kartu media di antrean atau pakai tombol panah naik/turun.

- 👥 **Multi-Akun Mandiri & Terisolasi**  
  Bisa mengelola banyak akun atau brand sekaligus. Setiap akun punya sesi login, profil, dan riwayat postingannya sendiri tanpa risiko tertukar.

---

## 📂 Cara Menata Folder Konten

Cukup masukkan file media Anda ke dalam folder `content/` dengan struktur seperti berikut:

```
content/
├── Nama Akun 1/                            <-- Folder Akun 1 (contoh: Brand A)
│   ├── Video/                              <-- Kategori Video (Reels / TikTok)
│   │   └── 2026-08-20/                     <-- Folder Tanggal (YYYY-MM-DD)
│   │       ├── video-2026-08-20-01.mp4     <-- File video
│   │       └── video-2026-08-20-01.json    <-- Metadata caption & settingan
│   ├── Poster/                             <-- Kategori Foto / Gambar Tunggal
│   │   └── 2026-08-20/
│   │       └── poster-2026-08-20-01.jpeg
│   └── Carousel/                           <-- Kategori Carousel (Multi-Slide)
│       └── 2026-08-20/
│           └── carousel-2026-08-20-01/
│               ├── slide 1.jpg
│               └── slide 2.jpg
│
└── Nama Akun 2/                            <-- Folder Akun 2 (contoh: Brand B)
    ├── Video/
    ├── Poster/
    └── Carousel/
```

> **Tips:** Penamaan file seperti `video-YYYY-MM-DD-01.mp4` juga akan otomatis dibuatkan secara rapi jika Anda menambahkan media langsung lewat tombol **`+ Tambah Media`** di dashboard.

---

## 🚀 Cara Menjalankan

### 1. Persiapan Awal (Hanya Sekali di Awal)
Pastikan di komputermu sudah terpasang **Python** (versi 3.10+) dan **Node.js**.

1. Buka terminal di folder proyek ini, lalu pasang dependensi:
   ```powershell
   pip install -r requirements.txt
   playwright install chromium
   ```
2. Build antarmuka web dashboard:
   ```powershell
   cd frontend
   npm install
   npm run build
   cd ..
   ```
3. *(Opsional)* Jika ingin memakai fitur AI Caption, salin file `.env.example` menjadi `.env` lalu masukkan API Key AI yang Anda miliki.

---

### 2. Buka Dashboard Studio
Cara paling mudah, cukup klik dua kali file:
```powershell
start_ui.bat
```
Atau bisa juga lewat terminal:
```powershell
python -m src.server
```

Setelah aplikasi berjalan, buka browser di alamat:  
👉 **`http://127.0.0.1:8000`**

---

## 💡 Tips & Panduan Pemakaian Singkat

1. **Login Akun Media Sosial Pertama Kali:**  
   Buka dashboard, klik tombol akun di kanan atas, pilih **Kelola Akun**, lalu klik tombol **Hubungkan** pada platform yang diinginkan (TikTok, Instagram, atau Facebook). Jendela browser akan terbuka untuk login seperti biasa. Setelah selesai, status akun akan otomatis tersambung.

2. **Menyiapkan Konten:**  
   Pilih akun yang ingin dikelola. Klik **`+ Tambah Media`** untuk menambahkan video, poster, atau slide carousel. Di panel kanan (Studio Inspector), kamu bisa mengatur caption, memilih sound TikTok, atau mengaktifkan keranjang kuning produk. Jangan lupa klik **Simpan**.

3. **Mempublikasikan Konten:**  
   - **Upload Satuan:** Klik tombol hijau **`Publish Konten`** di panel kanan.  
   - **Upload Massal:** Klik tombol **`Upload Massal`** di atas daftar antrean untuk menerbitkan beberapa konten sekaligus secara berurutan dengan jeda waktu otomatis.

4. **Mengambil Link Hasil Postingan:**  
   Setelah status postingan berhasil (berwarna hijau), klik tombol **`Salin Link`** pada kartu media untuk menyalin link postingan yang siap dibagikan ke tim atau klien.

---

## 🔒 Privasi & Keamanan Data
Semua file sesi login (`*_state.json`), cookie browser, kunci API (`.env`), dan file media pribadi Anda disimpan secara lokal di komputermu dan sudah diatur di `.gitignore` sehingga tidak akan terunggah ke repositori publik.
