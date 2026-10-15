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

### 🔹 Fase 47: Indikator & Feedback Transparan Pembuatan AI Caption Pasca-Upload
- [x] **Eliminasi Efek Tiba-Tiba pada Caption Baru:** Mengatasi masalah di mana caption muncul mendadak tanpa informasi bagi pengguna saat media baru diunggah.
- [x] **Active Auto-Caption Task Tracking (`src/server.py`):** Backend melacak status tugas pembuatan caption di thread latar belakang (`_active_auto_caption_tasks`) dan menyediakannya via atribut `is_generating_caption` pada endpoint `/api/content` dan respons upload `/api/content/upload-media`.
- [x] **Smart Auto-Select & Immediate Caption State (`useContent.js`):** Konten yang baru diunggah langsung otomatis terpilih di antrean dan ditandai dengan status `generatingCaption`. Polling pintar aktif setiap 2 detik hingga caption selesai dirumuskan.
- [x] **Visual Banner & Shimmer State di Studio Inspector (`CaptionEditorCard.jsx`):** Menampilkan banner notifikasi animasi elegan `[ ✨ Sedang membuat caption dengan AI... ]` tepat di atas textarea, serta placeholder dinamis `✨ AI sedang menyusun caption & rekomendasi hashtag...`.
- [x] **Badge Animasi di Antrean Feed (`ContentCard.jsx`):** Kartu konten di feed menampilkan badge header `[ ✨ AI Caption... ]` berkedip halus dan cuplikan teks `Sedang membuat caption dengan AI...` selama proses berlangsung.
- [x] **Toast Konfirmasi Penyelesaian:** Begitu AI selesai merumuskan caption, sistem memicu notifikasi sukses `✨ Caption AI untuk '...' selesai dibuat!` dan teks caption langsung terisi dengan mulus.

### 🔹 Fase 48: Eliminasi Native File Dialog Facebook & Modern Reel Composer Pipeline
- [x] **Investigasi Mendalam Bug Window File Picker Native:** Menemukan bahwa tombol `Reel` (`div[aria-label='Reel']`) dan `Foto/video` pada beranda Facebook memicu event file picker browser secara native. Mengklik tombol ini tanpa penanganan Playwright menyebabkan Windows membuka dialog native OS *"Select file to upload"*, yang membekukan Playwright dan menyebabkan proses upload massal video gagal.
- [x] **Native File Chooser Interceptor (`page.expect_file_chooser`):** Mengganti klik manual langsung dengan context manager Playwright `with page.expect_file_chooser() as fc_info: btn.click(force=True)` lalu menginjeksi file lewat `fc_info.value.set_files(...)`. Dialog native Windows 100% tercegat dan tidak pernah muncul di layar pengguna.
- [x] **Restrukturisasi Modal Composer Reel Modern:**
  - Menyesuaikan arsitektur dialog Reel Facebook terbaru yang terdiri dari tahap `Edit > Pengaturan`.
  - Mengisi deskripsi caption langsung pada tahap awal (`Edit`) di mana kolom *"Deskripsikan reel Anda..."* (`div[role='dialog'] div[role='textbox']`) berada.
  - Mengklik tombol *Berikutnya* sekali untuk masuk ke tahap `Pengaturan`, mengeliminasi pencarian tombol kedua yang redundan (menghemat waktu tunggu 15 detik).
  - Menekan tombol *Posting* biru di pojok bawah dialog `Pengaturan` dan memantau konfirmasi penerbitan serta popup dialog lanjutan.
