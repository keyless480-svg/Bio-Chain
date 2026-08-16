# BioChain-Opt 🌿

> **Decision Support System** untuk optimasi rantai pasok bioetanol generasi kedua (2G) dari tongkol jagung di Jawa Timur menggunakan **MILP Hub-and-Spoke** via Pyomo.

*Greenovate Challenge 2026 — Inovasi Penunjang*

---

## Arsitektur Sistem

```
React PWA (Port 80/5173)  ←→  FastAPI Backend (Port 8000)  ←→  PostgreSQL+PostGIS (Port 5432)
                                     ↓
                          Pyomo MILP (CBC Solver)
                          GeoPandas (Matriks Jarak)
```

## Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| 🗺️ Geo-Mapping | Peta interaktif Leaflet: farm, KUD, biorefinery di Jawa Timur |
| ⚙️ MILP Engine | Solver CBC via Pyomo — minimasi TAC (Total Annual Cost) |
| 📊 Scenario Builder | Slider pajak karbon, kapasitas, batas emisi real-time |
| 📱 PWA Android | Installable di Android via "Tambahkan ke Layar Utama" |
| 👥 Multi-Role UI | Petani / Pengepul KUD / Sopir Truk / Analis |
| 🔐 JWT Auth | Role-based access control per jenis pengguna |

## Cara Menjalankan

### Dengan Docker Compose (Direkomendasikan)

```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Jalankan semua layanan
docker-compose up --build

# 3. Buka di browser
open http://localhost
```

### Development Mode (Lokal)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
# Pastikan PostgreSQL+PostGIS jalan di localhost:5432
python src/seed/seed_data.py   # Seed data BPS Jawa Timur
uvicorn src.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

## Akun Demo

| Peran | Username | Password |
|-------|----------|----------|
| Analis / ESDM | `analis_esdm` | `biochain2026` |
| Petani Jagung | `petani_tuban` | `jagung123` |
| Pengepul KUD | `pengepul_bangkalan` | `kud2026` |
| Sopir Truk | `sopir_01` | `truk2026` |

## Model MILP

**Fungsi Objektif:** Minimasi TAC = Biaya Transportasi + Biaya Operasional Hub + Pajak Karbon

**Variabel Keputusan:**
- `x[i,j]` — aliran tongkol (ton/hari) dari farm `i` ke hub `j` (kontinu)
- `w[j,k]` — aliran dari hub `j` ke biorefinery `k` (kontinu)
- `y[j]`   — buka/tutup hub `j` (biner)

**Solver:** CBC (open-source) | Timeout: 300 detik | Default pajak karbon: $0.03/kg CO₂

## Data Sumber

- **Koordinat Kabupaten:** BPS Jawa Timur (9 kabupaten sentra jagung)
- **Produksi Jagung:** BPS Statistik Pertanian 2023
- **Emisi Truk:** IPCC Tier 2 (2.68 kg CO₂/liter diesel)
- **Nilai Ekonomi Karbon:** Perpres No. 98/2021 (NEK)

## Stack Teknologi

- **Backend:** Python 3.11, FastAPI, Pyomo, GeoPandas, SQLAlchemy, GeoAlchemy2
- **Database:** PostgreSQL 15 + PostGIS 3.3
- **Frontend:** React 18, Vite, Leaflet, Recharts, Zustand
- **PWA:** vite-plugin-pwa + Workbox
- **Solver:** CBC (coinor-cbc)
- **Deployment:** Docker Compose + Nginx

---

*Made with 💚 for sustainable bioethanol supply chain in East Java*
