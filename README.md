# fx-9860GII Text-to-G1M Compiler

Compiler ringan berbasis **Python 3** untuk mengubah berkas teks berisi **Casio BASIC** menjadi berkas **`.g1m`** yang dapat diimpor dengan **CASIO FA-124** untuk **Casio fx-9860GII**.

**Status: prototipe fungsional untuk subset Casio BASIC.** Hasil kompilasi `examples/BLOK112.txt` cocok **identik secara biner** dengan contoh `fixtures/BLOK112_known_working.g1m` yang telah berhasil dijalankan pada kalkulator pengguna. Perintah selain yang didukung belum dijamin kompatibel dengan perangkat karena belum diuji satu per satu di kalkulator.

> Ini adalah compiler **teks Casio BASIC ke format data G1M**, bukan compiler bahasa Python/C ke executable G1A. Tidak berafiliasi dengan CASIO.

## Mulai dalam 1 menit

### Cara termudah untuk Windows

1. Instal **Python 3** dari https://www.python.org/downloads/ jika belum ada.
2. Unduh/ekstrak seluruh isi repositori ke satu folder.
3. Klik ganda `BUAT_G1M.bat` untuk membuat contoh `BLOK112.g1m`.
4. Cari hasilnya di folder `output/BLOK112.g1m`.
5. Impor berkas itu dengan **FA-124**, kemudian kirim ke kalkulator.

**Cara membuat program sendiri:** edit/simpan teks Casio BASIC sebagai `.txt`. Seret file `.txt` ke ikon `BUAT_G1M.bat` di Windows. Untuk nama file sumber lebih dari 8 karakter, gunakan perintah terminal dengan `--name`.

### Cara terminal Windows

Buka Command Prompt atau PowerShell di folder proyek, lalu jalankan:

```powershell
py -3 g1m_compiler.py build examples/BLOK112.txt --name BLOK112 --output output/BLOK112.g1m
```

Contoh program lain:

```powershell
py -3 g1m_compiler.py build examples/HELLO.txt --name HELLO --output output/HELLO.g1m
```

### Linux atau macOS

```bash
python3 g1m_compiler.py build examples/HELLO.txt --name HELLO --output output/HELLO.g1m
```

### Periksa struktur file keluaran

```bash
python3 g1m_compiler.py inspect output/HELLO.g1m
```

Perintah ini memverifikasi informasi header, nama program, ukuran arsip, dan penanda akhir. Pemeriksaan format **tidak sama dengan uji eksekusi pada kalkulator**.

## Contoh kode Casio BASIC

Simpan sebagai file UTF-8 `HITUNG.txt`:

```text
ClrText
Locate 1,1,"INPUT A"
?→A
A+10→B
Locate 1,3,"HASIL"
Locate 1,4,B
Stop
```

Jalankan:

```bash
python3 g1m_compiler.py build HITUNG.txt --name HITUNG --output HITUNG.g1m
```

`HITUNG.g1m` yang dihasilkan bisa diimpor ke FA-124.

## Perintah dan simbol yang didukung

| Kategori | Sintaks dalam `.txt` |
| --- | --- |
| Tampilan | `ClrText`, `Locate`, `"TEKS"`, `◢` |
| Masukan dan penyimpanan | `?→X`, `10→A`, `->` sebagai alternatif `→` |
| Percabangan | `If`, `Then`, `IfEnd`, `Goto`, `Lbl` |
| Perulangan | `For`, `To`, `Next` |
| Operasi matematika | `Int(`, `+`, `-`, `*`, `/`, `^` |
| Perbandingan | `=`, `<`, `>`, `≤`, `≠`, `≥`, `<=`, `!=`, `>=` |
| Penghentian | `Stop` |
| Komentar khusus untuk compiler | `# ...`, `// ...` di luar string |

- Nama variabel sementara: huruf tunggal `A` sampai `Z`. Nama file program maksimal 8 karakter ASCII, harus diawali huruf.
- Teks yang ditampilkan di antara tanda petik harus karakter ASCII dasar. Hindari emoji, huruf beraksen, dan simbol di dalam string.
- Spasi di luar tanda petik diabaikan. Komentar dihapus sebelum penerjemahan.
- Perintah yang belum tersedia sengaja menghasilkan **pesan error**, bukan disalin sebagai teks mentah.
- `Else`, `While`, `Do`, `List`, `Mat`, fungsi grafis, dan seluruh perintah Casio BASIC lainnya **belum didukung** oleh versi ini.
- Compiler hanya menerjemahkan sintaks ke data token. Ia tidak membuktikan bahwa algoritme program pasti benar.

Panduan belajar dan langkah FA-124 lebih rinci ada di [docs/PANDUAN_ID.md](docs/PANDUAN_ID.md).

## Susunan repositori

```text
fx9860gii-g1m-compiler/
├── g1m_compiler.py             # Compiler dan pemeriksa struktur
├── BUAT_G1M.bat                # Cara praktis Windows dan drag-drop
├── examples/
│   ├── BLOK112.txt             # Contoh asli yang telah berhasil
│   └── HELLO.txt               # Contoh program sederhana
├── fixtures/
│   └── BLOK112_known_working.g1m
├── output/                     # Hasil build, diabaikan Git
├── tests/test_compiler.py      # Pengujian otomatis
├── docs/
│   ├── PANDUAN_ID.md
│   └── FORMAT_G1M.md
├── .github/workflows/tests.yml # CI otomatis saat push ke GitHub
├── QUICKSTART.txt
└── LICENSE
```

## Test dan kontribusi

```bash
python3 -m unittest discover -s tests -v
```

Sepuluh uji otomatis mencakup kecocokan byte terhadap berkas yang telah berhasil, token dasar, validasi nama, komentar, kesalahan sintaks, pengecekan header, dan perintah terminal. Pengujian dijalankan juga di GitHub Actions.

Untuk menambah perintah Casio BASIC, baca `docs/FORMAT_G1M.md`, tambahkan kode token pada `KEYWORDS` atau `SINGLE_CHAR_TOKENS` dan tulis tes yang membandingkan hasilnya dengan program yang diekspor dari kalkulator melalui FA-124.

## Referensi teknis

1. [CASIO FA-124 Software User's Guide](https://support.casio.com/pdf/004/FA-124_E.pdf), panduan resmi transfer program dan impor G1M.
2. [Cahute: CASIO container format](https://next.cahute.org/topics/file-formats/container.html), struktur header dan kontrol panjang berkas.
3. [Cahute: Main memory archives](https://next.cahute.org/topics/file-formats/mainmem.html), header grup dan item berkas.
4. [Cahute: Text encodings](https://cahute.org/topics/text-encodings.html), penjelasan token satu dan dua byte Casio.
5. [Cemetech: G1M/G3M file comparison](https://www.cemetech.net/forum/viewtopic.php?t=10497), contoh header file memori.
6. [casint, interpreter komunitas](https://github.com/jm-/casint), proyek terkait untuk belajar parsing G1M.

## Lisensi

MIT. Silakan perbarui nama pemegang hak cipta di `LICENSE` sesuai kebutuhan sebelum publikasi.