- [x] **Proteksi Komprehensif Upload Standar (Foto/Poster/Carousel):** Menerapkan interseptor file chooser yang sama pada tombol `Foto/video` dengan fallback pembukaan dialog composer manual via `Apa yang Anda pikirkan`.
- [x] **Deteksi Sesi Expired Lebih Peka:** Memperluas deteksi sesi Facebook yang kedaluwarsa dengan mendeteksi elemen input password (`input[type='password']`) pada beranda, mencegah bot mencoba upload saat akun belum terautentikasi.
### 🔹 Fase 49: Fitur Multi-Upload Video & Poster Menjadi Item Reel Terpisah di Antrean
- [x] **Dukungan Multi-Selection pada Modal Upload (`AddMediaModal.jsx`):**
  - Input file kategori Video dan Poster kini mendukung atribut `multiple`, memungkinkan pengguna memilih banyak berkas sekaligus (misalnya memilih 5 video bersamaan).
  - Tampilan dinamis interaktif:
    - Jika memilih 1 video: menampilkan pratinjau player video mandiri lengkap dengan nama dan ukuran berkas.
    - Jika memilih banyak video (misalnya 5 file): menyajikan ringkasan kartu hijau `✨ 5 Video Dipilih (akan menjadi 5 Reel terpisah)`, tombol `+ Tambah Lagi`, tombol `Hapus Semua`, serta daftar kartu video terpilih dengan badge penomoran (`#1`, `#2`, dst.), thumbnail, ukuran berkas (MB), dan tombol hapus per-item.
  - Tombol submit cerdas dan informatif: menampilkan label dinamis `Tambahkan 5 Reel/Video Terpisah ke Antrean`.
- [x] **Backend Multi-File Ingestion Pipeline (`src/server.py`):**
  - Endpoint `/api/content/upload-media` diperbarui untuk memproses setiap file yang diunggah secara individual pada kategori `Video` dan `Poster`.
  - Masing-masing file otomatis diberi penomoran sekuensial yang rapi (`video-YYYY-MM-DD-01.mp4`, `video-YYYY-MM-DD-02.mp4`, dst.) melalui `ContentManager.get_next_item_name`.
  - Dibuatkan berkas metadata `.json` terpisah untuk setiap item dengan parameter default optimal (`sound_db: "-7"`, target platform `tiktok, instagram, facebook`).
  - Memicu tugas pembuatan caption AI multimodal latar belakang (`_trigger_background_auto_caption`) untuk masing-masing item secara paralel.
  - Mengembalikan daftar lengkap `filenames`, `item_keys`, dan total `count` ke frontend.
- [x] **Sinkronisasi State & Parallel Caption Polling (`useContent.js`):**
  - Mengelola `selectedMediaFiles` terintegrasi dengan upload pipeline.
  - Polling cerdas memantau pembuatan caption untuk seluruh item yang baru dibuat hingga selesai dan menampilkan toast konfirmasi.

### 🔹 Fase 50: Reset Total Status Upload Saat Konten Dihapus & Diunggah Ulang
- [x] **Akar Masalah Teridentifikasi & Tuntas Diperbaiki:**
  - Sebelumnya, riwayat publikasi item disimpan di `accounts/<account>/upload_history.json`. Ketika sebuah item dihapus di bot via `/api/content/delete`, hanya file fisik media/metadata yang dihapus, sedangkan entri `item_key` di `upload_history.json` tetap tertinggal.
  - Akibatnya, saat video baru diunggah ke slot nama/tanggal yang sama, status lamanya (`UPLOADED`) terbawa kembali dan bot menolak mengunggah karena menganggap konten sudah terbit di semua platform.
- [x] **Pembersihan Riwayat Saat Penghapusan (`ContentManager.delete_item`):**
  - Menambahkan method `remove_item_history(account_name, item_key)` yang menghapus jejak publikasi dari `upload_history.json` dan `queue_order.json`.
  - Fungsi `delete_item` kini otomatis memanggil `remove_item_history` untuk semua variasi kunci (termasuk normalisasi separator slash dan nama carousel).
- [x] **Pembersihan Otomatis Saat Unggah Ulang Media (`/api/content/upload-media`):**
  - Setiap kali file video, poster, atau carousel baru disimpan ke disk, backend langsung memanggil `remove_item_history` untuk kunci item tersebut sehingga berkas baru dijamin 100% berstatus `PENDING` dengan daftar platform terbit kosong.
- [x] **Auto-Pruning Entri Yatim Piatu pada `scan_content`:**
  - Saat antrean dipindai (`scan_content`), sistem mendeteksi entri di `upload_history.json` yang berkas fisiknya sudah tidak ada di disk (misal dihapus lewat Windows File Explorer) dan otomatis membersihkannya.
- [x] **Endpoint & Tombol Manual Reset Status (`/api/content/reset-status`):**
  - Menambahkan endpoint `POST /api/content/reset-status` untuk mereset status konten kembali ke `PENDING` kapan saja tanpa perlu menghapus berkas media.
  - Menambahkan tombol interaktif `[ ↺ Reset Status ]` pada banner status publikasi di Studio Inspector (`PublishActionCenter.jsx`) yang aktif saat item memiliki status terbit.
