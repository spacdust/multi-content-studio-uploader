# 🚀 Multi-Content Studio Uploader & Pipeline Bot (v1.1)

<p align="center">
  <img src="https://img.shields.io/badge/version-1.1.0-emerald?style=for-the-badge" alt="Version 1.1.0" />
  <img src="https://img.shields.io/badge/platforms-TikTok%20%7C%20Instagram%20%7C%20Facebook-blue?style=for-the-badge" alt="Supported Platforms" />
  <img src="https://img.shields.io/badge/accuracy-100%25%20Precision-teal?style=for-the-badge" alt="Precision Scanner" />
  <img src="https://img.shields.io/badge/license-MIT-purple?style=for-the-badge" alt="License" />
</p>

<p align="center">
  <b>Sistem Otomatisasi Publikasi Konten Multi-Akun & Tri-Platform Terpadu</b><br>
  Mendukung <b>TikTok Studio</b>, <b>Instagram (Reels & Feed)</b>, dan <b>Facebook Fanspage (Reels & Foto/Carousel)</b> dengan Browser Automation Playwright, Instagrapi Mobile Engine, Precision Public Post Link Scanner, AI Multimodal Caption Generator, Sound Volume Tuning, dan Web Studio Dashboard Modern.
</p>

---

## 🌟 Fitur Unggulan (v1.1 Live Release)

- 🔗 **Precision Public Post Link Scanner (100% Akurat):**
  - Pemindaian otomatis tautan publik hasil postingan di **TikTok**, **Instagram**, dan **Facebook**.
  - **Category-Aware Routing:** Otomatis membedakan format **Video (Reels)**, **Poster (Foto Tunggal)**, dan **Carousel (Multi-Slide)**.
  - **Smart Sequence Matching (`difflib`):** Pencocokan caption berurutan presisi tinggi tanpa risiko salah cocok (*false positive*).
  - **Instagram Dedicated Clips:** Ekstraksi reel langsung via protokol Instagram Clips (`user_clips`) dan feed grid (`user_medias`).
  - **TikTok Studio Multi-Phrase Search:** Pemindaian pencarian frasa cerdas di TikTok Studio dengan fitur *early stop*.
  - **Facebook Scoped Reels & Timeline:** Memindai reels langsung di area konten utama Facebook (`div[role='main']`) dan membaca caption video player asli.
  - **Modal Salin Link Interaktif:** Tampilan modal modern bertema Obsidian dengan status *live progress*, tombol salin per-platform, dan tombol master **"Salin Semua Format (WhatsApp / Laporan)"**.
  - **Modal Persistence Lock:** Modal tetap terbuka stabil saat Anda menyalin link dan tidak akan tertutup otomatis oleh polling latar belakang.
- 🟢 **1-Click Master Publish (Tri-Platform Sequential):**
  - Publikasi konten ke 3 platform sekaligus secara berurutan (**TikTok $\rightarrow$ Instagram $\rightarrow$ Facebook**) hanya dengan satu tombol hijau.
  - Modal Live Progress interaktif dengan *embedded monospace log viewer*, persentase real-time, dan floating widget yang bisa diminimize.
- 👥 **Isolasi Multi-Akun & Kloning Sesi Mandiri:**
  - Setiap akun memiliki profil, sesi browser (`tiktok_state.json`, `instagram_state.json`, `facebook_state.json`), dan riwayat publikasi independen di folder `accounts/`.
- 🎬 **Dukungan Tri-Format Konten Baku:**
  - **Video (Reels / TikTok / FB Video):** Upload video otomatis ke TikTok Studio, IG Reels, dan Facebook Reels.
  - **Poster (Single Image):** Upload foto tunggal langsung ke TikTok Photo, IG Postingan, dan Facebook Fanspage.
  - **Carousel (Multi-Slide Images):** Upload banyak slide gambar dengan fitur pengurutan naik/turun interaktif, thumbnail jelas, dan navigasi slide di Studio Previewer.
- 🏷️ **Standard Penamaan Berkas Otomatis:**
  - Format baku: `video-YYYY-MM-DD-01.mp4`, `poster-YYYY-MM-DD-01.jpeg`, `carousel-YYYY-MM-DD-01`.
  - Penomoran otomatis (*auto-increment*) menyesuaikan nomor urut terakhir pada tanggal dan kategori yang sama.
