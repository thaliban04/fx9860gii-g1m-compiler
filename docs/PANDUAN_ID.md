# Panduan dari kode teks sampai file `.g1m`

## 1. Memahami jenis kode yang digunakan

Kalkulator Casio fx-9860GII memiliki bahasa pemrograman yang bernama **Casio BASIC**. Program ini **bukan Python, bukan C, dan bukan JavaScript**.

Contoh kodenya:

```text
ClrText
Locate 1,1,"HALO"
?→X
X+5→Y
Locate 1,3,Y
Stop
```

Penjelasan: `ClrText` membersihkan layar. `Locate 1,1,"HALO"` menulis teks pada kolom 1 baris 1. `?→X` meminta angka lalu menyimpannya dalam variabel `X`. `X+5→Y` menghitung angka baru dan menyimpannya dalam `Y`. `Locate 1,3,Y` menampilkan hasil. `Stop` mengakhiri program.

## 2. Menyiapkan lingkungan

- Gunakan komputer Windows jika akan memakai FA-124.
- Instal Python 3 dari <https://www.python.org/downloads/>.
- Saat memasang, aktifkan opsi penambahan Python ke PATH bila tersedia.
- Download lalu ekstrak file ZIP proyek ini. Jangan hanya menyalin `BUAT_G1M.bat` tanpa `g1m_compiler.py`.

Di Command Prompt cek Python:

```cmd
py -3 --version
```

Di komputer yang tidak memiliki launcher `py`, gunakan `python --version`.

## 3. Mengetik kode sendiri

1. Buka VS Code atau Notepad.
2. Ketik kode Casio BASIC memakai perintah yang sudah didukung.
3. Simpan dengan encoding **UTF-8** dan ekstensi `.txt`, misalnya `HITUNG.txt`.
4. Gunakan tanda petik biasa `"` untuk teks.
5. Gunakan `→` untuk penyimpanan, atau tulis `->` jika sulit mengetik simbol panah.
6. Gunakan variabel satu huruf misalnya `A`, `B`, `X`.

Contoh:

```text
# hitung luas persegi
ClrText
Locate 1,1,"SISI?"
?→A
A*A→B
Locate 1,3,"LUAS:"
Locate 1,4,B
Stop
```

Komentar setelah tanda `#` dihapus oleh compiler dan tidak ikut masuk ke kalkulator.

## 4. Menjalankan compiler

Cara klik ganda: jalankan `BUAT_G1M.bat` tanpa file untuk membangun contoh BLOK112. Atau seret berkas `.txt` milikmu ke ikon `BUAT_G1M.bat`.

Cara yang lebih fleksibel di Command Prompt:

```cmd
py -3 g1m_compiler.py build HITUNG.txt --name HITUNG --output output\HITUNG.g1m
```

Nama `HITUNG` muncul di menu PRGM kalkulator. Nama program tidak boleh lebih dari **8 karakter**, tanpa spasi, dimulai huruf A sampai Z.

Untuk contoh original:

```cmd
py -3 g1m_compiler.py build examples\BLOK112.txt --name BLOK112 --output output\BLOK112.g1m
```

## 5. Mengecek hasil konversi

```cmd
py -3 g1m_compiler.py inspect output\BLOK112.g1m
```

Hasilnya menampilkan nama program, ukuran file, ukuran data, dan jumlah program di dalam arsip. Pemeriksaan ini hanya memeriksa struktur berkas, bukan apakah rumus program menghasilkan jawaban yang benar.

## 6. Memasukkan `.g1m` lewat FA-124

1. Hubungkan fx-9860GII ke komputer dan jalankan FA-124.
2. Pada panel FA-124, buat atau pilih **memory image** yang dituju.
3. Klik kanan pada memory image, pilih **Import**.
4. Pilih `output\BLOK112.g1m` atau berkas buatanmu.
5. Sambungkan ke kalkulator, lalu pindahkan item program ke memori perangkat sesuai prosedur FA-124.
6. Buka menu `PRGM` pada kalkulator dan jalankan program dengan namanya.

Opsi **Import** pada memory image dan proses pemindahan data dijelaskan di panduan resmi CASIO FA-124, bagian transfer data antara komputer dan kalkulator: <https://support.casio.com/pdf/004/FA-124_E.pdf>.

Disarankan **membuat backup memori kalkulator** sebelum mencoba program baru. Berkas yang baru dikompilasi belum tentu benar secara logika dan hanya contoh BLOK112 yang sebelumnya telah dilaporkan berhasil pada perangkat.

## 7. Mengunggah proyek ke GitHub

### Cara melalui situs web

1. Masuk ke <https://github.com/new>.
2. Buat repo, misalnya `fx9860gii-g1m-compiler`.
3. Hindari memilih pembuatan README otomatis karena proyek sudah punya README.
4. Ekstrak ZIP ini lalu unggah seluruh isi proyek melalui menu **Add file** lalu **Upload files** di repo.
5. Commit unggahan. Struktur folder dan `.github/workflows/tests.yml` harus tetap dipertahankan.
6. Buka tab **Actions** untuk melihat pengujian otomatis, jika Actions diaktifkan.

### Cara melalui Git

Di dalam folder proyek, jalankan perintah berikut satu per satu:

```bash
git init
git add .
git commit -m "Initial release: Casio BASIC text to G1M compiler"
git branch -M main
git remote add origin https://github.com/USERNAME/fx9860gii-g1m-compiler.git
git push -u origin main
```

Ganti `USERNAME` dengan akun GitHub sendiri. Buat repository kosong di GitHub terlebih dahulu dan pastikan Git sudah terpasang dan autentikasi telah dilakukan.

## 8. Error yang sering muncul

| Pesan | Penyebab dan solusi |
| --- | --- |
| `Nama program harus 1-8 karakter` | Ganti nilai `--name` menjadi singkat, contohnya `TES001`. |
| `kata ... belum didukung` | Perintah belum ada di peta token. Periksa README dan jangan asal mengganti ekstensi. |
| `string hanya ASCII` | Ada huruf beraksen atau emoji di antara tanda petik. Ganti dengan teks biasa. |
| `tanda petik penutup tidak ditemukan` | Perbaiki pasangan tanda petik `"..."`. |
| `No such file or directory` | Jalankan terminal dari folder proyek atau gunakan lokasi file yang benar. |
| `py is not recognized` | Instal Python atau jalankan lewat `python` sebagai pengganti `py -3`. |

## 9. Batasan dan rencana pengembangan

Compiler versi ini mendukung **subset bahasa Casio BASIC**, menggunakan pembungkus satu program per berkas. Kompilasi yang berhasil bukan jaminan sintaks kompatibel untuk semua varian kalkulator. Pengembangan lanjutan dapat menambah `Else`, `While`, fungsi trigonometri, file multi-program, dan decompiler, tetapi setiap tambahan harus memiliki uji terhadap hasil ekspor asli dari kalkulator.
