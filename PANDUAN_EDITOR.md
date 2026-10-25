# Panduan Lengkap Aplikasi Editor & Compiler Casio FX Studio (fx-9860GII)

Selamat datang di **Casio FX Studio**! Proyek Anda kini telah dilengkapi dengan **2 jenis Editor GUI interaktif** yang memungkinkan Anda mengetik kode Casio BASIC langsung, memeriksa error secara instan, melihat simulasi tampilan kalkulator di layar, dan mengunduh berkas `.g1m` siap pakai.

---

## 🚀 1. Cara Menjalankan Editor

Anda memiliki 2 pilihan aplikasi GUI sesuai kebutuhan:

### Opsi A: Web Studio (Sangat Direkomendasikan! 🌟)
- **Kelebihan:** Tampilan modern, responsif, memiliki **Simulasi Layar LCD Casio fisik**, generator prompt AI interaktif, tombol cepat simbol khusus, dan **bisa berjalan tanpa instalasi apapun** di PC, Mac, maupun HP Android!
- **Cara buka:**
  - Klik ganda file [BUKA_WEB_STUDIO.bat](file:///c:/Users/Thaliban%20Hudzaifah/Documents/Project%20Casio/BUKA_WEB_STUDIO.bat), atau
  - Buka langsung file [index.html](file:///c:/Users/Thaliban%20Hudzaifah/Documents/Project%20Casio/index.html) di browser favorit Anda (Google Chrome, Microsoft Edge, Firefox, Brave).

### Opsi B: Desktop GUI (Python Tkinter)
- **Kelebihan:** Tampilan jendela native Windows, langsung terhubung dengan Python lokal.
- **Cara buka:**
  - Klik ganda file [BUKA_DESKTOP_GUI.bat](file:///c:/Users/Thaliban%20Hudzaifah/Documents/Project%20Casio/BUKA_DESKTOP_GUI.bat), atau
  - Jalankan di terminal:
    ```cmd
    python gui.py
    ```

---

## 📦 2. Cara Menjadikan Aplikasi Standalone (.EXE atau APK)

### Ingin Menjadikan Aplikasi Windows (.EXE)?
Anda bisa membuat file `.exe` mandiri yang bisa dijalankan di komputer Windows manapun **tanpa perlu menginstal Python**:
1. Cukup klik ganda file [BUILD_EXE.bat](file:///c:/Users/Thaliban%20Hudzaifah/Documents/Project%20Casio/BUILD_EXE.bat).
2. Script akan otomatis memasang `PyInstaller` dan mengompilasi `gui.py` menjadi:
   ```text
   dist\CasioStudio.exe
   ```
3. File `CasioStudio.exe` siap dibagikan dan dijalankan dengan sekali klik!

### Ingin Menggunakan di HP Android (APK / Web App)?
File [index.html](file:///c:/Users/Thaliban%20Hudzaifah/Documents/Project%20Casio/index.html) bersifat **100% Client-side**:
1. **Cara Termudah (Tanpa Build APK):** Buka `index.html` di browser Chrome HP Anda, lalu pilih menu titik tiga di pojok kanan atas > **"Tambahkan ke Layar Utama" (Add to Home Screen)**. Aplikasi akan terpasang di HP Anda layaknya aplikasi native!
2. **Cara Menjadi APK:** Anda bisa meng-upload folder ini ke GitHub lalu menggunakan layanan gratis seperti **PWA2APK** atau [PWABuilder](https://www.pwabuilder.com) untuk mengemasnya menjadi file `.apk`.

---

## ✨ 3. Fitur-Fitur Berguna di Editor

1. **Simulasi Percobaan Kode Interaktif (Runtime Emulator Casio fx-9860GII):**
   - Anda bisa langsung mencoba menjalankan kode program sebelum dikirim ke kalkulator!
   - Tekan tombol **▶ Jalankan** atau **⏭ Langkah (Step)** untuk menjalankan kode baris demi baris.
   - **Mendukung Input Interaktif (`?→X`):** Jika program meminta input nilai (seperti `?→A`), layar kalkulator akan menampilkan prompt tanda tanya `?` beserta kolom input angka dan tombol **Kirim [EXE]**.
   - **Mendukung Tanda Jeda (`◢`):** Jika program memiliki jeda pause `◢`, indikator segitiga akan muncul di pojok kanan bawah dan program menunggu Anda menekan tombol **[EXE]**.
   - **Inspektur Variabel Real-Time:** Menampilkan nilai variabel `A` sampai `Z` yang sedang aktif di memori kalkulator secara langsung!
   - **Virtual Keypad:** Dilengkapi tombol angka kalkulator (0-9, ., +, -, ×, ÷, ^, DEL, AC/ON, EXE).
2. **Cek Error Real-time & Diagnostik Pintar:**
   - Mengetahui langsung bila ada tanda petik belum ditutup, nama program melebihi 8 karakter, atau perintah yang belum didukung, lengkap dengan posisi baris dan kolomnya.
3. **Tombol Cepat Simbol Khusus (Quick Insert):**
   - Tidak perlu bingung mencari simbol panah `→`, tidak sama dengan `≠`, kurang dari sama dengan `≤`, `Locate`, atau `ClrText`. Cukup klik tombol di atas editor!
4. **Preset Contoh Program Siap Pakai:**
   - 1. *Halo Layar* (Demo tampilan teks)
   - 2. *Luas & Keliling Persegi* (Perhitungan interaktif input `?→S`)
   - 3. *Rumus Pythagoras* ($C = \sqrt{A^2 + B^2}$)
   - 4. *Persamaan Kuadrat ABC* (Mencari diskriminan dan jenis akar)
   - 5. *Game Tebak Angka* (Permainan logika loop & `If`)
   - 6. *BLOK112* (Fixture resmi kalkulator)
5. **Kompilasi & Unduh Langsung .G1M:**
   - Klik tombol **⚡ Compile .G1M** (atau tekan shortcut `Ctrl+Enter`), file binary `.g1m` akan langsung diunduh ke folder Download komputer Anda.
6. **Membuka & Mengonversi Berkas .G1M ke .TXT (Decompiler):**
   - **Buka langsung:** Klik tombol **📁 Buka (.txt / .g1m)** lalu pilih berkas `.g1m` apa saja. Kode Casio BASIC di dalamnya akan diekstrak otomatis dan ditampilkan di editor!
   - **Konversi 1-klik:** Klik tombol **📥 Convert .G1M → .TXT** untuk memilih berkas `.g1m` dan langsung mengunduh hasil konversinya sebagai file `.txt` rapi.
   - **Lewat Terminal CLI:**
     ```cmd
     python g1m_compiler.py decompile program.g1m -o hasil.txt
     ```

---

## 🤖 4. Master Prompt untuk AI (ChatGPT / Gemini / Claude / DeepSeek)

Jika Anda ingin meminta AI membuatkan rumus atau program kodingan untuk kalkulator, **jangan biarkan AI membuat sembarang kode**, karena AI sering kali menulis perintah yang tidak didukung kalkulator (seperti `Else` atau `While`).

Gunakan template prompt berikut:

```text
Tolong buatkan kode program Casio BASIC untuk kalkulator Casio fx-9860GII yang kompatibel dengan compiler teks G1M saya.

TUGAS PROGRAM:
[Tuliskan keinginan Anda di sini, misalnya: "Buatkan program menghitung rumus gaya Lorentz dan kuat medan magnet"]

ATURAN WAJIB (JANGAN DILANGGAR AGAR TIDAK ERROR):
1. Bahasa: Gunakan subset Casio BASIC murni. BUKAN Python, C, atau JavaScript!
2. Perintah Tampilan:
   - ClrText (untuk membersihkan layar)
   - Locate Kolom,Baris,"TEKS" (Layar teks hanya 21 kolom dan 8 baris, contoh: Locate 1,1,"JUDUL")
   - Locate Kolom,Baris,Variabel (contoh: Locate 1,3,A)
3. Input & Simpan:
   - Gunakan ?->X untuk meminta input angka dari pengguna.
   - Gunakan panah -> untuk simpan nilai (contoh: 10->A atau A+5->B).
   - Variabel HANYA huruf tunggal A sampai Z.
4. Kontrol Alur:
   - Percabangan: If <kondisi> \n Then \n ... \n IfEnd
   - PERINGATAN: Perintah "Else" dan "While" BELUM didukung oleh compiler! Jika butuh percabangan ganda, gunakan beberapa blok "If ... Then ... IfEnd" atau "Goto <label>" dan "Lbl <label>".
   - Perulangan: For 1->I To 10 ... Next
   - Akhiri program dengan: Stop
5. Karakter & Simbol:
   - Hanya string teks ASCII standar (tanpa emoji atau karakter unik).
   - Operator yang valid: +, -, *, /, ^, Int(
   - Operator logika: =, <, >, <=, >=, !=
   - Tanda jeda layar: ◢ (bisa digunakan jika ingin menunggu user menekan EXE).

Format output hanya blok kode teks tanpa komentar panjang agar langsung bisa dicopy-paste ke compiler!
```

*(Di Web Studio, Anda cukup membuka tab **"🤖 Prompt untuk AI"**, ketik tugas Anda, lalu klik tombol **"📋 Salin Prompt AI"**!)*

---

## 📖 5. Ringkasan Sintaks Casio BASIC yang Didukung

| Kategori | Sintaks | Penjelasan |
| --- | --- | --- |
| **Layar** | `ClrText` | Membersihkan layar kalkulator |
| **Teks** | `Locate X,Y,"TEKS"` | Menulis teks pada Kolom X (1-21), Baris Y (1-8) |
| **Variabel** | `Locate X,Y,A` | Menampilkan nilai angka dari variabel A |
| **Input** | `?→A` (atau `?->A`) | Menampilkan tanda tanya `?`, menunggu input dari user |
| **Simpan** | `10→A` (atau `10->A`) | Memasukkan angka 10 ke variabel A |
| **Variabel** | `A` sampai `Z` | Huruf tunggal 1 karakter |
| **Kondisi** | `If A>0` <br>`Then` <br>`...` <br>`IfEnd` | Percabangan Jika-Maka (*Catatan: Else belum didukung*) |
| **Loop** | `For 1→I To 10` <br>`...` <br>`Next` | Perulangan hitungan |
| **Lompat** | `Goto 1` ... `Lbl 1` | Lompat ke baris Label tertentu |
| **Selesai** | `Stop` | Mengakhiri program |
| **Pause** | `◢` | Menunggu tombol [EXE] ditekan |
| **Komentar** | `# komentar` atau `//` | Dihapus otomatis oleh compiler |

---

## 🔌 6. Transfer Langsung ke Kalkulator (FA-124 Native Bridge & Android OTG)

Aplikasi kami sekarang telah mem-porting antarmuka dan fungsi **CASIO FA-124** ke dalam program secara native melalui jendela pop-up **Dual-Pane Transfer Manager**!

### A. Fitur FA-124 Native Transfer Bridge:
1. **Dual-Pane Interface (Persis FA-124)**:
   - **Panel Kiri**: *PC Storage / Memory Image (`Default.g1m`)* — memuat program aktif dari editor atau file `.g1m`/`.txt` yang Anda impor.
   - **Tombol Tengah**: **Kirim ➔ (Download)** untuk mengirim program ke kalkulator, dan **⬅ Ambil (Upload)** untuk mengunduh program dari kalkulator langsung ke editor.
   - **Panel Kanan**: *Casio fx-9860GII (Main Memory)* — menampilkan daftar program yang tersimpan di dalam memori kalkulator.
2. **Koneksi USB Langsung (WebUSB & Protocol 7.00)**:
   - Terintegrasi dengan Vendor ID Casio (`0x07CF`) dan Product ID (`0x6101` / CESG502).
   - Indikator LED status sambungan (Merah: terputus, Hijau: terhubung).
   - Progress bar proses pengiriman paket data dan verifikasi checksum XOR 0xFF.
3. **1-Click Official Launcher**:
   - Di Desktop GUI (`gui.py`), terdapat tombol **"🚀 Buka Software Resmi CASIO FA-124.exe"** yang langsung menjalankan executable bawaan yang ada di folder proyek tanpa ribet.

---

### B. Cara Transfer Langsung dari HP Android (Via USB-OTG Tanpa Laptop):
Anda tidak harus selalu membawa laptop untuk mengisi program ke kalkulator di sekolah/kampus/lapangan! Cukup gunakan HP Android Anda:

1. **Persiapan**:
   - Kabel USB-OTG (Type-C / Micro-USB ke port USB Mini kalkulator).
   - Buka browser **Google Chrome** atau **Microsoft Edge** di HP Android Anda.
2. **Buka Web Studio**:
   - Buka berkas `index.html` kami di browser HP Anda.
3. **Hubungkan Kabel**:
   - Tancapkan kabel OTG dari HP ke kalkulator Casio fx-9860GII.
   - Pada layar kalkulator, tekan tombol **F1** (*Flash / Data Trans*).
4. **Mulai Transfer**:
   - Klik tombol **"🔌 FA-124 Transfer (USB/OTG)"** di bagian atas Web Studio.
   - Klik tombol **"🔗 Hubungkan USB / OTG"**.
   - Layar Android akan memunculkan dialog keamanan sistem: *"Izinkan Casio FX Studio mengakses perangkat USB Casio fx-9860GII?"*. Tekan **OK / Izinkan**.
   - Pilih program di panel kiri, lalu klik **"Kirim ➔"**. Program langsung masuk ke kalkulator!

---

### C. Cara Menggunakan Software Resmi CASIO FA-124 di PC (Manual / Alternatif):
Jika Anda tetap ingin menggunakan software resmi bawaan Casio:
1. Sambungkan kabel USB kalkulator Casio fx-9860GII ke komputer, pilih **F1** di kalkulator.
2. Buka dialog **🔌 FA-124 Transfer** di aplikasi kami lalu klik tombol **"🚀 Buka Software Resmi CASIO FA-124.exe"** (atau jalankan `CASIO FA-124\FA124.exe`).
3. Pada panel FA-124 sebelah kiri, klik kanan pada **Default.g1m**, pilih **Import**, lalu pilih file `.g1m` hasil kompilasi.
4. Klik tombol **Connect** pada toolbar FA-124.
5. Seret (*drag & drop*) program dari Memory Image ke memori kalkulator.
6. Selesai! Buka menu **PRGM** pada kalkulator dan jalankan program Anda!
