@echo off
color 0A
title BioChain-Opt Launcher
echo ========================================================
echo [+] Memulai BioChain-Opt...
echo ========================================================
"C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe" run.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Terjadi kesalahan saat menjalankan aplikasi.
    pause
)
