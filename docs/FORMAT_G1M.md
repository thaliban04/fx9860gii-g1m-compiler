# Catatan teknis format G1M

Proyek ini memakai **struktur yang diverifikasi dari berkas BLOK112.g1m** yang telah berhasil diterima oleh fx-9860GII, bukan pendekatan mengganti nama berkas teks. Detail diselaraskan dengan dokumentasi terbuka Cahute.

## Struktur arsip satu program

| Offset | Ukuran | Isi |
| --- | ---: | --- |
| `0x00` | 32 byte | Header standar, tiap byte di-XOR `0xFF` |
| `0x20` | 20 byte | Nama grup `PROGRAM` dan jumlah item |
| `0x34` | 24 byte | Direktori `system`, nama program, tipe, panjang data |
| `0x4C` | sesuai panjang | Data program Casio BASIC |

Bagian data program pada contoh yang berhasil terdiri dari 10 byte `00`, kode instruksi yang ditokenisasi, penanda akhir `F7 4D 00`. Antara baris terdapat `0D`, tanpa menambah pemisah baris setelah baris terakhir. Tidak perlu padding tambahan untuk struktur yang digunakan di sini.

## Header standar 32 byte

Header menyimpan ukuran total berkas dalam 4 byte big-endian. Sebelum ditulis ke berkas, setiap byte header di-XOR dengan `0xFF`. Byte kontrol dihitung dari panjang total berkas (`N`):

```python
control_1 = (N + 0x41) & 0xFF
control_2 = (N + 0xB8) & 0xFF
```

Kedua byte kontrol juga diinversi saat disimpan. Compiler mempertahankan byte reserved serta identifier tipe berkas berdasarkan **satu fixture nyata yang telah berhasil**. Header yang didukung tidak dimaksudkan mencakup semua model dan semua variasi berkas Casio.

## Tabel token contoh

| CASIO BASIC | Byte hex |
| --- | --- |
| `ClrText` | `F7 18` |
| `Locate` | `F7 10` |
| `If` | `F7 00` |
| `Then` | `F7 01` |
| `IfEnd` | `F7 03` |
| `For` | `F7 04` |
| `To` | `F7 05` |
| `Next` | `F7 07` |
| `Stop` | `F7 0E` |
| `Goto` | `EC` |
| `Lbl` | `E2` |
| `Int` | `A6` |
| `+`, `-`, `*`, `/` | `89`, `99`, `A9`, `B9` |
| `^` | `A8` |
| `→` | `0E` |
| `◢` | `0C` |
| `≤`, `≠`, `≥` | `10`, `11`, `12` |

Sebagian besar token perintah diperoleh dengan mencocokkan kode sumber asli terhadap fixture yang berhasil. Token `*` dan `^` dicocokkan dengan tabel kode keyboard fx-9860G yang dipublikasikan komunitas dan masih memerlukan uji perangkat independen.

## Cara menambah token baru dengan aman

1. Tulis satu program kecil berisi perintah baru langsung pada kalkulator.
2. Ekspor program menggunakan FA-124 sehingga mendapatkan `.g1m` pembanding.
3. Bandingkan data hex sebelum dan setelah penambahan perintah untuk menemukan token.
4. Tambahkan token baru dalam `KEYWORDS` atau `SINGLE_CHAR_TOKENS`.
5. Tambah kasus uji di `tests/test_compiler.py` dan, jika memungkinkan, tes byte-per-byte terhadap fixture baru.
6. Unggah perubahan setelah lolos tes dan mencoba program pada perangkat.

## Referensi

- https://next.cahute.org/topics/file-formats/container.html
- https://next.cahute.org/topics/file-formats/mainmem.html
- https://cahute.org/topics/text-encodings.html
- https://www.cemetech.net/forum/viewtopic.php?t=10497
- https://support.casio.com/pdf/004/FA-124_E.pdf
