@echo off
cd /d "%~dp0"
color 0A
title BioChain-Opt Launcher

echo ========================================================
echo [+] Memulai BioChain-Opt...
echo ========================================================

where py >nul 2>&1
if errorlevel 1 goto :trypython
set "PYCMD=py"
goto :havepython

:trypython
where python >nul 2>&1
if errorlevel 1 goto :nopython
set "PYCMD=python"
goto :havepython

:nopython
echo [!] Python tidak ditemukan di PATH. Install Python 3.9+ terlebih dahulu.
pause
exit /b 1

:havepython
echo Menjalankan Backend FastAPI...
if exist "backend\venv\Scripts\activate.bat" goto :startbackend

echo [!] Virtual environment (venv) tidak ditemukan!
echo [!] Sedang membuat venv dan menginstall dependencies secara otomatis...
cd backend
%PYCMD% -m venv venv
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 goto :installfailed
cd ..
goto :startbackend

:installfailed
echo [!] Gagal menginstall dependencies. Periksa koneksi internet / requirements.txt.
cd ..
pause
exit /b 1

:startbackend
start cmd /k "cd backend && call venv\Scripts\activate && uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"

echo Menunggu Backend siap...
ping -n 6 127.0.0.1 >nul

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
