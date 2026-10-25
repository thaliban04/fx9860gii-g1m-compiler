@echo off
setlocal
cd /d "%~dp0"
set "PY=python"
where py >nul 2>nul && set "PY=py -3"

echo =========================================================
echo   CASIO fx-9860G / fx-9860GII - ADD-IN GUI (.G1A) BUILDER
echo =========================================================
if "%~1"=="" (
    echo [Info] Mengompilasi contoh GUI bawaan: examples\TOMLIN_GUI.txt
    %PY% g1a_builder.py build "examples\TOMLIN_GUI.txt" --name TOMLIN --title "Tomlin P" --icon calculator --output "output\TOMLIN.g1a"
) else (
    echo [Info] Mengompilasi: %~nx1
    if "%~2"=="" (
        %PY% g1a_builder.py build "%~1" --output "output\%~n1.g1a"
    ) else (
        %PY% g1a_builder.py build "%~1" --name "%~2" --output "output\%~2.g1a"
    )
)

if errorlevel 1 goto :failed

echo.
echo [SUKSES] Berkas .g1a berhasil dibuat di folder 'output'!
echo.
echo [Langkah Pasang ke Kalkulator - 15 Detik]:
echo   1. Hubungkan kalkulator ke PC dengan kabel USB.
echo   2. Pada layar kalkulator, tekan tombol F1 (USB Flash).
echo   3. Buka File Explorer, drag-and-drop berkas .g1a ke dalam drive kalkulator!
echo   4. Selesai! Add-in langsung muncul di MAIN MENU kalkulator.
goto :done

:failed
echo.
echo [GAGAL] Terjadi kesalahan saat membuat .g1a. Baca pesan di atas.

:done
echo.
pause
