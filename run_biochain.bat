@echo off
color 0A
title BioChain-Opt Launcher

echo ========================================================
echo [+] Memulai BioChain-Opt...
echo ========================================================

echo Menjalankan Backend FastAPI...
if not exist "backend\venv\Scripts\activate.bat" (
    echo [!] Virtual environment (venv) tidak ditemukan!
    echo [!] Sedang membuat venv dan menginstall dependencies secara otomatis...
    cd backend
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
    cd ..
)
start cmd /k "cd backend && call venv\Scripts\activate && uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"

echo Menunggu Backend siap...
timeout /t 5

echo =======================================================
echo MENGAKTIFKAN CLOUDFLARE TUNNEL (ONLINE ACCESS)
echo =======================================================
echo HARAP TUNGGU...
start cmd /k "npx untun@latest tunnel http://localhost:8000"

echo.
echo =======================================================
echo BioChain-Opt sedang berjalan!
echo Backend Lokal: http://localhost:8000
echo Tunnel URL akan muncul di jendela baru (akhiran trycloudflare.com).
echo Salin URL tersebut dan masukkan ke ikon [Gear] di web Vercel Anda!
echo =======================================================
pause
