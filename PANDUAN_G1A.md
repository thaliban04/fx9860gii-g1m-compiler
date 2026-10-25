# 🎨 PANDUAN PENGEMBANGAN ADD-IN GUI CASIO (.G1A)
### Casio fx-9860G / fx-9860GII / fx-9860G SD / fx-9750GII (Modded)

---

## 🌟 1. Mengapa Beralih ke Format Add-in (.G1A)?

Format **`.g1a`** adalah format aplikasi resmi (*native binary add-in*) untuk kalkulator grafik Casio seri **fx-9860G**, berbeda jauh dengan skrip `.g1m` Casio BASIC biasa:

| Fitur | Program Biasa (`.G1M`) | Add-In Native GUI (`.G1A`) |
| :--- | :--- | :--- |
| **Lokasi di Kalkulator** | Tersembunyi di dalam menu `PRGM` | **Langsung muncul di MAIN MENU** kalkulator (sejajar dengan menu RUN, STAT, GRAPH)! |
| **Ikon Aplikasi** | Tidak ada ikon | **Memiliki ikon 30×17 pixel kustom** di layar carousel utama! |
| **Antarmuka (UI)** | Teks baris 21×8 karakter kaku | **Grafis Penuh 128×64 LCD**: Windows, Kotak Dialog, Garis, Tabel, Chart, dan Tombol Fungsi F1–F6! |
| **Kecepatan Eksekusi** | Bytecode lambat diinterpretasikan | **Native Renesas SuperH (SH-4A) 32-bit @ 29MHz** (instan tanpa jeda)! |
| **Cara Pasang ke Kalkulator** | Butuh software jadul FA-124 / protokol USB serial | **Sangat Mudah: Drag & Drop via Flashdisk USB (Mode F1)**! Tidak butuh FA-124 atau driver khusus! |

---

## 🚀 2. Cara Pasang .G1A ke Kalkulator (Hanya 15 Detik!)

Pemasangan berkas `.g1a` ke kalkulator fx-9860GII **sangat praktis dan tidak membutuhkan aplikasi FA-124**:

1. **Hubungkan Kalkulator ke Komputer:**
   - Gunakan kabel USB mini-B standar.
2. **Pilih Mode USB Flash di Kalkulator:**
   - Pada layar kalkulator akan muncul menu *Select Connection Mode*:
   - **Tekan tombol `F1` (USB Flash / Flash Disk)**.
