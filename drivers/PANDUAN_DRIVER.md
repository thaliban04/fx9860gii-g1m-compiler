# Panduan Porting FA-124 & Driver Modern Casio fx-9860GII

Dokumen ini menjelaskan hasil pembongkaran (reverse engineering) software resmi CASIO FA-124 dan bagaimana sistem transfer modern WebUSB & Android OTG diimplementasikan ke dalam **Casio FX Studio**.

---

## 1. Mengapa FA-124 Terlalu Jadul?
Software **CASIO FA-124** dibuat pada era Windows XP/2000 (~2002-2007) dengan arsitektur 32-bit MFC:
1. **Driver Usang (`cesg64.sys`)**: Driver kernel Casio tahun 2007 ini memonopoli port USB kalkulator dengan hak akses eksklusif (`ERROR_SHARING_VIOLATION`), sehingga software modern atau browser (Chrome/Edge WebUSB) dicegah membukanya saat FA-124 aktif.
2. **UI Kaku & Workspace Tertutup**: FA-124 tidak membaca file `.g1m` secara langsung dari folder dinamis, melainkan menyimpannya ke dalam file backup arsip biner internal (`Default.g2r`).

---

## 2. Hasil Pembongkaran (Reverse Engineering) FA-124

Melalui analisis disassembly terhadap `FA124.exe`, `CasComn.dll`, dan `EnumDev.dll`:
- **Protokol Inti**: Casio **Protocol 7.00**
- **Hardware Target**: `USB\VID_07CF&PID_6101` (Casio fx-9860G / fx-9860GII / Graph series)
- **Struktur Paket Protokol 7.00**:
  - `Byte 0`: Tipe Paket (`0x05` Handshake Koneksi, `0x01` Command, `0x02` Data Chunk, `0x06` ACK, `0x0B` Terminasi, `0x15` NAK).
  - `Byte 1..2`: Subtipe ASCII (misal `"00"` untuk Connect, `"25"` untuk Transfer Main Memory Program).
  - `Byte 3`: Flag Extended (`'1'` jika membawa payload data, `'0'` jika hanya header).
  - `Byte 4..7`: Panjang payload setelah di-escape (4 karakter heksadesimal ASCII, `%04X`).
  - **Payload 0x5C Padding**: Byte di bawah `0x20` diubah menjadi `\` (`0x5C`) + `(byte + 0x20)`. Karakter `\` diubah menjadi `\\`.
  - **Checksum**: Two's-complement dari jumlah byte (`(~(sum & 0xFF) + 1) & 0xFF`), dikodekan dalam 2 karakter ASCII hex.
- **Command 25 (Transfer Program ke Main Memory)**:
  - Header: Overwrite flag `"02"`, Data Type `"00"`, Ukuran File (8 hex), Panjang argumen direktori & nama (12 hex), Folder `"main"`, Nama Program (misal `"BLOK2"`).
  - Payload dipotong per blok 256 byte raw, dibungkus paket Data `0x02`, lalu diakhiri paket Terminasi `0x0B`.

Semua spesifikasi ini telah diporting penuh ke dalam:
- `casio_p7.py` (Mesin Python murni)
- `CasioProtocol7` di dalam `index.html` (Mesin JavaScript murni)

---

## 3. Cara Mengaktifkan Transfer Langsung di Browser (WebUSB)

### A. Di Komputer / Laptop Windows (Solusi Mengatasi 'Access Denied'):
Pesan error `Failed to execute 'open' on 'USBDevice': Access denied.` terjadi karena kalkulator masih terikat dengan driver lama `CESG64.sys` bawaan FA-124 tahun 2007. Chrome/Edge WebUSB mewajibkan driver **WinUSB**.

**Cara Mengaktifkan WinUSB dalam 15 Detik (Bawaan Windows, Resmi Microsoft):**
1. **Pastikan software resmi FA124.exe sudah DITUTUP** (agar port USB tidak dikunci).
2. Jalankan file pembantu: [`drivers\BUKA_DEVICE_MANAGER.bat`](file:///c:/Users/Thaliban%20Hudzaifah/Documents/Project%20Casio/drivers/BUKA_DEVICE_MANAGER.bat) (atau tekan `Win + X` lalu pilih **Device Manager**).
3. Di Device Manager, cari perangkat **CESG502 USB** (biasanya di bawah grup *Universal Serial Bus controllers* atau *USB*).
4. Klik kanan pada **CESG502 USB** ➔ pilih **Update driver** (*Perbarui pengandar*).
5. Pilih **Browse my computer for drivers** (*Cari pengandar di komputer saya*).
6. Pilih **Let me pick from a list of available drivers on my computer** (*Biarkan saya memilih dari daftar pengandar yang tersedia*).
7. Pilih grup **Universal Serial Bus devices** (atau centang *Show compatible hardware*) ➔ pilih model **WinUsb Device** ➔ klik **Next** ➔ klik **Yes**.
8. Selesai! Windows langsung mengganti driver ke WinUSB resmi Microsoft.
9. Cabut dan colokkan kembali kabel USB kalkulator, tekan tombol **F1** di kalkulator, lalu klik **🔗 Hubungkan USB / OTG** di browser. Browser langsung berhasil membuka antarmuka dan siap kirim program!

---

### B. Di HP Android via Kabel USB-OTG (Tanpa Driver!):
Android menggunakan kernel Linux standar yang langsung mengekspos `usbfs` ke browser Google Chrome / Edge:
1. Pasang kabel USB-OTG dari HP Android ke kabel USB kalkulator Casio.
2. Pada kalkulator, tekan tombol **F1** (*Select Connection Mode*).
3. Buka file `index.html` di Google Chrome HP Android Anda.
4. Klik tombol **🔌 FA-124 Transfer (USB/OTG)**, lalu tekan **🔗 Hubungkan USB / OTG**.
5. Android akan menampilkan jendela: *"Izinkan Chrome mengakses CESG502 USB?"*.
6. Klik **Izinkan** / **OK**.
7. Klik **Kirim ➔**. Program langsung masuk ke menu PRGM kalkulator tanpa perlu laptop/PC!
