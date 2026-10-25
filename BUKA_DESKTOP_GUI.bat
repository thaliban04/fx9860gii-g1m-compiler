@echo off
title Casio FX Studio Desktop GUI
cd /d "%~dp0"
py -3 gui.py
if %errorlevel% neq 0 (
    python gui.py
)
if %errorlevel% neq 0 (
    echo Gagal menjalankan gui.py. Pastikan Python 3 sudah terpasang.
    pause
)
