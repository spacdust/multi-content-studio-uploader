# 🎬 Content Uploader Studio (PRO)

Aplikasi desktop studio dan dashboard web interaktif untuk mengelola serta mengunggah konten media sosial (**TikTok, Instagram, dan Facebook**) secara otomatis, terjadwal, dan rapi dalam satu layar kendali.

Tidak perlu lagi repot login bolak-balik, membuka banyak tab peramban, atau posting manual satu per satu di setiap platform. Cukup siapkan konten di dashboard, atur narasi caption atau jadwal tayangnya, dan biarkan sistem otomatisasi yang bekerja untukmu!

---

## ✨ Fitur-Fitur Utama

- 🚀 **1-Klik Upload ke 3 Platform Sekaligus (Tri-Platform Master)**  
  Konten Anda otomatis dipublikasikan secara berurutan (*sequential*) ke **TikTok Studio**, **Instagram (Reels / Feed / Carousel)**, dan **Facebook Fanspage (Reels / Foto)** tanpa risiko tabrakan sesi.

- 🤖 **Auto-Detect Model AI & Pemilihan Model Fleksibel (Baru!)**  
  Ingin memakai Gemini, OpenAI, Claude, Groq, Ollama lokal, atau model AI lainnya? Cukup masukkan Base URL & API Key di menu **Pengaturan**, klik tombol **Deteksi Model**, dan seluruh model AI yang tersedia dari endpoint akan langsung terbaca otomatis dalam menu dropdown. Anda juga bisa mengetik nama model kustom secara manual kapan saja.

- ⏰ **Penjadwalan Otomatis & Upload Massal Bertahap (Smart Auto-Scheduler)**  
  Punya banyak video yang ingin diposting hari ini? Cukup atur jam tayang pertama dan pilih interval jeda waktu (misal tiap 15 menit, 30 menit, atau 1 jam sekali). Antrean media akan dijadwalkan otomatis dan dieksekusi secara mulus di latar belakang oleh daemon scheduler.

- 🛡️ **Mesin Penjadwalan Tangguh (Anti-Gagal & Zero Platform Drop)**  
  - **Tanpa Platform Tertinggal:** Memastikan seluruh platform yang ditargetkan (TikTok, Instagram, Facebook) terbit tuntas. Jika satu platform baru selesai, bot akan melanjutkan platform yang tersisa tanpa melewatkannya.
  - **Proteksi Anti-Infinite Loop:** Bot tidak akan membuka-buka jendela Chrome terus-menerus jika ada gangguan jaringan atau sesi kedaluwarsa. Sistem menerapkan mekanisme cooldown cerdas dan auto-retry hingga 2x.
  - **Pencegahan Jadwal Basi:** Jadwal lampau yang sudah lewat lebih dari 24 jam otomatis disaring sehingga indikator jadwal tetap bersih dan akurat.

- 🛒 **Dukungan Keranjang Kuning (TikTok Shop Showcase)**  
  Ingin menautkan produk jualan ke video TikTok? Aktifkan switch keranjang kuning, cari nama produk dari katalog tokomu, pilih produk yang sesuai, dan beri nama label keranjang kuning kustom (maksimal 30 karakter). Bot akan otomatis mengaitkannya ke video saat dipublikasikan!

- ✍️ **Pembuat Caption Otomatis Berbasis AI**  
  Kehabisan ide caption? Klik tombol **AI Caption** untuk menganalisis isi video atau gambarmu. AI akan meracik narasi yang menarik, engaging, dan dilengkapi rekomendasi hashtag relevan yang rapi (dibatasi maksimal 4 hashtag agar tidak terkesan spam).

- 🔗 **Ambil Link Postingan Otomatis (Format Laporan WhatsApp Siap Kirim)**  
  Setelah konten berhasil diposting, fitur **Link Finder** dapat memindai tautan publik video di TikTok, Instagram, dan Facebook. Cukup sekali klik tombol **Salin Semua Format**, laporan rapi langsung tersalin di clipboard dan siap dikirim ke grup WhatsApp atau laporan klien.

- 🔀 **Atur Urutan Antrean Konten Sesuka Hati (Drag & Drop)**  
  Urutan penerbitan media dapat disesuaikan dengan mudah. Cukup seret (*drag-and-drop*) kartu konten di antrean atau gunakan tombol panah naik/turun.

