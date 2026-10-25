@echo off
title Buka Device Manager Windows
echo ======================================================================
echo   MEMBUKA DEVICE MANAGER UNTUK MENGGANTI DRIVER KE WINUSB
echo ======================================================================
echo.
echo Langkah 15 Detik:
echo 1. Cari perangkat "CESG502 USB" (di bawah Universal Serial Bus controllers)
echo 2. Klik kanan "CESG502 USB" -^> pilih "Update driver" (Perbarui driver)
echo 3. Pilih "Browse my computer for drivers"
echo 4. Pilih "Let me pick from a list of available drivers on my computer"
echo 5. Pilih "WinUsb Device" (atau Universal Serial Bus devices -^> WinUsb Device)
echo 6. Klik Next -^> Selesai!
echo.
echo Membuka Device Manager...
start devmgmt.msc
exit /b
