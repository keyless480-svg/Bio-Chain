"""
seed/seed_data.py — Populates the database with realistic BPS Jawa Timur data.

Sources:
- Kabupaten coordinates: BPS Jawa Timur (centroid of each district)
- Corn production data: BPS Statistik Pertanian 2023 (Produksi Jagung Jawa Timur)
  9 kabupaten sentra: Lamongan, Tuban, Bojonegoro, Bangkalan, Pamekasan,
  Sumenep, Jember, Banyuwangi, Probolinggo
- Simulated: Hub locations (KUD candidates), biorefinery locations, daily supply values
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from src.database import engine, init_db
from src.models.spatial import Farm, Hub, Biorefinery, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─────────────────────────────────────────────
# BPS Jawa Timur: Corn production data (2023)
# Coordinate: WGS84 (lon, lat) of kabupaten centroid
# Annual production converted to corncob biomass at ~0.28 ratio
# ─────────────────────────────────────────────
FARM_DATA = [
    # Madura Island — Major corncob suppliers
    {
        "name": "Lahan Jagung Bangkalan Utara",
        "kabupaten": "Bangkalan",
        "lon": 112.9848, "lat": -7.0583,
        "annual_supply_ton": 35420.0,   # ~35k ton corncob/year
        "corn_area_ha": 42500.0,
    },
    {
        "name": "Lahan Jagung Pamekasan Tengah",
        "kabupaten": "Pamekasan",
        "lon": 113.4705, "lat": -7.1575,
        "annual_supply_ton": 41200.0,
        "corn_area_ha": 49800.0,
    },
    {
        "name": "Lahan Jagung Sumenep Timur",
        "kabupaten": "Sumenep",
        "lon": 113.8655, "lat": -7.0156,
        "annual_supply_ton": 58900.0,
        "corn_area_ha": 71200.0,
    },
    {
        "name": "Lahan Jagung Sampang",
        "kabupaten": "Sampang",
        "lon": 113.2493, "lat": -7.1804,
        "annual_supply_ton": 28700.0,
        "corn_area_ha": 34600.0,
    },
    # North Coast (Pantura) — Lamongan, Tuban, Bojonegoro
    {
        "name": "Lahan Jagung Lamongan Selatan",
        "kabupaten": "Lamongan",
        "lon": 112.4145, "lat": -7.1230,
        "annual_supply_ton": 62800.0,   # Lamongan: top producer
        "corn_area_ha": 75600.0,
    },
    {
        "name": "Lahan Jagung Tuban Barat",
        "kabupaten": "Tuban",
        "lon": 111.9060, "lat": -6.8983,
        "annual_supply_ton": 71300.0,   # Tuban: highest production
        "corn_area_ha": 86000.0,
    },
    {
        "name": "Lahan Jagung Bojonegoro Utara",
        "kabupaten": "Bojonegoro",
        "lon": 111.8814, "lat": -7.1503,
        "annual_supply_ton": 54200.0,
        "corn_area_ha": 65500.0,
    },
    # East — Jember, Banyuwangi, Probolinggo
    {
        "name": "Lahan Jagung Jember Selatan",
        "kabupaten": "Jember",
        "lon": 113.7016, "lat": -8.1735,
        "annual_supply_ton": 48600.0,
        "corn_area_ha": 58700.0,
    },
    {
        "name": "Lahan Jagung Banyuwangi Barat",
        "kabupaten": "Banyuwangi",
        "lon": 114.3600, "lat": -8.2193,
        "annual_supply_ton": 39400.0,
        "corn_area_ha": 47600.0,
    },
    {
        "name": "Lahan Jagung Probolinggo Barat",
        "kabupaten": "Probolinggo",
        "lon": 113.2148, "lat": -7.7543,
        "annual_supply_ton": 33100.0,
        "corn_area_ha": 39900.0,
    },
]

# Candidate Hub locations (simulated KUD locations)
HUB_DATA = [
    {
        "name": "KUD Madura Hub — Bangkalan",
        "kabupaten": "Bangkalan",
        "lon": 112.7890, "lat": -7.0340,
        "max_capacity_ton_day": 120.0,
        "operating_cost_usd_day": 450.0,
    },
    {
        "name": "KUD Sumenep Hub — Sumenep",
        "kabupaten": "Sumenep",
        "lon": 113.8540, "lat": -7.0080,
        "max_capacity_ton_day": 180.0,
        "operating_cost_usd_day": 620.0,
    },
    {
        "name": "KUD Pantura Hub — Tuban",
        "kabupaten": "Tuban",
        "lon": 111.9000, "lat": -6.8850,
        "max_capacity_ton_day": 200.0,
        "operating_cost_usd_day": 720.0,
    },
    {
        "name": "KUD Pantura Hub — Lamongan",
        "kabupaten": "Lamongan",
        "lon": 112.4100, "lat": -7.1150,
        "max_capacity_ton_day": 150.0,
        "operating_cost_usd_day": 540.0,
    },
    {
        "name": "KUD Timur Hub — Jember",
        "kabupaten": "Jember",
        "lon": 113.6950, "lat": -8.1650,
        "max_capacity_ton_day": 130.0,
        "operating_cost_usd_day": 480.0,
    },
]

# Central Biorefinery locations (simulated: near industrial zones)
BIOREFINERY_DATA = [
    {
        "name": "Biorefinery Gresik — Kawasan Industri",
        "kabupaten": "Gresik",
        "lon": 112.6560, "lat": -7.1607,
        "max_capacity_ton_day": 500.0,
        "ethanol_yield_liter_per_ton": 280.0,
        "investment_cost_usd": 15_000_000.0,
    },
    {
        "name": "Biorefinery Tuban — Kawasan Industri",
        "kabupaten": "Tuban",
        "lon": 111.9020, "lat": -6.9050,
        "max_capacity_ton_day": 400.0,
        "ethanol_yield_liter_per_ton": 280.0,
        "investment_cost_usd": 12_000_000.0,
    },
]

# Demo users per role
USERS_DATA = [
    {
        "username": "analis_esdm",
        "email": "analis@esdm.go.id",
        "password": "biochain2026",
        "role": "analyst",
        "full_name": "Analis Kebijakan ESDM",
        "kabupaten": None,
    },
    {
        "username": "petani_tuban",
        "email": "petani@tuban.com",
        "password": "jagung123",
        "role": "farmer",
        "full_name": "Pak Sugeng Petani",
        "kabupaten": "Tuban",
    },
    {
        "username": "pengepul_kud",
        "email": "kud@bangkalan.com",
        "password": "kud2026",
        "role": "collector",
        "full_name": "Bu Siti Pengepul KUD",
        "kabupaten": "Bangkalan",
    },
    {
        "username": "sopir_truk",
        "email": "sopir@logistik.com",
        "password": "truk2026",
        "role": "driver",
        "full_name": "Pak Budi Sopir",
        "kabupaten": None,
    },
]


def seed() -> None:
    """Insert all seed data into the database."""
    init_db()

    with Session(engine) as db:
        # Check if already seeded
        if db.query(Farm).count() > 0:
            print("✓ Database already seeded. Skipping.")
            return

        print("🌱 Seeding Farm data...")
        for data in FARM_DATA:
            farm = Farm(
                name=data["name"],
                kabupaten=data["kabupaten"],
                latitude=data["lat"],
                longitude=data["lon"],
                annual_supply_ton=data["annual_supply_ton"],
                daily_supply_ton=round(data["annual_supply_ton"] / 365, 2),
                corn_area_ha=data.get("corn_area_ha"),
            )
            db.add(farm)

        print("🏭 Seeding Hub data...")
        for data in HUB_DATA:
            hub = Hub(
                name=data["name"],
                kabupaten=data["kabupaten"],
                latitude=data["lat"],
                longitude=data["lon"],
                max_capacity_ton_day=data["max_capacity_ton_day"],
                current_load_ton=0.0,
                is_active=True,
                operating_cost_usd_day=data["operating_cost_usd_day"],
            )
            db.add(hub)

        print("⚗️  Seeding Biorefinery data...")
        for data in BIOREFINERY_DATA:
            bioref = Biorefinery(
                name=data["name"],
                kabupaten=data["kabupaten"],
                latitude=data["lat"],
                longitude=data["lon"],
                max_capacity_ton_day=data["max_capacity_ton_day"],
                ethanol_yield_liter_per_ton=data["ethanol_yield_liter_per_ton"],
                investment_cost_usd=data["investment_cost_usd"],
            )
            db.add(bioref)

        print("👤 Seeding User data...")
        for data in USERS_DATA:
            user = User(
                username=data["username"],
                email=data["email"],
                hashed_password=pwd_context.hash(data["password"]),
                role=data["role"],
                full_name=data["full_name"],
                kabupaten=data.get("kabupaten"),
                is_active=True,
            )
            db.add(user)

        db.commit()
        print("✅ Seeding complete!")


if __name__ == "__main__":
    seed()
