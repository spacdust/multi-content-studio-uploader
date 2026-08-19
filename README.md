# 🚀 Multi-Account Content Uploader & Pipeline Bot

Sistem otomatisasi upload konten media sosial (**TikTok** & **Instagram**) berbasis **Python & Playwright** dengan dukungan multi-akun terisolasi, manajemen folder terstruktur berbasis tanggal & kategori, pencarian sound resmi TikTok Studio Editor, penyesuaian volume dB, serta auto-captioning AI multimodal.

> 📖 **Dokumentasi Lengkap & Riwayat Progress Proyek:** Silakan baca [**`PROGRESS.md`**](file:///c:/Users/spacdust/Desktop/DEV/Bot/content-uploader/PROGRESS.md) untuk detail arsitektur, milestone pengembangan, dan status fitur terkini.

---

## 📂 Struktur Manajemen Folder Konten

Folder induk `content/` dirancang persis sesuai alur manajemen konten Anda:

```
content/
├── Aqobah International School/           <-- Nama Akun 1
│   ├── Video/
│   │   └── 2026-08-19/                    <-- Tanggal
│   │       ├── Vid1.mp4                   <-- File Video
│   │       ├── Vid1.txt                   <-- Caption (Opsional)
│   │       └── Vid2.mp4
│   ├── Poster/
│   │   └── 2026-08-19/
│   │       ├── Pic1.jpg                   <-- File Foto/Poster
│   │       └── Pic1.txt                   <-- Caption (Opsional)
│   └── Carousel/
│       └── 2026-08-19/
│           ├── Carousel 1/                <-- Subfolder Carousel
│           │   ├── Slide1.jpg
│           │   ├── Slide2.jpg
│           │   └── caption.txt
│           └── Carousel 2/
│               ├── Slide1.jpg
│               └── Slide2.jpg
│
└── Nama Akun 2/                           <-- Nama Akun 2
    ├── Video/
    │   └── 2026-08-19/
    │       ├── Vid1.mp4
    │       └── Vid2.mp4
    ├── Poster/
    │   └── 2026-08-19/
    │       └── Pic1.jpg
    └── Carousel/
        └── 2026-08-19/
            └── Carousel 1/
                ├── Slide1.jpg
                └── Slide2.jpg
```

---

## ⚡ Cara Penggunaan Praktis (1-Click Batch)

| File Batch | Fungsi |
| :--- | :--- |
| **`list_content.bat`** | 📋 Menampilkan tabel status semua konten (Pending vs Sukses Upload). |
| **`process_content.bat`** | 🚀 Memproses & mengunggah otomatis semua konten yang berstatus `PENDING`. |
| **`upload_test_tiktok.bat`** | 🎬 Uji coba manual upload video TikTok dengan browser visual & sound editor. |
| **`login_tiktok.bat`** | 🔑 Membuka browser visual untuk login akun TikTok. |
| **`login_instagram.bat`** | 🔑 Membuka browser visual untuk login akun Instagram. |

---

## 📝 Format Caption & Metadata

### 1. File `.txt` Sederhana (Rekomendasi)
Cukup buat file dengan nama yang sama, contoh:
- Video: `Vid1.mp4` -> Caption: `Vid1.txt`
- Poster: `Pic1.jpg` -> Caption: `Pic1.txt`
- Carousel: `Carousel 1/` -> Caption: `caption.txt`

### 2. File `.json` (Jika ingin kustomisasi Sound / Volume)
Contoh `Vid1.json`:
```json
{
  "caption": "Belajar asyik di Aqobah International School! #school #fyp",
  "sound_query": "school",
  "sound_db": "-7",
  "platforms": ["tiktok", "instagram"],
  "as_draft": false
}
```
*(Jika tidak ada file `.txt` atau `.json`, bot otomatis menggunakan nama file sebagai caption).*

---

## 💻 Panduan Perintah CLI

```powershell
# 1. Cek tabel manajemen konten
python -m src.cli content list

# 2. Buat folder tanggal otomatis untuk akun tertentu
python -m src.cli content init-date "2026-08-20" --account "Aqobah International School"

# 3. Proses upload semua konten PENDING
python -m src.cli content process

# 4. Proses upload dengan filter spesifik
python -m src.cli content process --account "Aqobah International School" --category Video --date "2026-08-19"
```

---

## 🛡️ Riwayat & Status Upload

Setiap postingan yang berhasil diunggah akan otomatis tercatat di `accounts/<nama_akun>/upload_history.json` dan diberi tanda **`[OK] SUKSES`** di tabel `list_content.bat`, sehingga konten yang sama tidak akan terunggah dua kali!