3. **Kalkulator Terbaca sebagai Flashdisk di PC:**
   - Buka **This PC / File Explorer** di Windows Anda.
   - Anda akan melihat drive baru bernama **`CASIO`** atau Drive Removable (misal: `E:\` atau `F:\`).
4. **Salin Berkas .G1A:**
   - Cukup **drag & drop** (salin) berkas `.g1a` hasil kompilasi langsung ke dalam drive kalkulator tersebut.
5. **Selesai!**
   - Cabut kabel USB.
   - Buka **MAIN MENU** di kalkulator — Add-in Anda sudah terpasang dengan ikon dan antarmuka GUI lengkap!

---

## 🛠️ 3. Cara Menggunakan Studio GUI di Proyek Ini

Kami telah menyediakan dua cara mudah untuk merancang dan mengompilasi Add-in `.g1a`:

### A. Menggunakan Web Studio (`index.html`)
1. Buka berkas `index.html` di browser (atau klik ganda `BUKA_WEB_STUDIO.bat`).
2. Klik tab **"🎨 Add-in GUI (.G1A)"** di panel kanan.
3. Anda akan melihat:
   - **Pratinjau Layar 128×64 LCD Real-time**: Menampilkan tampilan aplikasi secara persis seperti di layar fisik kalkulator.
   - **Desainer Ikon 30×17 Pixel**: Anda bisa menggambar ikon menggunakan mouse (pensil/penghapus/invert) atau memilih preset instan (Kalkulator, Grafik, Rumus, Game, Utilitas).
   - **Editor Skrip GUI**: Ubah judul, baris teks, atau label tombol F1–F6.
4. Klik tombol hijau **"⚡ Compile & Unduh .G1A"**.
   - Berkas `.g1a` langsung dikompilasi secara instan oleh browser dan diunduh ke komputer Anda!

### B. Menggunakan Desktop IDE (`gui.py`)
1. Jalankan `BUKA_DESKTOP_GUI.bat` atau ketik `python gui.py`.
2. Klik tombol ungu **"🎨 Add-in GUI (.G1A)"** pada bilah atas.
3. Jendela Studio Desainer Add-in akan terbuka:
   - Terdapat **Deteksi Drive Otomatis**: Jika kalkulator terhubung dalam mode F1, tombol **"🚀 Salin ke Kalkulator"** akan aktif, sehingga Anda bisa mentransfer berkas dalam 1 klik saja!
4. Anda juga bisa menyimpan berkas ke folder mana pun melalui tombol **"⚡ Compile & Simpan .G1A"**.

### C. Menggunakan Baris Perintah (CLI `g1a_builder.py`)
```bash
# Kompilasi skrip GUI menjadi berkas .g1a
python g1a_builder.py build examples/TOMLIN_GUI.txt -o output/TOMLIN.g1a

# Memeriksa dan memvalidasi struktur berkas .g1a
python g1a_builder.py inspect output/TOMLIN.g1a

# Melihat daftar drive kalkulator yang terhubung
python g1a_builder.py drives

# Mengirim langsung ke kalkulator via USB Flash
python g1a_builder.py send output/TOMLIN.g1a

# Menghasilkan kode sumber C murni (main.c)
python g1a_builder.py make-c examples/TOMLIN_GUI.txt -o output/main.c
```

---

## 📐 4. Format Skrip GUI Deklaratif

Skrip GUI dirancang sangat sederhana dan intuitif:

```text
APP "TOMLIN", "Tomlin Pro", "01.00.0000"
ICON "calculator"
HEADER "TOMLIN SURVEYOR v1.0"

TEXT "Koordinat X : 124.500 m"
TEXT "Koordinat Y : 340.250 m"
TEXT "Elevasi Z   :  45.120 m"
TEXT "Status GPS  : FIX (3D)"
TEXT "Akurasi     : +/- 0.005 m"

FKEY 1, "UKUR"
FKEY 2, "REKAM"
FKEY 3, "PETA"
FKEY 4, "HITUNG"
FKEY 5, "SETTING"
FKEY 6, "KELUAR"
```

### Penjelasan Perintah:
* **`APP "<Nama>", "<Judul>", "<Versi>"`**: Menentukan nama internal aplikasi (maksimal 7 karakter alfanumerik), judul sistem, dan nomor versi.
* **`ICON "<Preset>"`**: Memilih preset ikon menu (opsi: `calculator`, `graph`, `math`, `game`, `tool`).
* **`HEADER "<Teks>"`**: Menampilkan judul pada Title Bar bagian paling atas layar (Y: 0–8).
* **`TEXT "<Teks>"`**: Menampilkan baris teks konten pada layar kerja kalkulator.
* **`FKEY <1-6>, "<Label>"`**: Menampilkan tombol fungsi F1 sampai F6 di bagian bawah layar berupa kotak hitam terbalik (*inverted box*) persis seperti aplikasi bawaan Casio OS.

---

## 🔬 5. Arsitektur Biner & Spesifikasi Teknis Berkas .G1A

Bagi pengembang yang ingin memahami struktur biner mendalam:

1. **Header Kontener Standar (32 Byte, Offset `0x000..0x01F`):**
   * Di-obfuscate dengan operasi bitwise NOT (`b ^ 0xFF`).
   * Mengandung magic signature: `USBPower\xF3\0\x10\0\x10\0` (14 byte).
   * Control Byte 1 pada offset `0x0E`: `(TotalUkuran + 0x41) & 0xFF`.
   * Total Ukuran Berkas pada offset `0x10`: unsigned 32-bit big-endian integer.
   * Control Byte 2 pada offset `0x14`: `(TotalUkuran + 0xB8) & 0xFF`.

2. **Header Add-in fx-9860G (480 Byte, Offset `0x020..0x1FF`):**
   * `0x020`: Nama internal diawali `@` (8 byte NUL-padded).
   * `0x030`: String versi, misal `01.00.0000` (12 byte NUL-padded).
   * `0x03C`: Timestamp tanggal pembuatan, misal `2026.1025.2330` (16 byte).
   * `0x04C`: Bitmap Ikon Menu Utama 30×17 monochrome (68 byte, 1bpp MSB-first row-major).
   * `0x1D4`: Judul tampilan aplikasi (8 byte NUL-padded).
   * `0x1F0`: Ukuran biner payload eksekusi (unsigned 32-bit big-endian).

3. **Runtime Payload SuperH (SH-4A, Offset `0x200` ke atas):**
   * Saat add-in dijalankan, OS Casio memetakan berkas ke alamat virtual `0x00300000` dan melompat langsung ke entry point **`0x00300200`** (tepat setelah header 512 byte).
   * Memanggil fungsi sistem Casio OS via tabel dispatcher **`0x80010070`**:
     * `0x0272`: `Bdisp_AllClr_VRAM()` — Membersihkan buffer VRAM 128x64.
     * `0x0135`: `GetVRAMAddress()` — Mengambil pointer alamat buffer layar 1024 byte.
     * `0x025F`: `Bdisp_PutDisp_DD()` — Mentransfer VRAM ke layar fisik LCD.
     * `0x090F`: `GetKey()` — Menunggu interaksi tombol pengguna.
   * Add-in kembali secara aman ke Main Menu kalkulator saat tombol `EXIT` atau `MENU` ditekan dengan instruksi return `rts`.