- [x] **Unit Testing Lengkap & Verifikasi Penuh (`tests/test_reset_upload_status.py`):**
  - Menguji alur hapus item $\rightarrow$ re-upload berstatus `PENDING`, auto-pruning entri yatim piatu, fungsi `reset_item_status`, endpoint `/api/content/reset-status`, dan upload media baru.
  - 35/35 unit test passing (100% OK).
- [x] **Unit & Integration Testing Komprehensif (`tests/test_multi_video_upload.py`):**
  - Menguji upload 5 video menghasilkan 5 file video dan 5 file metadata JSON terpisah dengan sekuens penomoran baku.
  - Menguji `ContentManager.scan_content` memuat kelima item secara individual.
  - Memverifikasi single-upload dan multi-poster tetap berjalan sempurna tanpa regresi.
  - Seluruh 30 unit test suite lulus 100% (*30/30 OK*).
- [x] **Rebuild Bundle Frontend:** Asset produksi React Vite telah di-build ulang (`npm run build`).

### 🔹 Fase 51: Pencegahan Ghost Scheduled Spikes & Stricter Due Window pada Auto-Scheduler
- [x] **Akar Masalah Teridentifikasi & Analisis Kejadian:**
  - Kemarin (9 Oktober), terdapat 50 video di akun Shift & Co. yang dijadwalkan dan sukses diposting ke Instagram & Facebook. Karena kemarin TikTok belum terhubung, target TikTok belum terunggah dan nilai `scheduled_time` lama tertinggal di metadata `.json`.
  - Ketika pengguna melakukan login TikTok Shift & Co. hari ini (10 Oktober), `remaining_platforms` mendadak menyertakan TikTok untuk ke-50 video tersebut.
  - Karena aturan lama `AutoScheduler` menggunakan rentang kedaluwarsa 24 jam (`diff_seconds < -86400`), jadwal kemarin (~21 jam lalu) dianggap **AKTIF & JATUH TEMPO SAAT INI JUGA (`is_due: True`)**, memicu badge navbar `50 Terjadwal` dan membuka jendela Chrome otomatis untuk upload massal.
- [x] **Logika Toleransi Jadwal Presisi (Stricter Due Window & Past-Date Elimination):**
  - Jadwal dari tanggal lampau (`sched_dt.date() < now.date()`) atau yang terlambat lebih dari 30 menit (`diff_seconds < -1800`) kini **100% DIANGGAP KEDALUWARSA (EXPIRED)**.
  - Scheduler hanya mengeksekusi item yang jatuh tempo pada hari ini dengan toleransi maksimal 30 menit (`0 >= diff_seconds >= -1800` & `sched_dt.date() == now.date()`).
- [x] **Auto-Sanitasi & Pembersihan `scheduled_time` Pasca-Eksekusi:**
  - Menambahkan method `_clear_item_scheduled_time()` yang otomatis membersihkan `scheduled_time` dari file `.json` metadata setelah konten berhasil dipublikasikan oleh scheduler, maupun saat jadwal lampau terdeteksi kadaluarsa.
  - Membersihkan 59 sisa jadwal hantu lampau di `Shift & Co.` sehingga antrean terjadwal kembali bersih (`0 Terjadwal`).
- [x] **Unit Testing Diperbarui (`tests/test_scheduler_retry.py`):**
  - Menguji jadwal kemarin dan keterlambatan > 30 menit hari ini tidak dimasukkan ke antrean aktif dan tidak memicu eksekusi otomatis. Seluruh 35 unit test lulus 100% (*35/35 OK*).

