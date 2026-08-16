import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def print_step(msg):
    print(f"\n{'='*50}\n🚀 {msg}\n{'='*50}")

def main():
    print("🌿 Memulai BioChain-Opt (Mode Lokal / Tanpa Docker)...")
    
    root_dir = Path(__file__).parent.absolute()
    backend_dir = root_dir / "backend"
    frontend_dir = root_dir / "frontend"
    
    # 1. Setup Backend Dependencies
    print_step("Memeriksa dependensi Python (Backend)...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                       cwd=backend_dir, check=True)
    except subprocess.CalledProcessError:
        print("❌ Gagal menginstal dependensi backend. Pastikan Python terinstal dengan benar.")
        sys.exit(1)
        
    # 2. Setup SQLite Database
    print_step("Inisialisasi Database SQLite & Seed Data...")
    env_vars = os.environ.copy()
    env_vars["PYTHONPATH"] = str(backend_dir)
    try:
        subprocess.run([sys.executable, "src/seed/seed_data.py"], 
                       cwd=backend_dir, env=env_vars, check=True)
    except subprocess.CalledProcessError:
        print("❌ Gagal inisialisasi database.")
        sys.exit(1)
        
    # 3. Check / Install Frontend Dependencies
    print_step("Memeriksa dependensi Node.js (Frontend)...")
    try:
        # Check if node_modules exists, if not install
        if not (frontend_dir / "node_modules").exists():
            print("Menginstal package NPM (mungkin butuh beberapa saat)...")
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True, shell=True)
    except subprocess.CalledProcessError:
        print("❌ Gagal menginstal dependensi NPM. Pastikan Node.js terinstal.")
        sys.exit(1)
        
    # 4. Start Servers
    print_step("Menyalakan Server Backend & Frontend...")
    
    # Backend Server (FastAPI)
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.main:app", "--port", "8000"],
        cwd=backend_dir,
        env=env_vars
    )
    
    # Frontend Server (Vite)
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        shell=True
    )
    
    # Buka browser
    def open_browser():
        time.sleep(5) # Tunggu 5 detik agar server nyala
        print("\n🌐 Membuka BioChain-Opt di browser...")
        webbrowser.open("http://localhost:5173")
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

    try:
        # Tahan script utama agar server tetap berjalan
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Menghentikan BioChain-Opt...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ Berhasil dihentikan.")

if __name__ == "__main__":
    main()
