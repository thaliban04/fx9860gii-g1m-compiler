@echo off
title Build Casio FX Studio menjadi EXE
cd /d "%~dp0"
echo ========================================================
echo   MEMBUAT APLIKASI STANDALONE (.EXE) CASIO FX STUDIO
echo ========================================================
echo.
echo 1. Memeriksa PyInstaller...
py -3 -m pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo    PyInstaller belum terpasang. Memasang PyInstaller...
    py -3 -m pip install pyinstaller
) else (
    echo    PyInstaller sudah terpasang.
)

echo.
echo 2. Mengompilasi gui.py menjadi CasioStudio.exe...
py -3 -m PyInstaller --onefile --windowed --name="CasioStudio" --clean gui.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo   BERHASIL!
    echo   File executable ada di folder: dist\CasioStudio.exe
    echo ========================================================
) else (
    echo.
    echo [ERROR] Gagal membuat file exe. Silakan cek pesan di atas.
)

pause