### 🔹 Fase 52: Switch ON/OFF Platform Penjadwalan & Default Audio Mode "No Sound"
- [x] **Switch ON/OFF Platform Fleksibel pada Modal Penjadwalan (`MassUploadModal.jsx`):**
  - Menambahkan kontrol selektif 3 platform (**TikTok Studio**, **Instagram**, dan **Facebook Fanspage**) dengan komponen switch toggle iOS/Tailwind interaktif.
  - Pengguna dapat bebas memilih mau upload ke platform mana saja (misal hanya TikTok, atau hanya IG + FB).
  - Terdapat validasi protektif cerdas (*minimal 1 platform harus tetap aktif*) agar antrean tidak kosong tanpa tujuan.
  - Pilihan platform diteruskan ke API backend `/api/content/batch-schedule` dan tersimpan langsung ke `meta.json` (`platforms: ["tiktok", "instagram", "facebook"]`).
  - Scheduler dan engine publish secara ketat menghormati filter `platforms` dari metadata sehingga platform yang di-switch OFF tidak akan dibuka maupun diproses oleh browser bot.
- [x] **Default Mode Audio TikTok ke "No Sound" (`none`):**
  - Mengubah nilai default mode audio TikTok saat upload video/poster/carousel baru dari yang sebelumnya `"favorite"` menjadi **`"none"` ("No Sound")**.
  - Panel Studio Inspector (`TikTokSoundCard.jsx`) kini secara default menampilkan opsi segmented **"No Sound"** terpilih.
  - Backend `ContentManager` dan endpoint FastAPI `/api/content/upload-media` serta `/api/content/caption/save` otomatis menginisialisasi `sound_mode: "none"`.
  - Jika pengguna tetap ingin menggunakan suara, mereka dapat beralih ke tombol `Favorite` atau `Search Sound` kapan saja di panel inspector.
- [x] **Pengujian & Unit Testing Komprehensif:**
  - Dibuat unit test otomatis di `tests/test_platform_switch_and_sound_mode.py`.
  - Seluruh 38/38 unit test pada test suite lulus 100% (*Ran 38 tests in 3.574s, OK*).
  - Bundle frontend berhasil dikompilasi ulang dengan Vite (`npm run build`).

### 🔹 Fase 53: Auto-Dismiss Popup "Aktifkan Pemeriksaan Konten Otomatis" di TikTok Studio
- [x] **Akar Masalah Teridentifikasi & Analisis Kejadian:**
  - Saat file video selesai di-inject ke TikTok Studio, TikTok menampilkan dialog baru: *"Aktifkan pemeriksaan konten otomatis?"* dengan checkbox *"Pemeriksaan hak cipta musik"* dan tombol *"Aktifkan"* / *"Batal"*.
  - Di `src/tiktok_uploader.py`, fungsi `dismiss_popups` memiliki proteksi modal konfirmasi posting `is_post_dialog_open` yang sebelumnya mengecek frasa umum `t.includes('hak cipta')` dan `t.includes('proses')`.
  - Karena popup baru ini memuat kata "hak cipta", `dismiss_popups` salah mengidentifikasinya sebagai modal konfirmasi post akhir ("Post anyway"). Akibatnya, `dismiss_popups` langsung `return` tanpa menutup dialog.
  - Modal overlay tetap menutupi layar, menghalangi input caption dan tombol Post sehingga bot mengalami stuck.
- [x] **Solusi & Penanganan Khusus Modal Pemeriksaan Konten:**
  - Ditambahkan penanganan khusus dialog *"Aktifkan pemeriksaan konten otomatis?"* / *"Turn on automatic content checks"*:
    1. Mencari tombol primer **"Aktifkan"** (atau "Turn on" / "Enable") dan langsung menekannya untuk mengaktifkan perlindungan resmi TikTok sekaligus menutup dialog.
    2. Fallback otomatis ke tombol **"Batal"** / **"Cancel"**, tombol icon Close "X", `Escape`, atau pembersihan DOM overlay jika tombol tidak merespon.
  - Memperbaiki proteksi `is_post_dialog_open` agar **hanya** aktif pada modal konfirmasi posting sesungguhnya yang memuat frasa eksplisit (`post anyway`, `tetap posting`, `posting sekarang`, `post now`) dan secara eksplisit mengecualikan modal pemeriksaan konten otomatis.
  - Memastikan pemanggilan `self.dismiss_popups(page)` dieksekusi sebelum pengisian caption dan sebelum penekanan tombol Post.
- [x] **Unit Testing & Verifikasi:**
  - Dibuat unit test baru di `tests/test_tiktok_content_check_modal.py`.
  - Seluruh 40/40 unit test pada sistem lulus 100% (*Ran 40 tests in 3.816s, OK*).