- 📅 **Filter Tanggal Terpadu (Default: Hari Ini):**
  - Antarmuka otomatis menyaring dan memfokuskan antrean pada **Hari Ini**.
  - Dropdown tanggal tunggal terpadu (*Hari Ini*, *Semua Tanggal*, arsip folder tanggal, dan *Pilih Tanggal Kustom...*).
- 🎵 **TikTok Sound & Volume Tuning Spesifik Kategori:**
  - Default volume suara latar: **`-7 dB`** untuk Video, dan **`0 dB`** untuk Poster & Carousel.
  - Dual Mode Audio: Pencarian kata kunci spesifik (*Search Query*) atau pengacakan otomatis pustaka lagu favorit (*Favorite Randomizer*).
- 🤖 **AI Multimodal Caption Generator:** Pembuatan caption menarik secara otomatis menggunakan LLM (**Google Gemini**, **Groq Llama-3**, atau **OpenAI**) dengan batas maksimal 4 hashtag relevan.
- 🛡️ **Zero-Leak Data Security:** Seluruh berkas sesi login, cookie, token API, dan berkas media pribadi secara ketat dikecualikan dari Git repository via `.gitignore`.

---

## 📂 Struktur Manajemen Konten

Konten diatur secara terstruktur dan otomatis di dalam direktori `content/` berdasarkan nama akun, kategori, dan tanggal posting:

```
content/
├── Gus Kikin Official/                      <-- Folder Nama Akun 1
│   ├── Video/
│   │   └── 2026-08-20/                     <-- Folder Tanggal (YYYY-MM-DD)
│   │       ├── video-2026-08-20-01.mp4     <-- File Video
│   │       └── video-2026-08-20-01.json    <-- Metadata & Caption
│   ├── Poster/
│   │   └── 2026-08-20/
│   │       ├── poster-2026-08-20-01.jpeg   <-- File Poster
│   │       └── poster-2026-08-20-01.json
│   └── Carousel/
│       └── 2026-08-20/
│           └── carousel-2026-08-20-01/     <-- Subfolder Carousel
│               ├── Slide 1.jpg
│               ├── Slide 2.jpg
│               └── meta.json
│
└── Poros Waras/                            <-- Folder Nama Akun 2
    ├── Video/
    ├── Poster/
    └── Carousel/
```

---

## 🚀 Panduan Memulai Cepat

### 1. Prasyarat Sistem
- Python 3.10+
- Node.js 18+ & npm
- Google Chrome atau Chromium

### 2. Instalasi Dependensi
```powershell
# 1. Install dependensi Python & Playwright Chromium
pip install -r requirements.txt
playwright install chromium

# 2. Build Frontend Web Studio
cd frontend
npm install
npm run build
cd ..
```

### 3. Konfigurasi Lingkungan (Opsional untuk AI Caption)
Salin `.env.example` menjadi `.env` dan masukkan API Key yang Anda miliki:
```powershell
copy .env.example .env
```

---

## ⚡ Cara Menjalankan Aplikasi

### Menjalankan Web Studio Dashboard
Cukup klik dua kali:
```powershell
start_ui.bat
```
Atau via terminal:
```powershell
python -m src.server
```
Buka browser dan akses: **`http://localhost:8000`**

---

## 💻 Panduan Perintah CLI

```powershell
# 1. Kelola Akun
python -m src.cli account list
python -m src.cli account add --name "Nama Akun" --desc "Deskripsi"

# 2. Login Sesi Platform
python -m src.cli login --account "Nama Akun" --platform tiktok
python -m src.cli login --account "Nama Akun" --platform instagram
python -m src.cli login --account "Nama Akun" --platform facebook

# 3. Proses Publikasi Konten
python -m src.cli content process --account "Nama Akun" --platform all

# 4. Buka Browser Studio Terisolasi
python -m src.cli open-studio --account "Nama Akun"
```

---

## 🛡️ Keamanan & Privasi Data

- **Strict Session Isolation:** Seluruh cookie, sesi login (`*_state.json`), kunci API (`.env`), serta file video dan gambar pribadi Anda secara ketat dikecualikan dari Git repository via [`.gitignore`](.gitignore).
- **Anti-Duplikasi Postingan:** Riwayat publikasi dan tautan URL postingan tersimpan di `accounts/<nama_akun>/upload_history.json` sehingga konten yang sama tidak akan terunggah dua kali.

---

## 📜 Lisensi
Dikembangkan untuk efisiensi alur kerja manajemen konten media sosial multi-akun. Bebas digunakan dan dikembangkan untuk kebutuhan pribadi atau organisasi.
