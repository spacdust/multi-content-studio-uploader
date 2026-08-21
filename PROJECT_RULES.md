# 📜 ATURAN PENGEMBANGAN PROYEK (DEVELOPMENT RULES)

Dokumen ini berisi aturan ketat yang **WAJIB** dipatuhi oleh asisten AI / agen selama pengembangan proyek ini:

---

### ⚠️ 1. Aturan Git Push (SANGAT KETAT)
> **DILARANG KERAS** menjalankan perintah `git push` (ke remote GitHub/origin) secara otomatis setelah membuat atau mengedit kode.
> 
> * **Aturan:** `git push` **HANYA** boleh dijalankan jika dan hanya jika **USER secara eksplisit memberikan perintah langsung** (misalnya: *"tolong push ke github"*, *"push sekarang"*, dll).
> * Untuk perubahan kode biasa: Cukup buat, edit, uji secara lokal, dan jangan lakukan `git push` tanpa izin langsung.

---

### 🛡️ 2. Aturan Keamanan & Zero-Leak
> **DILARANG KERAS** men-stage atau meng-commit file kredensial, berkas sesi login (`*_state.json`, `*instagrapi_session.json`, `*account_info.json`), file `.env`, file log gambar screenshot (`logs/*.png`), serta video/foto pribadi milik pengguna (`content/*`).
> Pastikan `.gitignore` selalu dipatuhi secara ketat.

---

### 🧪 3. Aturan Validasi Lokal
> Sebelum memberikan konfirmasi penyelesaian tugas ke pengguna:
> 1. Jalankan `npm run build` di folder `frontend/` untuk memastikan tidak ada error sintaksis/bundling.
> 2. Jalankan `python -m unittest discover tests` untuk memastikan semua unit test backend lulus (*passed*).