- [x] **Fase 54: Perbaikan UX Tombol Master Publish Inspector & Sinkronisasi Status Terbit Selesai**
  - **Latar Belakang & Investigasi Mendalam:**
    - Pengguna bertanya: *"aku upload pake tombol ini eror ya? belum di update kah metodenya"* saat menekan tombol master hijau *"Publish to TikTok & Instagram & Facebook"* di panel Studio Inspector.
    - Berdasarkan hasil audit log sesi (`logs/sessions/pub_1791600926758.json`, `pub_1791600716317.json`, `pub_1791601045919.json`) serta file riwayat `upload_history.json`, ditemukan bahwa video tersebut (`video-2026-10-10-01.mp4` pada akun Shift & Co.) **SUDAH 100% SUKSES TERBIT DI KETIGA PLATFORM**:
      - TikTok: Sukses terbit pukul 09:56:15 WIB.
      - Instagram: Sukses terbit pukul 09:53:47 WIB.
      - Facebook Fanspage: Sukses terbit pukul 09:58:16 WIB.
    - Pada backend (`src/content_manager.py`), bot sengaja melewati (*skip*) proses upload jika seluruh platform target sudah terbit guna melindungi pengguna agar tidak terjadi duplikasi video di feed.
    - Namun pada frontend sebelumnya, tombol master tetap berwarna hijau aktif dan bertuliskan *"Publish to TikTok & Instagram & Facebook"*, sehingga ketika diklik tidak ada browser yang dibuka dan membuat pengguna mengira tombol tersebut error atau metodenya belum diperbarui.
  - **Solusi & Peningkatan UX yang Diimplementasikan:**
    1. **Teks & Status Tombol Master Dinamis:**
       - Menghitung sisa platform yang belum terbit (`remainingPlatforms`) terhadap platform yang terhubung aktif di akun saat ini (`connectedPlatforms`).
       - **Jika Semua Sudah Terbit (`isAllConnectedUploaded`):**
         - Tombol master berganti tampilan menjadi **Completed State**: *"Semua Platform Sudah Terbit (Selesai)"* dengan ikon `CheckCircle2` hijau emerald.
         - Disediakan tombol aksi 1-klik di bawahnya: **`[Reset & Upload Ulang Semua Platform]`** (ikon `RotateCcw` amber) yang otomatis mereset riwayat dan memicu upload baru ke semua platform tanpa kebingungan.
         - Catatan keterangan informatif: *"✓ Konten ini sudah terposting di seluruh platform. Bot otomatis melewatinya agar tidak duplikat."*
       - **Jika Terbit Parsial (e.g. TikTok & IG sudah, FB belum):**
         - Tombol master secara transparan hanya menampilkan platform yang tersisa: *"Lanjutkan Publish ke Facebook"* (bukan lagi menampilkan semua).
         - Catatan keterangan: *"ℹ️ Platform yang sudah terbit (TikTok, Instagram) otomatis dilewati."*
       - **Jika Belum Terbit Sama Sekali:**
         - Tombol menampilkan *"Publish to TikTok & Instagram & Facebook"*.
    2. **Sinkronisasi Hook `useContent.js`:**
       - Variabel `publishBtnText` kini reaktif memperhitungkan status `uploaded_platforms` dari item yang sedang dipilih di inspector.
    3. **Verifikasi:**
       - Bundle frontend berhasil dibuild ulang dengan `npm run build` (vite v6.4.3).
       - Seluruh 40 unit test regression lulus 100% (*Ran 40 tests in 11.249s, OK*).