- 👥 **Multi-Akun Mandiri & Terisolasi**  
  Kelola banyak akun atau brand sekaligus tanpa khawatir data tercampur. Setiap akun memiliki sesi login, folder konten, dan riwayat postingannya sendiri secara mandiri.

---

## 📂 Struktur Folder Konten

Cukup letakkan file media Anda ke dalam folder `content/` dengan struktur seperti berikut:

```
content/
├── Nama Akun 1/                            <-- Folder Akun 1 (contoh: Brand Official)
│   ├── Video/                              <-- Kategori Video (Reels / TikTok / FB Reel)
│   │   └── 2026-10-05/                     <-- Folder Tanggal (YYYY-MM-DD)
│   │       ├── video-2026-10-05-01.mp4     <-- File video
│   │       └── video-2026-10-05-01.json    <-- Metadata caption, jadwal, & keranjang kuning
│   ├── Poster/                             <-- Kategori Foto / Gambar Tunggal
│   │   └── 2026-10-05/
│   │       └── poster-2026-10-05-01.jpeg
│   └── Carousel/                           <-- Kategori Carousel (Multi-Slide)
│       └── 2026-10-05/
│           └── carousel-2026-10-05-01/
│               ├── slide 1.jpg
│               └── slide 2.jpg
│
└── Nama Akun 2/                            <-- Folder Akun 2 (contoh: Toko Online)
    ├── Video/
    ├── Poster/
    └── Carousel/
```

> 💡 **Tips Praktis:** Anda tidak perlu membuat folder secara manual. Cukup gunakan tombol **`+ Tambah Media`** di dashboard web, sistem akan otomatis memberi nomor urut dan menata foldernya secara rapi.

---

## 🚀 Cara Menjalankan Aplikasi

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

---

### 2. Membuka Dashboard Studio

Cara paling praktis, cukup klik dua kali file shortcut:
```powershell
start_ui.bat
```

Atau jika ingin menjalankannya lewat terminal:
```powershell
python -m src.server
```

Setelah aplikasi berjalan, buka browser di alamat:  
👉 **`http://127.0.0.1:8000`**

---

## 💡 Panduan Pemakaian Singkat

1. **Menghubungkan Akun Media Sosial:**  
   Buka dashboard web, klik tombol profil akun di kanan atas, pilih **Kelola Akun**, lalu klik tombol **Hubungkan** pada platform yang diinginkan (TikTok, Instagram, atau Facebook). Jendela peramban Playwright akan terbuka di layar fisik agar kamu bisa login dengan aman. Setelah login selesai, status akun akan berubah menjadi **`● TERHUBUNG`** (Hijau).

2. **Menyiapkan Konten & Caption:**  
   Pilih akun yang ingin dikelola. Klik **`+ Tambah Media`** untuk menambahkan video, poster, atau slide carousel. Di panel kanan (*Studio Inspector*), kamu bisa merapikan caption, membuat caption otomatis dengan AI, mengatur jadwal tayang, atau menautkan keranjang kuning produk. Jangan lupa tekan tombol **Simpan**.

3. **Mempublikasikan Konten:**  
   - **Upload Satuan:** Klik tombol hijau **`Publish Konten`** di panel kanan. Proses upload akan berjalan secara visual dengan log proses real-time.  
   - **Upload Massal Terjadwal:** Klik tombol **`Upload Massal`** di atas daftar antrean untuk menerbitkan seluruh konten secara bertahap dengan jeda waktu yang kamu tentukan.

4. **Mengambil Link Laporan Postingan:**  
   Setelah postingan berhasil terbit di media sosial, klik tombol **`Salin Link`** pada kartu media untuk menyalin tautan publik video atau menggunakan tombol **`Salin Format WA`** untuk laporan instan siap kirim.

---

## 🔒 Privasi & Keamanan Data

- Seluruh data sesi login (`*_state.json`), cookie browser, file kredensial (`.env`), serta file video dan foto pribadi Anda **100% tersimpan secara lokal** di komputer Anda sendiri.
- File-file sensitif telah dilindungi dalam `.gitignore` sehingga tidak akan pernah terunggah ke repositori publik.
