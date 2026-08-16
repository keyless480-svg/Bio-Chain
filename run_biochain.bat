@echo off
color 0A
title BioChain-Opt Launcher (Python 3.12)
echo ========================================================
echo 🌿 Memulai BioChain-Opt menggunakan Python 3.12...
echo ========================================================
py -3.12 run.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Terjadi kesalahan saat menjalankan aplikasi.
    pause
)
