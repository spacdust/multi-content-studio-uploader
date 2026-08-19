# 🚀 Multi-Content Studio Uploader & Pipeline Bot

<p align="center">
  <b>Sistem Otomatisasi Publikasi Konten Multi-Akun & Multi-Platform Modern</b><br>
  Mendukung <b>TikTok Studio</b> & <b>Meta Business Suite (Instagram & Facebook)</b> dengan Browser Automation Playwright, AI Caption Generator, Sound Auto-Randomizer, dan Web Studio Dashboard.
</p>

---

## 🌟 Fitur Utama

- 🎨 **Modern Web Studio Dashboard:** Antarmuka visual berbasis React, Vite, Tailwind CSS, & Lucide Icons dengan pengalaman interaktif layaknya Canva/Meta Creator Studio.
- 👥 **Isolasi Multi-Akun Sempurna:** Setiap akun memiliki sesi browser, cookie login, profil, dan riwayat publikasi independen di folder `accounts/`.
- 🎬 **Multi-Format Content Publishing:**
  - **Video (Reels / TikTok / FB Video):** Upload video otomatis dengan penyesuaian volume suara asli vs musik latar.
  - **Poster (Single Image):** Upload foto tunggal langsung ke tab *Photos* TikTok Studio dan *Meta Business Suite*.
  - **Carousel (Multi-Slide Images):** Upload banyak slide gambar berurutan dengan fitur pratinjau dan pengurutan slide interaktif.
- 🎵 **TikTok Sound Auto-Randomizer & Editor:**
  - **Mode Favorites:** Memilih lagu secara acak dari tab *Favorites* resmi akun TikTok Anda.
  - **Mode Search:** Mencari sound berdasarkan kata kunci tertentu.
  - **Audio Volume Tuning:** Mengatur volume sound latar belakang (dB) secara presisi.
- 🤖 **AI Multimodal Caption Generator:** Pembuatan caption menarik secara otomatis menggunakan LLM (**Google Gemini**, **Groq Llama-3**, atau **OpenAI**) dengan aturan ketat maksimal 4 hashtag relevan.
- 🔄 **Real-Time Auto-Refresh & Granular Badges:** Pemantauan status publikasi latar belakang secara *real-time* dengan label platform jelas: `[✓ TIKTOK & META]`, `[✓ TIKTOK SAJA]`, `[✓ META SUITE SAJA]`, dan `[PENDING]`.
- 📅 **Friendly Date & Time Scheduler:** Jadwalkan postingan pada tanggal dan jam tertentu dengan format waktu WIB yang jelas.

---

## 📂 Struktur Manajemen Konten Lokal

Konten diatur secara terstruktur di dalam direktori `content/` berdasarkan nama akun, kategori, dan tanggal posting:

```
content/
├── Brand Creator Official/                 <-- Folder Nama Akun 1
│   ├── Video/
│   │   └── 2026-08-20/                     <-- Folder Tanggal (YYYY-MM-DD)
│   │       ├── video_edukasi.mp4           <-- File Video
│   │       └── video_edukasi.txt           <-- Caption & Hashtags
│   ├── Poster/
│   │   └── 2026-08-20/
│   │       ├── pamflet_promo.jpg           <-- File Foto Poster
│   │       └── pamflet_promo.txt
│   └── Carousel/
│       └── 2026-08-20/
│           └── Carousel 1/                 <-- Subfolder Konten Carousel
│               ├── Slide 1.jpg
│               ├── Slide 2.jpg
│               ├── Slide 3.jpg
│               └── caption.txt
│
└── Studio Media Digital/                   <-- Folder Nama Akun 2
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

# 2. Install dependensi Frontend Web UI
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
*(Jika tidak menggunakan API Key, bot tetap berjalan normal menggunakan Smart Persona Template Engine lokal).*

---

## ⚡ Cara Menjalankan Aplikasi

### Opsi 1: Menjalankan Web Studio Dashboard (Sangat Direkomendasikan)
Cukup jalankan file batch:
```powershell
start_ui.bat
```
Atau via perintah command line:
```powershell
python -m src.server
```
Buka browser Anda dan akses: **`http://localhost:8000`**

### Opsi 2: Skrip Batch 1-Klik

| File Batch | Fungsi |
| :--- | :--- |
| **`start_ui.bat`** | 🚀 Menjalankan Server Studio & membuka Web Dashboard di browser. |
| **`list_content.bat`** | 📋 Menampilkan tabel status semua konten (Pending vs Sukses Upload). |
| **`process_content.bat`** | ⚡ Memproses & mengunggah otomatis semua konten yang berstatus `PENDING`. |
| **`login_tiktok.bat`** | 🔑 Membuka browser interaktif untuk login akun TikTok Studio. |
| **`login_instagram.bat`** | 🔑 Membuka browser interaktif untuk login Meta Business Suite / Instagram. |

---

## 💻 Panduan Perintah CLI (Command Line Interface)

```powershell
# 1. Kelola Akun
python -m src.cli account list
python -m src.cli account add --name "Demo Brand" --desc "Akun Utama"

# 2. Login Sesi Akun
python -m src.cli login --account "Demo Brand" --platform tiktok
python -m src.cli login --account "Demo Brand" --platform meta

# 3. Cek Feed Konten
python -m src.cli content list --account "Demo Brand"

# 4. Buat Folder Tanggal Baru Otomatis
python -m src.cli content add-date --account "Demo Brand" --date "2026-08-20"

# 5. Proses Upload Konten
python -m src.cli content process --account "Demo Brand" --platform all
python -m src.cli content process --account "Demo Brand" --category Video --date "2026-08-20"
```

---

## 🛡️ Keamanan & Privasi Data

- **Zero-Credential Exposure:** Seluruh cookie, sesi login (`*_state.json`), kunci API (`.env`), serta file video dan gambar pribadi Anda secara ketat dikecualikan dari Git repository via [`.gitignore`](file:///c:/Users/spacdust/Desktop/DEV/Bot/content-uploader/.gitignore).
- **Anti-Duplikasi Postingan:** Riwayat postingan tersimpan di `accounts/<nama_akun>/upload_history.json` sehingga konten yang sama tidak akan pernah terunggah dua kali.

---

## 📜 Lisensi & Kontribusi
Dikembangkan untuk efisiensi alur kerja manajemen konten media sosial multi-akun. Bebas digunakan dan dikembangkan untuk kebutuhan pribadi atau organisasi.