- [x] **Fase 55: Pembebasan Tombol Upload Massal untuk Konten Parsial & Tanggal Lampau**
  - **Latar Belakang Masalah:**
    - Pengguna meminta: *"tolong fitur upload massal bisa dipake lagi, jangan disable soalnya aku ingin upload tiktok yg tanggal kemarin"*.
    - Pada konten tanggal kemarin (`2026-10-09`), seluruh 50 video sudah terbit di Instagram dan Facebook, tetapi **belum pernah diupload ke TikTok** (`uploaded_platforms: ['instagram', 'facebook']`).
    - Namun, tombol *"Upload Massal"* di `FeedFilterBar.jsx` sebelumnya menjadi `disabled` (berwarna abu-abu redup dan tidak bisa diklik) karena sistem menghitung `unuploadedSortedItems` secara kaku dengan syarat `uploaded.length === 0`. Konten yang sudah terbit di salah satu platform langsung diabaikan dari antrean massal.
  - **Perbaikan yang Diterapkan:**
    1. **Logika Kelayakan Upload Massal yang Akurat (`useContent.js`):**
       - Konten kini dianggap pending jika masih ada platform terhubung aktif yang belum diupload (misalnya TikTok belum diupload meskipun IG dan FB sudah).
       - `unuploadedSortedItems` mendeteksi kebutuhan upload per-platform (`tiktokNeeded`, `instagramNeeded`, `facebookNeeded`).
       - `massUploadQueue` memprioritaskan item pending, dan otomatis fallback ke seluruh item terfilter (`sortedItems`) jika pengguna ingin menjadwalkan atau memposting ulang konten yang sudah terbit.
    2. **Pembebasan Tombol Upload Massal (`FeedFilterBar.jsx` & `App.jsx`):**
       - Tombol *"Upload Massal"* tidak lagi disable selama terdapat konten di tampilan feed (`totalItemsCount > 0` atau `unuploadedCount > 0`).
       - Counter badge menampilkan jumlah item yang siap diproses.
    3. **Filter Status yang Selaras:**
       - Filter `PENDING` di toolbar kini menampilkan seluruh konten yang belum 100% selesai di semua platform aktif (tidak lagi menyembunyikan konten terbit parsial).
    4. **Verifikasi & Build:**
       - Bundle frontend berhasil dikompilasi via `npm run build` (`vite v6.4.3`).
       - Seluruh 40/40 unit test lulus (`Ran 40 tests in 9.997s, OK`).

- [x] **Fase 56: Perbaikan Bug Switch Platform yang Reset Sendiri Menjadi ON (Modal State Stability)**
  - **Latar Belakang & Gejala:**
    - Pengguna melaporkan: *"loh kok switch nya eror, udah ku matiin, malah on lagi"* sambil melampirkan screenshot selector 3 platform pada modal massal.
    - Ketika switch Instagram atau Facebook dimatikan oleh pengguna, dalam hitungan 1-2 detik switch tersebut tiba-tiba kembali menyala (*ON*) dengan sendirinya.
  - **Investigasi & Akar Masalah:**
    - Pada `MassUploadModal.jsx`, terdapat `useEffect` sinkronisasi `[isOpen, activePlatforms]` yang mengeksekusi `setSelectedPlatforms(supported)` (semua 3 platform aktif).
    - Pada `useContent.js`, array `activePlatforms` sebelumnya didefinisikan sebagai array baru pada setiap siklus render (bukan `useMemo`).
    - Akibatnya, setiap kali background timer polling (interval 1.5s - 5s) atau event focus berjalan di dashboard, referensi array `activePlatforms` berubah -> memicu `useEffect` di modal -> menimpa state `selectedPlatforms` kembali ke default 3 platform menyala.
  - **Solusi yang Diterapkan:**
    1. **Isolasi Inisialisasi Modal via Ref (`MassUploadModal.jsx`):**
       - Menambahkan `prevIsOpenRef` agar inisialisasi platform dan default schedule **HANYA berjalan tepat 1x saat modal pertama kali bertransisi dari closed ke open** (`isOpen && !prevIsOpenRef.current`).
       - Selama modal terbuka, perubahan state switch murni dikendalikan oleh interaksi pengguna tanpa risiko tertimpa polling latar belakang.
    2. **Memoize `activePlatforms` (`useContent.js`):**
       - Membungkus komputasi `activePlatforms` dengan `useMemo` berbasis dependensi status akun (`tiktok_active`, `instagram_active`, `facebook_active`).
    3. **Verifikasi & Build:**
       - Bundle frontend berhasil dikompilasi via `npm run build` (`vite v6.4.3`).
       - Seluruh 40/40 unit test lulus (`Ran 40 tests in 4.286s, OK`).

