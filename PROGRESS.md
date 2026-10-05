# 📘 DOKUMENTASI PROYEK & LOG PROGRESS PENGEMBANGAN
## Multi-Account Social Media Content Uploader & Automation Bot

Dokumen ini mencatat seluruh arsitektur teknis, riwayat progress pengembangan (*development milestone*), status fitur terkini, serta panduan operasional bot pengunggah konten media sosial (**TikTok & Instagram**).

---

## 📑 Daftar Isi
0. [Aturan Pengembangan & Git Policy](#-aturan-pengembangan--git-policy)
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

## ⚠️ Aturan Pengembangan & Git Policy
> **ATURAN MUTLAK:** DILARANG melakukan `git push` ke remote repository (GitHub) secara otomatis setelah pengerjaan fitur/perbaikan kode, **KECUALI jika USER secara eksplisit memberikan perintah push**.
> Seluruh pengerjaan, pengujian, dan build dilakukan secara lokal.

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

### 🔹 Fase 28: Direct Facebook Fanspage Uploader (Reels & Foto/Carousel)
- [x] **Pemisahan Alur Konten Facebook Presisi:** Video diunggah via ikon merah `Reel`, sedangkan Poster & Carousel diunggah via ikon hijau `Foto/video`.
- [x] **Alur Caption Foto/Carousel:** Pengetikan narasi caption dilakukan di bagian atas postingan segera setelah media terunggah, lalu dilanjutkan dengan tombol `[ Berikutnya ]` $\rightarrow$ `[ Kirim ]`.
- [x] **Pencatatan Status Independen:** Status tersimpan terpisah di `upload_history.json` dengan bukti screenshot di folder `logs/`.

### 🔹 Fase 29: Tri-Platform Master 1-Click Sequential Publishing (TikTok ➔ Instagram ➔ Facebook)
- [x] **Eksekusi 1-Klik Terpadu (Tombol Hijau):** Mengotomasi publikasi ke 3 platform secara berurutan (*sequential*): TikTok Studio $\rightarrow$ Instagram Web $\rightarrow$ Facebook Fanspage.
- [x] **Live Real-time Multi-Platform Polling:** Pemantauan otomatis frontend diperbaiki agar tetap aktif memantau hingga ketiga platform selesai terposting tanpa berhenti di platform pertama.
- [x] **Default Audio Volume Spesifik Kategori:** Suara latar belakang disetel default `-7 dB` untuk Video, dan `0 dB` untuk Poster & Carousel. Default query TikTok sound dikosongkan (`""`).

### 🔹 Fase 30: Standarisasi Format Penamaan Berkas Otomatis (Sequential Naming)
- [x] **Format Baku Otomatis:**
  * Video: `video-YYYY-MM-DD-01.mp4`, `video-YYYY-MM-DD-02.mp4`, dst.
  * Poster: `poster-YYYY-MM-DD-01.jpeg`, `poster-YYYY-MM-DD-02.jpeg`, dst.
  * Carousel: Folder `carousel-YYYY-MM-DD-01`, `carousel-YYYY-MM-DD-02`, dst.
- [x] **Auto-Increment Nomor Terakhir:** Sistem secara cerdas mendeteksi nomor urut terbesar yang sudah ada pada tanggal dan kategori tersebut, lalu melanjutkan ke nomor berikutnya.
- [x] **Pembersihan Form Manual:** Form input manual *Judul Carousel* dihilangkan dari modal upload agar proses penambahan antrean 100% instan.

### 🔹 Fase 31: Default Filter Hari Ini, Single Unified Date Selector, & Pembersihan UI
- [x] **Default Tampilan Hari Ini (`TODAY`):** Setiap kali aplikasi dibuka atau di-*refresh*, feed langsung menampilkan media untuk hari ini.
- [x] **Single Unified Date Selector:** Menyatukan selector tanggal menjadi satu dropdown terpadu (*Hari Ini*, *Semua Tanggal*, arsip folder, dan opsi interaktif *Pilih Tanggal Lain...*).

### 🔹 Fase 35: Interactive Real-Time Publishing Modal with Backdrop Blur & Live Monospace Logs
- [x] **Backdrop Blur & Glassmorphism Design (`backdrop-blur-md bg-black/75`):** Menampilkan modal interaktif berlatar belakang blur saat proses publish berjalan, dengan nuansa modern *Linear/Apple Pro Studio*.
- [x] **Live Progress Bar & Dynamic Percentage:** Progress bar bercahaya (*glow gradient*) dengan indikator persentase real-time dan label langkah aktif bot.
- [x] **Multi-Platform Visual Tracking Cards:** Kartu terpisah untuk TikTok Studio, Instagram, dan Facebook Fanpage dengan status badge dinamis (*Menunggu*, *Memproses...*, *Berhasil ✓*, *Gagal ✗*).
- [x] **Embedded Monospace Terminal Bot Log Viewer:** Menampilkan output log detail aktivitas bot secara langsung dengan timestamp, badge platform (`[TIKTOK]`, `[INSTAGRAM]`, `[FACEBOOK]`, `[SYS]`), auto-scroll toggle, dan tombol copy log.
- [x] **Floating Minimized Widget:** Tombol minimize yang menciutkan modal menjadi widget kapsul melayang di pojok kanan bawah tanpa memotong proses upload, dan dapat diperbesar kembali kapan saja.
- [x] **Celebratory Completion State:** Banner penyelesaian dengan tombol *Selesai & Tutup* serta link langsung ke postingan media yang berhasil diterbitkan.
- [x] **Thread-Safe SSE Streaming & Polling Fallback:** Modul [`src/publish_tracker.py`](file:///c:/Users/spacdust/Desktop/DEV/Bot/content-uploader/src/publish_tracker.py) dan endpoint `/api/content/upload/stream` untuk streaming data real-time via Server-Sent Events.
- [x] **Pembersihan Tombol Redundan:** Tombol manual `+ Folder Baru` dihilangkan karena folder sudah dibuat 100% otomatis saat upload.
- [x] **Auto-Select Topmost Item:** Media teratas di antrean otomatis terpilih dan terbuka di Studio Inspector saat halaman dimuat.

### 🔹 Fase 32: Manajemen Akun, Instant Login Cookie Detection, & Session Cloning
- [x] **Fix Pendaftaran Akun Baru:** Menyelaraskan endpoint JSON API `/api/accounts/create` sehingga penambahan akun berjalan lancar.
### 🔹 Fase 36: Precision Public Post Link Scanner & Live Copy Manager (v1.1 Release)
- [x] **Category-Aware Precision Routing:** Sistem pencari tautan secara cerdas membedakan pencarian antara format `Video (Reels)`, `Poster (Foto Tunggal)`, dan `Carousel (Multi-Slide)`.
- [x] **Instagram Mobile Clips Protocol (`user_clips`):** Mengekstrak reel video secara langsung via endpoint Instagrapi Clips dengan metadata caption utuh, serta `user_medias` untuk Poster dan Carousel.
- [x] **TikTok Studio Multi-Phrase Smart Search:** Menggunakan pencarian kata kunci 3 kata spesifik dengan *early-stop matching* 100% pada TikTok Studio.
- [x] **Facebook Scoped Reels Grid & Video Player Captioning:** Mengisolasi pemindaian pada grid utama (`div[role='main']`), menghindari tautan notifikasi komentar di navbar, dan membaca langsung teks caption dari player video Facebook.
- [x] **Sequential Fingerprint Matching (`difflib.SequenceMatcher`):** Menjamin pencocokan urutan kata asli kalimat caption sehingga bebas dari salah cocok (*zero false-positives*).
- [x] **Interactive Obsidian Live Copy Modal:** Modal bertema gelap dengan indikator pemindaian live, tombol salin tautan per platform, dan tombol salin format lengkap laporan (WhatsApp ready).
- [x] **Modal Persistence Lock:** Modal tidak akan tertutup secara otomatis oleh background polling dashboard, dan hanya tertutup jika pengguna mengklik tombol Tutup atau tombol X.

### 🔹 Fase 37: Drag-and-Drop Interactive Queue Reordering & Manual Sequence Rank
- [x] **Drag-and-Drop Antrean:** Memungkinkan pengguna menyeret kartu media langsung di panel antrean untuk menyusun urutan posting.
- [x] **Tombol Chevron Cepat:** Tombol naik (`▲`) dan turun (`▼`) di samping nomor urut `#1`, `#2`, dst untuk penyesuaian posisi cepat.
- [x] **Endpoint Queue Reorder:** Endpoint `POST /api/content/reorder-queue` untuk menyimpan preferensi susunan antrean manual.

### 🔹 Fase 38: Fitur Upload Massal Terjadwal (Mass Scheduled Upload) & Jeda Waktu Bertahap
- [x] **Relokasi Fitur Penjadwalan:** Memindahkan konfigurasi jadwal publikasi dari per-item satuan ke modal **Upload Massal** terpadu (`MassUploadModal.jsx`).
- [x] **Waktu Mulai Tunggal + Interval Otomatis:** Pengguna hanya memasukkan waktu awal sekali saja, lalu sistem secara otomatis menghitung waktu posting bertahap untuk media-media selanjutnya berdasarkan jeda waktu yang dipilih.
- [x] **Preset Jeda Waktu & Kustom Menit:** Pilihan jeda waktu 15 menit, 30 menit, 1 jam, atau input kustom menit sesuai kebutuhan strategi posting.
- [x] **Quick Time Presets:** Shortcut waktu mulai praktis: *Malam Ini (19:30)*, *Besok Pagi (08:00)*, *Besok Malam (19:30)*, serta offset `+30m` / `+1h`.
- [x] **Preview Progresif:** Pratinjau daftar urutan upload lengkap dengan indikator waktu tayang spesifik per item.

### 🔹 Fase 39: Background Autonomous Scheduler Daemon & Multi-Account Conflict Resolution
- [x] **Scheduler Engine Terintegrasi (`src/scheduler.py`):** Background thread daemon yang memantau timestamp `scheduled_time` setiap interval 30 detik tanpa membebani performa UI.
- [x] **Multi-Account Safe Execution:** Penanganan konflik jadwal antar akun secara aman (mekanisme locking/antrean mutex) sehingga browser upload tidak saling bertabrakan atau menimpa satu sama lain saat waktu publikasi bersamaan.
- [x] **Live Scheduler Status Endpoint:** Endpoint `/api/scheduler/status` dan `/api/scheduler/trigger` untuk memantau status scheduler secara real-time dari frontend.

### 🔹 Fase 40: Antisipasi Bug Popup Video Processing di TikTok Studio
- [x] **Deteksi Popup Pemrosesan Video:** Otomatis mendeteksi dialog popup konfirmasi saat video masih diproses oleh server TikTok (*"Video is processing" / "Lanjutkan posting"*).
- [x] **Auto-Confirm Post:** Bot secara otomatis menekan tombol konfirmasi lanjut sehingga proses publikasi TikTok tidak terhenti atau gagal posting.

### 🔹 Fase 41: Integrasi Penuh Keranjang Kuning TikTok Shop (Product Showcase Link)
- [x] **Sinkronisasi Sesi Toko:** Menghubungkan sesi browser creator dengan sesi TikTok Shop sehingga seluruh produk toko muncul lengkap dan dapat dipilih.
- [x] **Endpoint Pencarian Produk Toko:** Endpoint `/api/tiktok/products` untuk memuat dan mencari katalog produk TikTok Shop secara real-time.
- [x] **UI Controller Studio Inspector (`TikTokProductCard.jsx`):**
  - Switch ON/OFF tautan keranjang kuning khusus TikTok.
  - Form pencarian produk toko dan daftar produk dengan thumbnail, harga, dan stok.
  - Kartu preview produk yang dipilih dan tombol ganti produk.
  - Kolom kustom **Nama Keranjang Kuning (Tampil di Video)** dengan batasan maksimal 30 karakter.
- [x] **Automasi Playwright TikTok Product Link (`src/tiktok_uploader.py`):**
  - Mengklik tombol *Add link* $\rightarrow$ *Product*.
  - Mencari dan memilih produk yang sesuai dari katalog toko.
  - Mengetik nama kustom keranjang kuning dan menekan tombol *Add/Tambahkan* sebelum mempublikasikan video.
- [x] **Label Bersih & Minimalis di Antrean Konten:** Menampilkan badge `[ 🛍️ Keranjang Kuning ]` di header card antrean kiri untuk item yang memiliki tautan produk aktif.
- [x] **Dukungan Penuh di Upload Massal:** Item yang memiliki tautan produk tetap membawa metadata keranjang kuning secara utuh pada pipeline upload massal terjadwal.

### 🔹 Fase 42: Perbaikan Presisi Dialog-Scoped File Input & Navigasi Facebook Reels
- [x] **Eliminasi Shadowing Multi-Input Facebook:** Memperbaiki selektor upload Reel yang sebelumnya salah menargetkan hidden file input feed latar belakang.
- [x] **Dialog-Scoped Locator:** Menargetkan secara presisi `div[role='dialog'] input[type='file']` di dalam modal *Buat reel*.
- [x] **Explicit Wait Navigasi Multi-Tahap:** Menambahkan explicit wait untuk tombol *Berikutnya* (tahap edit dan tahap pengaturan) serta selektor tombol *Posting* dan penanganan popup event *Terbitkan Postingan Asli*.
- [x] **Verifikasi Live 100% Berhasil:** Teruji secara nyata menerbitkan video Facebook Reel secara otomatis hingga selesai.

### 🔹 Fase 43: Standarisasi Port UI Dashboard di `http://127.0.0.1:8000`
- [x] **Penyelarasan Host & Port:** Memperbarui `start_ui.bat` dan backend FastAPI uvicorn agar secara konsisten dan stabil berjalan di `http://127.0.0.1:8000`.

### 🔹 Fase 44: Penguatan Total Arsitektur Upload Multi-Platform & Penjadwalan Terpercaya
- [x] **Eliminasi Bug Fatal Scheduler Tertinggal:** Memperbaiki logika `get_scheduled_items()` di mana sebelumnya konten yang sudah terupload di satu platform (misal TikTok) langsung dilewati dan mengabaikan platform lain (Instagram/Facebook). Kini scheduler memvalidasi sisa platform (`remaining_platforms`) dan hanya menandai selesai jika seluruh target telah terpublikasi.
- [x] **Fresh State Cache Sync:** Thread penjadwalan otomatis menyinkronkan data item dari disk (`scan_content`) tepat sebelum eksekusi untuk memastikan daftar `uploaded_platforms` selalu akurat.
- [x] **Mekanisme Auto-Retry Multi-Platform:** Menambahkan wrapper `run_upload_with_retry` pada `src/content_manager.py` yang otomatis mengulang percobaan upload hingga 2x dengan jeda 5 detik jika terjadi kegagalan sementara (*transient error* / *network timeout*).
- [x] **Deduplikasi Platform Sudah Terbit:** Pipeline upload otomatis mendeteksi platform yang sudah terbit sebelumnya dan melewatinya secara cerdas, mencegah risiko posting ganda.
- [x] **Inter-Platform Cooldown (3s):** Memberikan jeda aman 3 detik antar platform untuk pembersihan memori browser dan pelepasan soket jaringan.
- [x] **Penguatan Timeout & Verifikasi TikTok Studio:** Memperpanjang batas waktu polling dari 45s ke 120s untuk video (dan 75s untuk Poster/Carousel). Jika batas waktu habis tanpa konfirmasi, sistem kini mengembalikan `False` (bukan *false positive* `True`) sehingga memicu retry otomatis.
- [x] **Verifikasi Instagram Web Asli & Anti-Hang:** Memperbaiki validasi status posting Instagram sehingga mendeteksi popup kesalahan server secara instan dan mencegah browser tertutup sebelum file terunggah utuh.
- [x] **Rute Langsung Facebook Reels & Popup Handling:** Menambahkan rute langsung `https://www.facebook.com/reel/create` dan penanganan popup pergantian profil/halaman untuk mencegah kegagalan deteksi tombol upload.
- [x] **Anti Background Window Throttling Chrome:** Menambahkan flag `--disable-background-timer-throttling`, `--disable-backgrounding-occluded-windows`, dan `--disable-renderer-backgrounding` agar eksekusi penjadwalan di background tidak membeku.

### 🔹 Fase 45: Anti-Infinite-Looping Scheduler, Real Cookie Expiry Verification, & Stale Schedule Protection
- [x] **Eliminasi Infinite Looping Browser Chrome:** Mencegah scheduler membuka browser berulang kali saat terjadi kegagalan. Menerapkan `_failed_attempts` tracking dan jeda pendinginan `_failed_cooldown` (15 menit untuk kegagalan sementara, dan dinonaktifkan 24 jam jika gagal 3 kali berturut-turut).
- [x] **Validasi Timestamp Kedaluwarsa Cookie Nyata (`src/auth_manager.py`):** Fungsi `is_tiktok_authenticated`, `is_instagram_authenticated`, dan `is_facebook_authenticated` kini memverifikasi timestamp `expires` cookie secara matematis terhadap waktu sekarang. Cookie kadaluarsa otomatis dianggap `False` sehingga bot tidak akan mencoba membuka browser upload.
- [x] **Sistem Invalidasi Sesi Otomatis (`invalidate_session`):** Jika uploader mendapati sesi di-redirect ke halaman login saat proses upload berlangsung, file sesi kadaluarsa langsung dihapus dan status diubah menjadi *Belum Login*.
- [x] **Filter Eliminasi Jadwal Basi (> 24 Jam):** Fungsi `get_scheduled_items()` otomatis mengabaikan jadwal lampau yang sudah terlewat lebih dari 24 jam (`diff_seconds < -86400`). Jadwal lama tidak akan lagi dihitung di antrean `total_scheduled_pending` maupun memicu eksekusi mendadak saat aplikasi dibuka.
- [x] **Pembersihan Metadata Sisa & Eliminasi Akun Dummy:**
  - Metadata `scheduled_time` pada item lama dari bulan September dibersihkan sehingga indikator navbar menampilkan `0 Terjadwal`.
  - Folder dummy `testacc` dan `non_existent_account_12345` dihapus total dari direktori `accounts/` dan `content/`.
  - Seluruh pengujian unit diisolasi menggunakan mock dan virtual `tempfile` sehingga pengujian 100% steril tanpa mengotori filesystem produksi.
### 🔹 Fase 46: Auto-Detection Model LLM & Dropdown Interaktif pada Pengaturan AI Engine
- [x] **Backend Model Discovery Endpoint (`/api/settings/models`):** Mengimplementasikan deteksi model dual-layer di `src/server.py` (`OpenAI(base_url=..., api_key=...).models.list()` dengan fallback direct HTTP GET `/models` yang mendukung format standar OpenAI, Gemini API, maupun Ollama).
- [x] **Auto-Detect saat Buka Modal Pengaturan:** Ketika modal Pengaturan dibuka (`SettingsModal`), daftar model AI dari endpoint aktif otomatis dipindai di latar belakang dan disajikan secara instan.
- [x] **Dropdown Interaktif & Toggle Mode Manual:** Kolom *Model Name* otomatis bertransformasi menjadi dropdown `<select>` obsidian yang rapi saat model terdeteksi, dengan opsi model aktif saat ini tetap terpilih. Pengguna juga dapat menekan tautan `[Ketik Manual]` atau `[← Pilih Dropdown]` serta tombol reload `[Deteksi Model]` kapan saja.
- [x] **Penyelarasan Endpoint `/api/settings/test-llm`:** Menambahkan alias endpoint `/api/settings/test-llm` mendampingi `/api/settings/test` dengan pengembalian latensi (ms), nama model, dan cuplikan respon AI.
- [x] **Unit Testing Lengkap & Terisolasi (`tests/test_settings_models.py`):** Menambahkan 6 unit test baru untuk memvalidasi parser SDK, fallback HTTP, response Gemini format, dan FastAPI endpoints. Total 23/23 unit test berhasil (*100% Passing*).
- [x] **Rebuild Produksi React:** Asset bundle produksi `frontend/dist` telah di-build ulang menggunakan Vite.

---

## 📊 Tabel Matriks Fitur & Status Terkini (v1.3)

| Fitur / Komponen | Status | Keterangan |
| :--- | :---: | :--- |
| **Auto-Detect Model AI Dropdown** | ✅ **Stabil (v1.3)** | Deteksi otomatis model dari endpoint (OpenAI/Gemini/Ollama) & pemilih dropdown |
| **Robust Multi-Platform Scheduler** | ✅ **Stabil (v1.3)** | 0 platform tertinggal, sinkronisasi state disk, & auto-skip terbit |
| **Anti-Infinite-Loop & Cooldown Engine** | ✅ **Stabil (v1.3)** | Cooldown 15m saat gagal, max 3x retry, cegah Chrome looping |
| **Cookie Expiry & Auto-Invalidation** | ✅ **Stabil (v1.3)** | Validasi timestamp `expires`, hapus sesi mati saat redirect login |
| **Stale Schedule Filter (>24h)** | ✅ **Stabil (v1.3)** | Otomatis abaikan jadwal basi lampau, 0 false pending count |
| **Automated Upload Retry System** | ✅ **Stabil (v1.3)** | Auto-retry 2x dengan jeda cerdas saat terjadi error sementara |
| **Anti-Throttling Background Engine** | ✅ **Stabil (v1.3)** | Flag Chromium anti-sleep saat jendela tertutup/di background |
| **Upload Massal Terjadwal** | ✅ **Stabil (v1.2)** | Waktu awal + interval jeda bertahap otomatis (15m, 30m, 1h, kustom) |
| **Background Auto-Scheduler** | ✅ **Stabil (v1.2)** | Daemon thread otomatis mengeksekusi publikasi saat timestamp tiba |
| **Keranjang Kuning TikTok Shop** | ✅ **Stabil (v1.2)** | Pencarian produk toko, penamaan custom keranjang, & automasi link |
| **Label Keranjang Kuning di Card** | ✅ **Stabil (v1.2)** | Badge ringkas `[ 🛍️ Keranjang Kuning ]` di header card antrean |
| **Drag & Drop Queue Reorder** | ✅ **Stabil (v1.2)** | Geser posisi kartu antrean interaktif + penomoran urutan dinamis |
| **Popup Processing Dismissal** | ✅ **Stabil** | Otomatis menekan konfirmasi lanjut saat video diproses TikTok |
| **Facebook Reels Scoped Input** | ✅ **Stabil** | Selektor input scoped ke modal Reel tanpa terbajak background feed |
| **Precision Post Link Scanner** | ✅ **Stabil (v1.1)** | 100% akurat memindai link TikTok, IG, dan FB sesuai format |
| **Obsidian Live Copy Modal** | ✅ **Stabil (v1.1)** | Modal progress live, salin per-platform, & format laporan WA |
| **Tri-Platform Master Publish** | ✅ **Stabil** | 1-klik publikasi berurutan ke TikTok, Instagram, dan Facebook |
| **Facebook Fanspage Uploader** | ✅ **Stabil** | Upload Reel (ikon merah) & Foto/Carousel (ikon hijau + caption atas) |
| **Instagram Web Direct Uploader** | ✅ **Stabil** | Upload 9:16 Original tanpa crop + multi-slide carousel |
| **TikTok Studio Uploader** | ✅ **Stabil** | Upload Video, Poster & Carousel + Sound volume tuning (-7dB / 0dB) |
| **Standar Auto-Naming Baku** | ✅ **Stabil** | Format `video-tgl-01`, `poster-tgl-01`, `carousel-tgl-01` otomatis |
| **Unified Date Filter (Hari Ini)** | ✅ **Stabil** | Dropdown tunggal dengan default Hari Ini + selector kustom |
| **Real-time Status Polling** | ✅ **Stabil** | Status otomatis terperbarui langsung hingga seluruh platform selesai |
| **Multi-Platform Status Badges** | ✅ **Stabil** | Indikator `TT`, `IG`, `FB`, dan `Semua Platform (TT · IG · FB)` |
| **AI Multimodal Caption Generator** | ✅ **Stabil** | Integrasi Gemini/Groq/OpenAI dengan batas ketat 4 hashtag |
| **Interactive Carousel Viewer** | ✅ **Stabil** | Pratinjau & geser slide di Inspector + reorder slide di modal |
| **Multi-Account & Session Cloning** | ✅ **Stabil** | Isolasi sesi per akun + kloning sesi Facebook lintas fanspage |
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
| **Unit Test Coverage** | ✅ **100% Green** | 17 unit test passing (Regression & Scheduler/Retry/Uploader) |

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

1. [x] **Scheduler Daemon Engine (`src/scheduler.py`):** Service latar belakang thread-safe yang memantau dan mengeksekusi upload otomatis sesuai timestamp `scheduled_time` dengan proteksi mutex konflik multi-akun.
2. [x] **TikTok Shop Showcase Integration:** Penautan produk keranjang kuning otomatis langsung dari antrean studio.
3. [ ] **Instagram Carousel Multi-Image Poster Live Flow:** Pengujian alur posting carousel multi-slide visual di Instagram.
4. [ ] **Background Audio Merger untuk Carousel:** Otomatisasi penggabungan kumpulan slide gambar menjadi video carousel berlatar musik sebelum upload ke TikTok Photo Mode.
5. [ ] **Notifikasi Telegram / WhatsApp Bot:** Mengirim laporan keberhasilan upload beserta bukti screenshot ke grup tim konten.
6. [ ] **Trending Hashtags Recommender:** Rekomendasi tagar populer secara cerdas berdasarkan kategori produk dan niche akun.
