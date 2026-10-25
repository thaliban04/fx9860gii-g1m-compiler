@echo off
setlocal
cd /d "%~dp0"
set "PY=python"
where py >nul 2>nul && set "PY=py -3"
echo ======================================
echo CASIO fx-9860GII - TEXT TO G1M
echo ======================================
if "%~1"=="" (
    echo Tanpa file: compile contoh BLOK112.txt
    %PY% g1m_compiler.py build "examples\BLOK112.txt" --name BLOK112 --output "output\BLOK112.g1m"
) else (
    if "%~2"=="" (
        echo Compile file %~nx1
        %PY% g1m_compiler.py build "%~1" --output "output\%~n1.g1m"
    ) else (
        echo Compile file %~nx1 dengan nama kalkulator %~2
        %PY% g1m_compiler.py build "%~1" --name "%~2" --output "output\%~2.g1m"
    )
)
if errorlevel 1 (
    echo.
    echo GAGAL. Baca pesan kesalahan dan PANDUAN_ID.md
) else (
    echo.
    echo SUKSES. Lihat folder output lalu import G1M dengan FA-124.
)
echo.
pause
