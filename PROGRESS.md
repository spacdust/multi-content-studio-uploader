# 📘 DOKUMENTASI PROYEK & LOG PROGRESS PENGEMBANGAN
## Multi-Account Social Media Content Uploader & Automation Bot

Dokumen ini mencatat seluruh arsitektur teknis, riwayat progress pengembangan (*development milestone*), status fitur terkini, serta panduan operasional bot pengunggah konten media sosial (**TikTok & Instagram**).

---

## 📑 Daftar Isi
1. [Ringkasan Proyek & Arsitektur](#-ringkasan-proyek--arsitektur)
2. [Modul & Komponen Utama](#-modul--komponen-utama)
3. [Riwayat Progress Pengembangan (Milestones)](#-riwayat-progress-pengembangan-milestones)
4. [Tabel Matriks Fitur & Status Terkini](#-tabel-matriks-fitur--status-terkini)
5. [Spesifikasi Manajemen Folder Konten](#-spesifikasi-manajemen-folder-konten)
6. [Sistem AI Multimodal Caption Generator](#-sistem-ai-multimodal-caption-generator)
7. [Pro Studio Web Dashboard (React + FastAPI)](#-pro-studio-web-dashboard-react--fastapi)
8. [Manajemen Akun & Sesi Login Platform In-App](#-manajemen-akun--sesi-login-platform-in-app)
9. [In-App LLM & Vision AI Settings Manager](#-in-app-llm--vision-ai-settings-manager)
10. [Panduan Operasional & Cheat Sheet](#-panduan-operasional--cheat-sheet)
11. [Roadmap Pengembangan Selanjutnya](#-roadmap-pengembangan-selanjutnya)

---

## 📌 Ringkasan Proyek & Arsitektur

Bot ini dibangun menggunakan **Python**, **Playwright**, **OpenCV/FFmpeg**, **Multimodal LLM (Gemini Vision)**, dan **Pro Studio Web Dashboard (React + Tailwind CSS)** dengan standar desain *Linear / Apple Pro Aesthetic* untuk mengotomatisasi rantai publikasi konten dari file mentah hingga terposting secara resmi di platform target.

```
[ Pro Studio Dashboard / High-Performance Parallel Hydration ]
                      │
                      ▼
[ FastAPI Backend Engine (src/server.py) ] (72ms Ultra-Fast Latency)
                      │
       ┌──────────────┴──────────────┐
       ▼                             ▼
[ Fitur Hapus Antrean & Sortir ]     [ Friendly Dark DateTime Picker ]
 • Hapus File Media, Txt & Json Meta • Quick Presets (19:30 Prime TT/IG)
 • Modal Konfirmasi Aman             • Format 24 Jam (Jam : Menit)
 • Sortir Tanggal, Nama, Status      • Dark Mode Sesuai Tema Obsidian
 • Badge Kategori (Video/Poster/Car) • Switch Toggle ON/OFF
       │                             │
       └──────────────┬──────────────┘
                      ▼
       ┌──────────────┴──────────────┐
       ▼                             ▼
[ TikTok Studio Uploader ]   [ Instagram Uploader ]
 • Full Maximized Browser     • Reels & Feed Uploader
 • Auto-Dismiss Popups        • Multi-Slide Carousel
 • In-App Sound Search        • Status Session Tracker
 • Top Track Auto-Select (+)
 • Volume dB Tuning (-7 dB)
 • Post Submission
       │                             │
       └──────────────┬──────────────┘
                      ▼
       [ accounts/<akun>/upload_history.json ] ──> Pencatatan Sukses & Bukti Screenshot
```

---

## 🧩 Modul & Komponen Utama

| Modul File | Tanggung Jawab & Fungsi |
| :--- | :--- |
| **`src/server.py`** | Backend FastAPI REST API: Endpoint Hapus Konten (`POST /api/content/delete`), TikTok Studio Session (`/api/accounts/open-tiktok-studio`), multi-upload (`/api/content/upload-media`), penyusunan slide terurut (`Slide 1.jpg`, `Slide 2.jpg`), dukungan penjadwalan `scheduled_time`, serving frontend static bundle, dan verifikasi cookie instan. |
| **`src/content_manager.py`** | `ContentManager.delete_item(...)`: Menghapus file fisik media, file caption `.txt`, dan file metadata `.json` (atau direktori slide carousel) secara aman dari disk. |
| **`frontend/`** | Pro Studio Dashboard (React 18, Vite 6, Tailwind CSS, Lucide Icons): **Fitur Hapus Konten Antrean** (Quick Delete di feed card & Tombol Hapus di Inspector dengan Modal Konfirmasi), **Tampilan Badge Kategori & Tanggal Upload** di setiap card, **Fitur Sortir / Pengurutan Konten** (Terbaru, Terlama, Nama A-Z / Z-A, Status Pending Dulu). |
| **`src/auth_manager.py`** | `AuthManager.open_tiktok_studio(account_name)`: Membuka browser visual **True Maximized Fullscreen** (`no_viewport=True`, `--start-maximized`) yang langsung termuat dengan `storage_state` akun terpilih dan menyinkronkan cookie terbaru. |
| **`src/caption_generator.py`** | Ekstraksi keyframe video (OpenCV) & analisis visual via Multimodal LLM, aturan bebas emoji, dan batas tepat maksimal 4 hashtag. |
| **`src/tiktok_uploader.py`** | Automasi TikTok Studio: Buka browser visual fullscreen, upload video, cari musik resmi di editor sound, klik `+` lagu teratas, set volume `-7 dB`, simpan, isi caption, dan klik tombol merah `Post`. |
| **`src/instagram_uploader.py`** | Automasi Instagram: Login session handling, upload Reels & Post single/carousel. |
| **`src/account_manager.py`** | Isolasi multi-akun (misal: *Brand Creator Official*, *Studio Media Digital*, dst) dan manajemen kredensial/session state. |
| **`src/audio_processor.py`** | Engine mixing audio offline FFmpeg dengan 5 preset volume (`voiceover`, `balanced`, `music_beat`, dll). |
| **`src/validator.py`** | Validasi integritas file media (format, resolusi, durasi, batasan ukuran file). |
| **`src/cli.py`** | Antarmuka CLI terpadu untuk semua aksi (`account`, `content`, `caption`, `login`, `open-studio`, `upload`, `sound`). |

---

## 📈 Riwayat Progress Pengembangan (Milestones)

### 🔹 Fase 1: Fondasi Multi-Akun & Login Headed Interaktif
- [x] Inisialisasi arsitektur modular Python dengan Playwright.
- [x] Pembuatan sistem Multi-Account isolation di folder `accounts/<nama_akun>/`.
- [x] Implementasi browser visual (*headed*) untuk mempermudah login manual awal tanpa terblokir proteksi bot/captcha.
- [x] Penyimpanan state session ke `tiktok_state.json` dan `instagram_state.json`.

### 🔹 Fase 2: Optimasi Tampilan Layar & Auto-Dismiss Popup
- [x] Konfigurasi `--start-maximized` dan `no_viewport=True` agar browser Playwright selalu terbuka fullscreen di monitor fisik.
- [x] Implementasi mekanisme otomatis penutup popup modal (panduan tur, cookie banner, *Phone mode guidance*, dan dialog *Got it*).

### 🔹 Fase 3: Integrasi Penuh TikTok Studio In-App Sound Editor
- [x] Otomasi tombol editor sound (`button.editor-entrance[data-button-name='sounds']`) di bawah preview video TikTok.
- [x] Pencarian musik berdasarkan query pencarian (`--sound-query`).
- [x] **Deteksi Dinamis Card Lagu Teratas:** Filter elemen kartu musik (`height 40-70px`) dan klik tombol bulat merah **`+`** pada lagu paling atas secara presisi pada resolusi layar berapa pun.
- [x] **Penyesuaian Volume dB:** Pengisian otomatis nilai volume (contoh: **`-7 dB`**) pada input resmi `input.PropSettingInput__input` di panel kanan Audio.
- [x] Otomasi tombol **`Save`** untuk kembali ke form posting upload.

### 🔹 Fase 4: Perbaikan Tombol Post & Eliminasi Loop Exit
- [x] Mengatasi konflik selector antara menu sidebar `Posts` dengan tombol aksi `Post` utama.
- [x] Mengunci tombol posting resmi menggunakan `button.Button__root--type-primary` (`x > 250`), memastikan video langsung terposting tanpa memicu dialog konfirmasi keluar (*discard*).

### 🔹 Fase 5: Standarisasi Struktur Folder Konten Berbasis Tanggal
- [x] Implementasi struktur folder per akun:
  `content/<Nama Akun>/<Video|Poster|Carousel>/<Tanggal>/...`
- [x] Penambahan perintah `python -m src.cli content init-date` dan `content list`.
- [x] Pembuatan file batch 1-klik: **`list_content.bat`** dan **`process_content.bat`**.
- [x] Sistem pelacak riwayat posting `upload_history.json` untuk mencegah konten ganda (*anti-duplication*).

### 🔹 Fase 6: Otomasi Captioning dengan Multimodal AI Vision (Gemini)
- [x] Integrasi endpoint lokal OpenAI-compatible: `http://localhost:20128/v1` dengan model **`ag/gemini-3.7-flash-medium`**.
- [x] **Analisis Visual Video Asli (Vision):** Ekstraksi snapshot frame video via OpenCV dan pengiriman ke LLM untuk memahami konteks visual nyata.
- [x] **Aturan Ketat Bebas Emoji:** Penghapusan total emoji/emotikon dari caption agar hasil teks terlihat formal, profesional, dan berwibawa.
- [x] **Batas Maksimal Tepat 4 Hashtag:** Sistem *sanitizer* otomatis memastikan jumlah hashtag di baris akhir tidak melebihi 4 tagar.

### 🔹 Fase 7: Pro Studio Redesign (Linear / Apple Pro Aesthetic)
- [x] **Bespoke 2-Pane Split Studio:** Panel kiri untuk feed & timeline master list, panel kanan untuk Studio Inspector terfokus.
- [x] **Obsidian & Zinc Palette:** Mengeliminasi warna gradasi generik ("AI slop") menjadi palet gelap profesional tingkat tinggi (`#09090b`, `#18181b`, `#27272a`).
- [x] **Dedicated Video Player:** Pemutar video internal dengan rasio aspek bersih (9:16 vertical pill preview).

### 🔹 Fase 8: In-App Visual Login & Multi-Account Platform Connection Manager
- [x] **Modal Manajemen Akun & Sesi Login:** Tombol **"Kelola Akun & Login"** di header studio.
- [x] **Daftar Akun & Platform Card:** Status koneksi live per akun untuk **TikTok** dan **Instagram** (`● TERHUBUNG` vs `○ BELUM LOGIN`).
- [x] **Instant Session Verification & Auto-Refresh:** Mengganti verifikasi lambat dengan validasi cookie instan dan interval auto-poll 3 detik.

### 🔹 Fase 9: Multi-Slide Carousel Reordering, Previews, & Toggleable Scheduled Uploads
- [x] **Toggle Switch ON/OFF Penjadwalan:** Fitur penjadwalan memiliki tombol toggle switch ON/OFF yang fleksibel baik di modal Tambah Media maupun di Studio Inspector.
- [x] **Multi-File Upload untuk Carousel:** Dukungan pemilihan banyak gambar sekaligus (`multiple accept="image/*"`).
- [x] **Interactive Carousel Slide Reorder Manager:** Grid interaktif penampil semua slide dengan tombol geser urutan `[⬅️ Geser]` dan `[Geser ➡️]`, tombol hapus slide `[✕]`, serta badge penomoran urutan otomatis (`#1`, `#2`, dst). File tersimpan ke folder sebagai `Slide 1.jpg`, `Slide 2.jpg`, dst sesuai urutan yang diatur.
- [x] **Live Media Preview untuk Video & Poster:** Pemutar video dan thumbnail gambar otomatis muncul seketika saat file dipilih sebelum disimpan ke antrean.

### 🔹 Fase 10: Fitur Hapus Antrean Media, Badge Kategori/Tanggal, & Fitur Sortir
- [x] **Fitur Hapus Konten Antrean:** Tombol Hapus merah di Studio Inspector dan icon tong sampah di setiap card media list, dilengkapi dialog modal konfirmasi untuk mencegah penghapusan yang tidak disengaja.
- [x] **Tampilan Kategori & Tanggal yang Jelas:** Setiap card feed menampilkan badge kategori berwarna (`🎬 Video`, `🖼️ Poster`, `📑 Carousel`) dan badge tanggal upload (`📅 YYYY-MM-DD`).
- [x] **Fitur Sortir / Pengurutan Lengkap:** Selector pengurutan dengan 5 opsi: *Tanggal Terbaru*, *Tanggal Terlama*, *Nama (A-Z)*, *Nama (Z-A)*, dan *Status (Pending Dulu)*.

### 🔹 Fase 11: Ekstraksi & Tampilan Logo / Avatar Akun TikTok Asli
- [x] **Ekstraksi Otomatis Profil TikTok:** Membaca data resmi dari sesi akun (`tiktok_state.json`) via endpoint passport & user-detail TikTok.
- [x] **Metadata Profil:** Menampilkan foto avatar profil asli, username / handle (`@username`), nama tampilan (*nickname*), dan jumlah pengikut (*followers*).
- [x] **Penyimpanan Cache Lokal Offline:** Avatar diunduh ke `accounts/<akun>/tiktok_avatar.jpg` dan metadata ke `tiktok_profile.json` sehingga tetap dapat ditampilkan offline/cepat tanpa terpengaruh batas kedaluwarsa token CDN TikTok.
- [x] **Integrasi Visual UI:** Avatar dan handle `@username` tampil di:
  - Header Account Switcher (di samping nama akun aktif).
  - Modal Kelola Akun & Login (avatar besar, handle, dan follower counter).
  - Header Studio Inspector (avatar mini di samping nama akun konten).

### 🔹 Fase 12: Bespoke Pro Account Switcher Popover (Linear / Raycast / Apple Aesthetic)
- [x] **Redesain Switcher Akun Menjadi Pro Command Button:** Mengganti `<select>` HTML bawaan menjadi tombol interaktif berkelas dengan foto avatar bulat, titik status aktif, nama akun tebal, handle `@username`, platform status chips (`TT ●` | `IG ●`), dan chevron ganda (*ChevronsUpDown*).
- [x] **Floating Popover Menu:** Membuka menu popover mengambang dengan latar *Obsidian Deep Black* (`#09090b`), efek *backdrop-blur-xl*, dan *hairline border* (`zinc-800`).
- [x] **Daftar Akun Eksklusif:** Setiap akun ditampilkan dalam kartu lengkap dengan foto profil, handle `@username`, follower counter, status platform, dan badge glowing checkmark `✓ AKTIF`.
- [x] **Dukungan Micro-Interactions:** Otomatis tertutup saat klik di luar area (*click-outside*) atau saat menekan tombol `Escape` (ESC).
- [x] **Quick Action Footer:** Integrasi langsung tombol cepat *Kelola Akun & Login* dan shortcut *Buka TikTok Studio* di dalam popover.

### 🔹 Fase 13: Pembersihan Navbar & Relokasi Tombol Tambah Media
- [x] **Minimalist Pro Navbar:** Menghapus tombol redundan *TikTok Studio*, *Kelola Akun*, dan *Tambah Media* dari navbar atas sehingga menyisakan hanya identitas studio, switcher akun popover, dan tombol konfigurasi settings.
- [x] **Contextual Feed Section Header:** Memindahkan tombol utama **`[+ Tambah Media]`** ke header panel kiri (Master Feed), berdampingan langsung dengan judul *Antrean Konten* dan badge counter media.

### 🔹 Fase 14: Persistensi Akun Aktif Terakhir (*Persistent Active Account State*)
- [x] **Penyimpanan State Otomatis:** Menggunakan mekanisme `localStorage` terenkapsulasi untuk mengingat akun aktif terakhir yang Anda pilih.
- [x] **Hydration Tanpa Flicker:** Saat dashboard direfresh atau dibuka kembali, sistem langsung memuat antrean konten untuk akun terakhir yang aktif tanpa berpindah ke akun pertama secara default.

### 🔹 Fase 15: Shortcut Buka Instagram Sesuai Akun Terpilih (*Account-Specific Instagram Launcher*)
- [x] **Shortcut Popover Switcher:** Tombol aksi cepat **`[📸 Instagram]`** di dalam footer floating popover switcher akun, berdampingan dengan shortcut TikTok Studio.
- [x] **Shortcut Modal Kelola Akun:** Tombol **`[Instagram]`** di dalam kartu platform Instagram pada modal manajemen akun.
- [x] **Maximized Session Browser:** Membuka browser visual Playwright Chromium langsung fullscreen/maximized dengan sesi login akun yang tersimpan (`instagram_state.json`), dan otomatis menyimpan perubahan cookies saat selesai.
- [x] **Stealth & Zero-Interference Polling:** Menghilangkan injeksi JavaScript CDP berulang setiap 2 detik yang memicu redirect loop / refresh di aplikasi React Instagram, serta menambahkan modul anti-detection `navigator.webdriver` sehingga Instagram berjalan mulus dan tenang tanpa reload berulang.

### 🔹 Fase 16: Integrasi Meta Business Suite (Posting Paralel Instagram + Facebook)
- [x] **Cross-Posting Paralel IG & FB:** Mengintegrasikan komposer resmi Meta Business Suite (`https://business.facebook.com/latest/composer`) untuk mempublikasikan konten ke Instagram dan Halaman Facebook sekaligus dalam 1x klik.
- [x] **Login Interaktif via Akun Instagram/FB:** Mendukung login visual 1x menggunakan akun Instagram (tombol *Log in with Instagram*) atau Facebook, dan menyimpan sesi terisolasi per akun di `accounts/<nama_akun>/meta_state.json`.
- [x] **Shortcut Meta Suite Popover & Modal:** Tombol aksi cepat **`[⚡ Meta Suite]`** di footer popover switcher akun dan kartu platform ke-3 di modal manajemen akun.
- [x] **Status Platform Tri-Indikator:** Indikator visual realtime `TT ● | IG ● | META ●` pada switcher trigger navbar dan kartu akun.

### 🔹 Fase 17: Perbaikan Tampilan Thumbnail & Interactive Carousel Slide Navigator
- [x] **Fix Broken Carousel Media URL:** Memperbaiki resolusi URL media Carousel pada endpoint `/api/content/media/...` dari string parsing `.split(" ")[0]` menjadi regex extractor utuh dan nested path routing `{filename:path}` sehingga semua slide gambar carousel langsung tampil jernih.
- [x] **Thumbnail Badge Counter:** Menambahkan badge jumlah slide `[📑 N]` pada sudut thumbnail card di antrean konten.
- [x] **Interactive Multi-Slide Inspector Viewer:** Menambahkan kontrol navigasi slide interaktif (`<` / `>`) serta badge counter `[Slide 1 / 4]` di dalam Studio Inspector sehingga seluruh slide carousel dapat di-preview dan digeser langsung sebelum di-publish.

### 🔹 Fase 18: Fitur TikTok Sound Dual Mode (Search Query vs Random Favorite Sound)
- [x] **Mode 1 - Pencarian Sound Spesifik (`search`):** Memungkinkan pengguna mengetik kata kunci musik (misal: `nasyid`, `school`, `santri`, `instrumental`) dan bot akan otomatis mencari serta memilih lagu teratas di TikTok Studio.
- [x] **Mode 2 - Randomizer Pustaka Suara Favorit (`favorite`):** Bot secara otomatis membuka tab *Favorites* di TikTok Studio akun tersebut, lalu memilih salah satu musik favorit secara **acak (random)** untuk tiap postingan agar konten selalu dinamis, variatif, dan tidak monoton.
- [x] **Segmented Sound Controller UI:** Panel kontrol audio di Studio Inspector yang intuitif dengan toggle `[🔍 Cari Sound]` dan `[⭐ Favorite (Random)]` lengkap dengan slider/input volume dB.
- [x] **Universal Multi-Format Sound:** Fitur sound TikTok aktif dan dapat disetel untuk semua kategori konten: **Video**, **Poster**, dan **Carousel**.

### 🔹 Fase 19: Dynamic Platform Detection & Platform-Scoped Inspector Rules
- [x] **Smart Dynamic Publish Button:** Tombol publish utama otomatis menyesuaikan teks dan platform target secara dinamis berdasarkan platform yang sedang terhubung/login (`Publish to TikTok`, `Publish to TikTok & Instagram`, `Publish to TikTok & Meta Suite`, dsb). Jika belum ada platform yang login, tombol otomatis terkunci dengan label instruksi.
- [x] **Platform Scope Badging:** Setiap kartu aturan konfigurasi di Studio Inspector kini dilengkapi label scope yang jelas:
  - *Jadwalkan Publikasi:* `[Semua Platform]`
  - *Narasi Caption & Hashtags:* `[Semua Platform]`
  - *Mode Audio / Sound TikTok:* `[Khusus TikTok]`
- [x] **Pembersihan Teks Redundan:** Menghilangkan label *"(Tanpa Emoji)"* pada bagian narasi caption sehingga tampilan menjadi lebih profesional dan bersih (`Narasi Caption & Hashtags`).
### 🔹 Fase 22: Clean Code Modular Frontend Architecture Refactoring
- [x] **Component-Driven Architecture:** Memecah monolitik `App.jsx` (~2.800 baris) menjadi 18 modul komponen terpisah di `components/` (Navbar, Feed, Studio Inspector, Modals, Common).
- [x] **Centralized API Services Layer:** Memisahkan seluruh pemanggilan HTTP endpoint ke dalam folder `api/` (`accountApi.js`, `contentApi.js`, `settingsApi.js`).
- [x] **Custom Hooks State Management:** Mengenkapsulasi logika state ke dalam custom hooks yang terisolasi di folder `hooks/` (`useAccounts.js`, `useContent.js`, `useSettings.js`, `useToast.js`).
- [x] **Dedicated Utility & Constants:** Helper waktu 24 jam & konfigurasi warna di folder `utils/` (`dateUtils.js`, `constants.js`).
- [x] **Lean Root Orchestrator:** `App.jsx` dirampingkan dari 2.800+ baris menjadi hanya ~170 baris yang bersih dan sangat terstruktur.
### 🔹 Fase 23: CLI Content Process Subparser Fix & Targeted Publishing
- [x] **CLI Subparser Integration:** Memperbaiki registrasi subparser `content process` pada `src/cli.py` yang sebelumnya belum terdaftar sehingga pemanggilan `python -m src.cli content process` kini dieksekusi secara mulus.
- [x] **Targeted Item Dispatch:** Menambahkan parameter `--item` ke CLI sehingga tombol publish di web UI dapat menargetkan konten spesifik secara presisi tanpa terhalang filter status.
- [x] **Full Chromium Automation Verified:** Menguji eksekusi `TikTokUploader.upload()` secara langsung yang terbukti berhasil membuka halaman Creator Upload TikTok dan mengunggah video beserta sound pilihan.

### 🔹 Fase 24: Robust Multi-Strategy TikTok Favorites Tab & Sound Selection
- [x] **Eliminated High-Level Selector Collisions:** Menghilangkan selektor broad generic yang sebelumnya mengenai container root wrapper, digantikan dengan selektor presisi bertingkat (`role="tab"`, exact text matching, dan area bounding box detection).
- [x] **Interactive Hover & Click Trigger:** Menambahkan auto-hover pada sound card di tab Favorites untuk memicu tombol `+` (*Add*) sebelum mengklik koordinat.
- [x] **Graceful Fallback:** Menambahkan auto-fallback ke mode search query secara otomatis jika akun TikTok belum memiliki daftar lagu favorit yang tersimpan.

### 🔹 Fase 25: Real-time Auto-Refresh Status & Multi-Platform Publication Badges
- [x] **Proactive Real-time Status Polling:** Dashboard otomatis menjalankan pemantauan status latar belakang setiap 4 detik saat upload berlangsung dan langsung memperbarui status tanpa perlu refresh manual.
- [x] **Platform-Specific Status Badges:** Menggantikan status biner generic dengan label presisi:
  * `[ 🟢 ✓ TIKTOK & META ]` (Terposting di kedua platform)
  * `[ 🟢 ✓ TIKTOK ]` (Terposting di TikTok saja)
  * `[ 🔵 ✓ META SUITE ]` (Terposting di Meta Suite saja)
  * `[ 🟡 PENDING ]` (Belum dipublikasikan)
- [x] **Studio Inspector Status Breakdown:** Menyajikan banner ringkasan status publikasi interaktif untuk TikTok dan Meta Suite, lengkap dengan tombol `Re-Publish` atau `Publish`.
- [x] **Granular Status Filter:** Memungkinkan penyaringan antrean konten berdasarkan `Semua Status`, `Belum Diposting`, `TikTok Saja`, `Meta Suite Saja`, dan `Semua Platform`.

### 🔹 Fase 26: TikTok Poster & Carousel Photo Upload + Direct Sound Integration
- [x] **Tab Photos Navigation & Multi-Slide Payload:** Mengarahkan uploader langsung ke `tiktokstudio/upload?tab=photo` dan mengunggah gambar tunggal (Poster) atau multi-file slide (Carousel) ke form TikTok Photo Composer.
- [x] **Direct Sound Selection under Description:** Menyesuaikan alur sound khusus konten foto dengan mengklik tombol `+ Add sound` yang berada tepat di bawah deskripsi caption.
- [x] **Modal Favorites & 'Use' Action Verified:** Mengintegrasikan pemilihan sound dari tab Favorites (maupun Search) di dalam modal Sound TikTok dan mengklik tombol merah `Use` untuk menerapkan sound ke postingan foto/carousel.
- [x] **Direct File Injection (No Native OS Picker):** Memastikan Playwright menyuntikkan file gambar langsung via `set_input_files()` ke elemen `<input type="file">` tanpa mengklik kontainer dropzone/tombol yang memicu kotak dialog "Open" Windows.
- [x] **Title Field Left Blank (Caption-Only):** Kolom judul (*catchy title*) dikosongkan secara default agar fokus hanya menggunakan deskripsi caption yang rapi.
- [x] **Verified via Live Playwright Testing:** Teruji berhasil memilih sound favorit secara otomatis dan mengaitkannya ke postingan carousel 4 slide dengan bukti screenshot visual.

---

## 📊 Tabel Matriks Fitur & Status Terkini

| Fitur / Komponen | Status | Keterangan |
| :--- | :---: | :--- |
| **TikTok Poster & Carousel Upload** | ✅ **Stabil** | Upload multi-slide / single photo + sound via tab Photos |
| **Direct Photo Sound Selector** | ✅ **Stabil** | Otomasi tombol `+ Add sound` di bawah deskripsi caption |
| **Real-time Status Polling** | ✅ **Stabil** | Status otomatis terperbarui langsung begitu bot selesai upload |
| **Multi-Platform Status Badges** | ✅ **Stabil** | Keterangan jelas: TikTok Saja, Meta Saja, atau Keduanya |
| **TikTok Random Favorite Sound** | ✅ **Stabil** | Multi-strategy selector tab Favorit + hover & click sound |
| **CLI Targeted Publishing** | ✅ **Stabil** | Integrasi `content process --item` langsung ke Playwright uploader |
| **Modular Clean Architecture** | ✅ **Stabil** | Pemisahan modul API, Hooks, Utilities, & UI Components |
| **Individual Platform Test Buttons** | ✅ **Stabil** | Tombol `Publish TikTok` & `Publish Meta Suite` mandiri |
| **Unified 2-Platform Model** | ✅ **Stabil** | TikTok Studio + Meta Business Suite (Instagram & Facebook) |
| **Dynamic Platform Detection** | ✅ **Stabil** | Tombol publish & uploader auto-detect platform yang aktif login |
| **TikTok Random Favorite Sound** | ✅ **Stabil** | Auto-randomizer sound favorit dari tab Favorites TikTok |
| **Carousel Slide Navigator** | ✅ **Stabil** | Preview interaktif semua slide carousel di Studio Inspector |
| **Meta Business Suite (IG+FB)** | ✅ **Stabil** | 1x klik posting paralel ke Feed/Reels IG & Fanspage Facebook |
| **Account-Specific Instagram** | ✅ **Stabil** | 1-klik buka browser langsung masuk ke sesi Instagram akun |
| **Persistent Active Account** | ✅ **Stabil** | Otomatis mengingat akun terakhir saat app dibuka kembali |
| **Minimalist Pro Navbar** | ✅ **Stabil** | Navbar bersih dengan switcher akun terintegrasi & settings |
| **Contextual Feed Header** | ✅ **Stabil** | Tombol `[+ Tambah Media]` tepat di atas antrean konten |
| **Bespoke Pro Account Switcher** | ✅ **Stabil** | Floating popover dengan avatar, `@username`, dan quick actions |
| **Logo & Avatar Akun TikTok Asli** | ✅ **Stabil** | Foto profil resmi, handle `@username`, & follower counter |
| **Fitur Hapus Antrean Media** | ✅ **Stabil** | Hapus file fisik media & caption dengan modal konfirmasi |
| **Badge Kategori & Tanggal di Card**| ✅ **Stabil** | Label `🎬 Video`, `🖼️ Poster`, `📑 Carousel`, `📅 Tanggal` |
| **Fitur Sortir / Pengurutan Data**| ✅ **Stabil** | Urutkan berdasarkan Tanggal, Nama A-Z/Z-A, dan Status |
| **Single Media Entrypoint** | ✅ **Stabil** | 1 tombol Tambah Media lengkap dengan auto-folder |
| **Maximized Account Studio Window** | ✅ **Stabil** | Browser Chromium langsung fullscreen di foreground |
| **Account-Specific TikTok Studio** | ✅ **Stabil** | 1-klik buka browser langsung masuk ke sesi akun yang dipilih |
| **Friendly Dark DateTime Picker** | ✅ **Stabil** | Picker gelap dengan Quick Preset (Hari ini, Besok, Prime 19:30) |
| **Format Waktu 24 Jam (Jam : Menit)**| ✅ **Stabil** | Jam 00-23 dan Menit 00-55 tanpa AM/PM membingungkan |
| **Toggleable Schedule (ON/OFF)** | ✅ **Stabil** | Switch toggle aktif/nonaktif penjadwalan konten |
| **Carousel Multi-Slide Reordering** | ✅ **Stabil** | Atur urutan tayang slide carousel dengan tombol ⬅️ ➡️ |
| **Live Single Media Preview** | ✅ **Stabil** | Preview video player & gambar poster sebelum upload |
| **Instant Video Thumbnail** | ✅ **Stabil** | Frame pertama video langsung tampil di list feed |
| **Stable Account Switcher** | ✅ **Stabil** | Pilihan akun tidak ter-reset saat background polling |
| **Sub-100ms Ultra-Fast Startup** | ✅ **Stabil** | Total latensi 3 endpoint hanya 72ms (~70x lebih cepat) |
| **Non-Blocking Media Scanner** | ✅ **Stabil** | Scan direktori instan tanpa menunggu model AI |
| **Instant Session Auto-Sync** | ✅ **Stabil** | Status terupdate otomatis begitu browser login ditutup |
| **In-App Account & Login Manager** | ✅ **Stabil** | Hubungkan TikTok & IG langsung dari dashboard |
| **Live Browser Spawner** | ✅ **Stabil** | Native subprocess membuka browser Chromium visual di layar |
| **In-App LLM Settings** | ✅ **Stabil** | Atur Base URL, API Key, Model di UI |
| **Live Connection Tester** | ✅ **Stabil** | Uji latensi dan respon endpoint secara instan |
| **Pro Studio Web Dashboard** | ✅ **Stabil** | Desain studio 2-pane di `http://localhost:8000` |
| **1-Click UI Launcher** | ✅ **Stabil** | `start_ui.bat` otomatis membuka browser |
| **Multi-Account Storage** | ✅ **Stabil** | Sesi terpisah per subdirektori akun |
| **Visible Fullscreen Browser** | ✅ **Stabil** | Native fullscreen tanpa terpotong |
| **Auto-Dismiss Dialog & Popups** | ✅ **Stabil** | Menutup modal panduan TikTok otomatis |
| **In-App Sound Search (+)** | ✅ **Stabil** | Mengklik lagu #1 hasil search teratas |
| **Volume dB Adjustment (-7 dB)** | ✅ **Stabil** | Mengisi nilai dB dan menggeser slider volume |
| **Primary Post Button Submission** | ✅ **Stabil** | Klik tombol merah Post tanpa salah sasaran |
| **Struktur Folder Tanggal & Kategori**| ✅ **Stabil** | `Video/`, `Poster/`, `Carousel/` |
| **Upload History Tracker** | ✅ **Stabil** | Mencegah posting ganda (`upload_history.json`) |
| **LLM Vision Auto-Caption** | ✅ **Stabil** | Analisis frame video nyata dengan vision model |
| **Aturan Bebas Emoji (No Emojis)** | ✅ **Stabil** | 100% teks bersih tanpa simbol emotikon |
| **Maksimal Tepat 4 Hashtag** | ✅ **Stabil** | Filter ketat pembatas 4 tagar relevan |
| **Unit Test Coverage** | ✅ **100% Green** | 6 unit test passing |

---

## 📁 Spesifikasi Manajemen Folder Konten

```
content/
├── Brand Creator Official/                 <-- Akun 1
│   ├── Video/
│   │   └── 2026-08-19/                    <-- Format Tanggal (YYYY-MM-DD)
│   │       ├── 1.mp4                      <-- Video Asli
│   │       └── 1.txt                      <-- Caption AI (Otomatis Dibuat)
│   ├── Poster/
│   │   └── 2026-08-19/
│   │       ├── Pic1.jpg                   <-- Gambar Tunggal
│   │       └── Pic1.txt                   <-- Caption (Opsional/Auto AI)
│   └── Carousel/
│       └── 2026-08-19/
│           └── Carousel 1/                <-- Folder Slide
│               ├── Slide 1.jpg            <-- Slide Urutan #1
│               ├── Slide 2.jpg            <-- Slide Urutan #2
│               ├── caption.txt
│               └── meta.json              <-- Metadata & Jadwal
│
└── Studio Media Digital/                   <-- Akun 2 (Dst)
    ├── Video/
    │   └── 2026-08-19/
    ├── Poster/
    │   └── 2026-08-19/
    └── Carousel/
        └── 2026-08-19/
```

---

## 🔑 Manajemen Akun & Sesi Login Platform In-App

Klik tombol **`👥 Kelola Akun & Login`** atau klik pill status `TT` / `IG` di header:
1. **Daftar Akun Terdaftar:** Menampilkan semua profil akun (misal: *Brand Creator Official*, *Studio Media Digital*, dll).
2. **Status Live Per Platform:**
   - **TikTok:** Menunjukkan status session aktif (`● TERHUBUNG`) atau belum login (`○ BELUM LOGIN`).
   - **Instagram / Meta:** Menunjukkan status session aktif (`● TERHUBUNG`) atau belum login (`○ BELUM LOGIN`).
3. **Tombol "Hubungkan Platform":**
   - Klik **`[Hubungkan TikTok]`** atau **`[Hubungkan Meta Suite]`** untuk otomatis membuka jendela Chromium visual Playwright di layar fisik.
   - Selesaikan login di jendela yang muncul.
   - Sesi cookie otomatis tersimpan dan status di dashboard langsung berubah menjadi **TERHUBUNG (Hijau)** secara real-time.
4. **Tombol Shortcut Sesi:** Pada card TikTok tersedia tombol shortcut `[Studio]` untuk membuka browser visual dengan sesi akun tersebut.

---

## 🛠 Panduan Operasional & Cheat Sheet

### 1. File Shortcut 1-Klik
* **[`start_ui.bat`](file:///c:/Users/spacdust/Desktop/DEV/Bot/content-uploader/start_ui.bat)** : 🚀 **Membuka Pro Studio Web Dashboard (React)**.
* **[`list_content.bat`](file:///c:/Users/spacdust/Desktop/DEV/Bot/content-uploader/list_content.bat)** : 📋 Tampilkan tabel status konten di terminal.
* **[`process_content.bat`](file:///c:/Users/spacdust/Desktop/DEV/Bot/content-uploader/process_content.bat)** : ⚡ Eksekusi upload semua konten yang berstatus `PENDING`.
* **[`upload_test_tiktok.bat`](file:///c:/Users/spacdust/Desktop/DEV/Bot/content-uploader/upload_test_tiktok.bat)** : 🎬 Test upload langsung video TikTok di browser fullscreen.
* **[`login_tiktok.bat`](file:///c:/Users/spacdust/Desktop/DEV/Bot/content-uploader/login_tiktok.bat)** : 🔑 Buka browser untuk login akun TikTok via terminal.
* **[`login_instagram.bat`](file:///c:/Users/spacdust/Desktop/DEV/Bot/content-uploader/login_instagram.bat)** : 🔑 Buka browser untuk login akun Instagram via terminal.

### 2. Perintah CLI Terminal
```powershell
# Jalankan Pro Studio dashboard
start_ui.bat

# Buka TikTok Studio langsung dengan sesi akun tertentu
python -m src.cli open-studio --account "Demo Brand"

# Cek tabel konten via CLI
python -m src.cli content list

# Proses upload antrean via CLI
python -m src.cli content process

# Test generate caption AI untuk topik tertentu
python -m src.cli caption generate "lomba pidato bahasa arab" --account "Demo Brand"

# Menjalankan unit test
python -m unittest discover tests
```

---

## 🚀 Roadmap Pengembangan Selanjutnya

1. [ ] **Instagram Carousel Multi-Image Poster Live Flow:** Pengujian alur posting carousel multi-slide visual di Instagram.
2. [ ] **Background Audio Merger untuk Carousel:** Otomatisasi penggabungan kumpulan slide gambar menjadi video carousel berlatar musik sebelum upload ke TikTok Photo Mode.
3. [ ] **Scheduler Daemon / Cron Mode:** Service latar belakang yang mengeksekusi upload otomatis sesuai timestamp `scheduled_time`.
4. [ ] **Notifikasi Telegram / WhatsApp Bot:** Mengirim laporan keberhasilan upload beserta bukti screenshot ke grup tim konten.
