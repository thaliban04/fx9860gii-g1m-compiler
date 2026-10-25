@echo off
title Pasang Driver WinUSB Casio fx-9860GII (Zadig Portable)
cd /d "%~dp0"
echo ======================================================================
echo   PEMASANGAN DRIVER MODERN WINUSB UNTUK CASIO fx-9860GII (VID: 0x07CF)
echo   Mengizinkan Browser (Chrome/Edge WebUSB) Langsung Akses Kalkulator
echo ======================================================================
echo.
echo Menjalankan Zadig (Official Driver Installer)...
echo.
echo PETUNJUK 3 LANGKAH DI JENDELA ZADIG:
echo 1. Klik menu "Options" -^> centang "List All Devices"
echo 2. Pada kotak pilihan dropdown di atas, pilih: "CESG502 USB"
echo 3. Di sebelah kanan tanda panah hijau, pastikan tertulis "WinUSB"
echo 4. Klik tombol besar: "Replace Driver" (atau "Install Driver")
echo 5. Tunggu sampai muncul pesan "Driver installed successfully", lalu tutup Zadig.
echo.
echo Membuka Zadig sekarang...
start "" "%~dp0zadig.exe"
exit /b