- [x] **Fase 57: Penanganan & Panduan Keranjang Kuning Kosong (Toko Saya vs Produk Etalase)**
  - **Latar Belakang & Gejala:**
    - Pengguna bertanya: *"kira kira kenapa ya, pas di tools ada list keranjang kuning, pas proses upload malah ga muncul"* sambil melampirkan 2 screenshot:
      1. Modal TikTok Studio: *"Tidak ada produk di etalase Anda. Buka aplikasi TikTok > Profil > TikTok Shop untuk menambahkan produk ke etalase Anda."*
      2. Dashboard Studio: Produk terdaftar dengan status *"Toko Saya"*.
  - **Analisis Mendalam & Akar Masalah:**
    - Di **Dashboard Tools**, API backend (`/api/tiktok/products`) memanggil endpoint Seller Center (`streamer_desktop/selection/search`) yang membaca database produk toko secara langsung (*Toko Saya*).
    - Di **TikTok Studio Web**, antarmuka upload hanya membaca produk yang sudah dimasukkan ke dalam **"Produk etalase" (Showcase)** profil kreator.
    - Pada akun TikTok kreator/pemasaran, produk dari toko tidak otomatis tampil di etalase profil jika belum ditambahkan secara manual melalui aplikasi TikTok di HP (*Profil > TikTok Shop > Tambah Produk ke Etalase*).
  - **Peningkatan Bot (`src/tiktok_uploader.py`):**
    - Menambahkan deteksi otomatis teks *"Tidak ada produk di etalase Anda"* / *"No products in your showcase"*.
    - Memberikan log peringatan jelas ke `PublishTracker`.
    - Otomatis menekan tombol *"Batal"* pada modal kosong agar proses upload video tidak stuck atau terhalang dialog di layar.
  - **Verifikasi:**
    - Seluruh 40/40 unit test lulus 100% (`Ran 40 tests in 2.797s, OK`).

- [x] **Fase 58: Manajemen Antrean Jadwal Terbuka & Pembatalan Jadwal 1-Klik**
  - **Pembersihan Jadwal Aktif Shift & Co.:**
    - Sebanyak 10 video pada akun Shift & Co. (`video-2026-10-15-01.mp4` s/d `video-2026-10-15-10.mp4`) berhasil dihapus jadwalnya secara instan (`scheduled_time` disetel ke `None`). Total antrean scheduler kembali bersih (0 pending).
  - **Interaktivitas Badge Jadwal Navbar (`Navbar.jsx`):**
    - Pill `[ 📅 X Terjadwal ]` di header studio kini interaktif (*clickable*) dengan kursor pointer dan efek hover transisi halus.
    - Saat ada jadwal aktif, tampil warna hijau emerald lengkap dengan ping animasi live dan counter. Saat 0 jadwal, tampil dalam format gelap zinc `[ 📅 0 Terjadwal ]` yang tetap dapat diklik kapan saja untuk membuka modal antrean.
  - **Modal Detail Antrean & Pembatalan (`ScheduledQueueModal.jsx`):**
    - Menampilkan seluruh postingan yang sedang mengantre rilis otomatis lengkap dengan thumbnail/preview, nama file, tanggal folder, waktu tayang WIB, hitung mundur relatif (*countdown*), dan platform tujuan (TikTok, Instagram, Facebook).
    - Filter dropdown/pill akun (*Semua Akun*, *Shift & Co.*, dll) serta kotak pencarian instan (*search query*).
    - **Aksi Batal Per-Item:** Tombol *"Batalkan Jadwal"* pada tiap baris konten untuk membatalkan jadwal secara spesifik tanpa mengganggu postingan lain.
    - **Aksi Batal Massal:** Tombol *"Batalkan Semua Jadwal"* di footer modal yang dilengkapi dialog konfirmasi aman (*safety confirmation*) untuk mereset seluruh jadwal sekaligus.
  - **Backend & AutoScheduler API Enhancements:**
    - Endpoint `/api/content/batch-clear-schedule` disempurnakan untuk mendukung pembatalan per item berbasis akun masing-masing serta pembersihan massal `account = "all"`.
    - Endpoint `/api/scheduler/status` (`AutoScheduler.get_status()`) diperkaya untuk mengembalikan properti queue mendalam (`item_key`, `date`, `remaining_platforms`, `media_url`, dan preview `caption`) tanpa batasan kuota 10 item.
  - **Verifikasi & Kualitas Kode:**
    - Penambahan 2 unit test baru di `tests/test_scheduler_retry.py` (`test_scheduler_get_status_rich_upcoming_queue` dan `test_batch_clear_schedule_single_item`).
    - Seluruh 42 unit test lulus 100% (`Ran 42 tests in 3.573s, OK`).
    - Bundle frontend produksi Vite berhasil dikompilasi ulang (`npm run build`).

