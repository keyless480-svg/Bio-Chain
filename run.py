import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path
import traceback

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
        print("❌ Gagal menginstal dependensi backend. Pastikan requirements.txt ada dan valid.")
        return
    except FileNotFoundError:
        print("❌ Python tidak ditemukan.")
        return
        
    # 2. Setup SQLite Database
    print_step("Inisialisasi Database SQLite & Seed Data...")
    env_vars = os.environ.copy()
    env_vars["PYTHONPATH"] = str(backend_dir)
    try:
        subprocess.run([sys.executable, "src/drop_tables.py"], 
                       cwd=backend_dir, env=env_vars, check=True)
        subprocess.run([sys.executable, "src/seed/seed_data.py"], 
                       cwd=backend_dir, env=env_vars, check=True)
    except subprocess.CalledProcessError:
        print("❌ Gagal inisialisasi database.")
        return
        
    # 3. Check / Install Frontend Dependencies
    print_step("Memeriksa dependensi Node.js (Frontend)...")
    try:
        if not (frontend_dir / "node_modules").exists():
            print("Menginstal package NPM (mungkin butuh beberapa saat)...")
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True, shell=True)
    except subprocess.CalledProcessError:
        print("❌ Gagal menginstal dependensi NPM. Pastikan koneksi internet stabil.")
        return
    except FileNotFoundError:
        print("❌ NPM tidak ditemukan. Pastikan Node.js sudah diinstal dari nodejs.org.")
        return
        
    # 4. Start Servers
    print_step("Menyalakan Server Backend, Frontend & Tunnel Publik...")
    
    # Backend Server (FastAPI)
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.main:app", "--port", "8000", "--reload"],
        cwd=backend_dir,
        env=env_vars
    )
    
    # Frontend Server (Vite)
    try:
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            shell=True
        )
        
        # Tunnel Server (Localtunnel) untuk integrasi Vercel
        tunnel_process = subprocess.Popen(
            ["npx", "localtunnel", "--port", "8000", "--subdomain", "biochain-opt-backend"],
            cwd=root_dir,
            shell=True
        )
    except FileNotFoundError:
         print("❌ NPM tidak ditemukan. Gagal menjalankan frontend & tunnel.")
         backend_process.terminate()
         return
    
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
        tunnel_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Menghentikan BioChain-Opt...")
        backend_process.terminate()
        frontend_process.terminate()
        tunnel_process.terminate()
        print("✅ Berhasil dihentikan.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\n❌ Terjadi kesalahan tak terduga:")
        traceback.print_exc()
    finally:
        # Pause before closing window on double click
        input("\nTekan Enter untuk menutup layar ini...")