- [x] **Fase 59: Pencarian Presisi & Smart Multi-Criteria Matching Keranjang Kuning TikTok**
  - **Latar Belakang & Gejala:**
    - Pengguna bertanya: *"aku kan memilih varian ini, kenapa pas pemilihan keranjang kuning dia tidak search yg sama persisi judulnya, jadinya ada paket serupa 2 botol yg kepilih (salah)"*.
  - **Akar Masalah Teridentifikasi:**
    1. *Pemotongan Keyword Terlalu Pendek:* Logika sebelumnya memakai `prod_title.split("-")[0].strip()`. Pada judul produk Shift & Co. (`Inspired by Danhil Blu - Shift & CO. Parfum...`), ini memotong kata kunci menjadi hanya `"Inspired by Danhil Blu"`, membuang identitas merek dan penjelas varian.
    2. *Ketiadaan Pencocokan Baris & Fallback Buta:* Pencocokan baris sebelumnya mencari teks `prod_id`. Karena TikTok Studio tidak menampilkan numeric ID produk di teks baris antarmuka, pencarian ID selalu nihil dan bot langsung jatuh ke fallback buta: `radio = page.locator(".TUXRadio").first` (memilih baris radio pertama di hasil pencarian). Jika produk urutan pertama adalah "Paket 2 Botol", paket 2 botol itulah yang salah terpilih.
  - **Solusi & Peningkatan Bot (`src/tiktok_uploader.py`):**
    1. *Pencarian Judul Spesifik:* Kata kunci pencarian kini menggunakan judul spesifik hingga 60 karakter di batas kata terdekat (`clean_title[:60]`) tanpa memotong di tanda `-`. Jika pencarian panjang tidak ada hasil, bot memiliki fallback otomatis ke varian utama.
    2. *Smart Multi-Criteria Evaluator:* Menambahkan algoritma pembobotan cerdas (*scoring*) di browser context untuk mengevaluasi seluruh baris radio produk:
       - **Kesesuaian Harga (+400 poin):** Mencocokkan `format_price` (misal Rp40.500). Paket 2 botol yang harganya Rp75.000/Rp80.000 otomatis tersingkir.
       - **Kesesuaian Gambar Cover (+800 poin):** Mencocokkan URL hash gambar sampul produk.
       - **Kesesuaian Kata Kunci Judul (+500 poin & 25-char prefix +300 poin):** Menghitung persentase overlap kata penting antara judul target dan teks baris.
       - **Negative Variant Penalty (-900 poin):** Jika target adalah 1 botol tetapi baris memuat teks "2 botol" / "paket 2" / "bundle 2" / "isi 2", baris tersebut mendapat penalti -900 poin sehingga mustahil terpilih secara keliru.
  - **Verifikasi:**
    - Dibuat unit test baru di `tests/test_tiktok_content_check_modal.py` (`test_apply_tiktok_product_link_smart_selection`).
    - Seluruh 43/43 unit test lulus 100% (`Ran 43 tests in 3.407s, OK`).

---

## 📊 Tabel Matriks Fitur & Status Terkini (v1.4)

| Fitur / Komponen | Status | Keterangan |
| :--- | :---: | :--- |
| **Switch Platform Jadwal (TikTok/IG/FB)** | ✅ **Stabil (v1.4)** | Pilih target platform bebas dengan switch toggle ON/OFF pada modal penjadwalan |
| **Default Audio Mode "No Sound"** | ✅ **Stabil (v1.4)** | Default sound mode TikTok disetel ke "No Sound" (`none`) saat upload konten baru |
| **Multi-Video Upload (Separate Reels)** | ✅ **Stabil (v1.3)** | Pilih banyak video sekaligus (misal 5 file), otomatis menjadi 5 Reel terpisah |
| **Native File Chooser Interceptor** | ✅ **Stabil (v1.3)** | Cegat native file dialog OS Windows pada Facebook Reel & Post |
| **Transparan Auto-Caption Feedback** | ✅ **Stabil (v1.3)** | Indikator live banner & badge saat AI sedang menyusun caption pasca-upload |
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
