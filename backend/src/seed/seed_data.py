"""
seed/seed_data.py — Populates the database with realistic BPS Jawa Timur data.
5-Step Circular Flow: 10 Petani, 5 Pengepul, 1 Pabrik, 22 Users, dummy transactions.

Sources:
- Kabupaten coordinates: BPS Jawa Timur (centroid of each district)
- Corn production data: BPS Statistik Pertanian 2023
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from datetime import date, timedelta
import random
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from src.database import engine, init_db
from src.models.spatial import Farmer, Hub, Factory, User
from src.models.transactions import Harvest, HubBatch, Shipment, FactoryHppLog, CircularityLog
from src.models.fleet import Vehicle

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ═══════════════════════════════════════════
# STEP 1: 10 PETANI (Farmers)
# ═══════════════════════════════════════════
FARMER_DATA = [
    {
        "name": "Petani Jagung Bangkalan Utara",
        "kabupaten": "Bangkalan",
        "lon": 112.9848, "lat": -7.0583,
        "annual_supply_ton": 35420.0,
        "corn_area_ha": 42500.0,
        "initial_moisture_pct": 38.0,
        "harvest_cost_per_ton": 145000.0,
        "packing_cost_per_ton": 22000.0,
        "supply_variability": 0.12,
    },
    {
        "name": "Petani Jagung Pamekasan Tengah",
        "kabupaten": "Pamekasan",
        "lon": 113.4705, "lat": -7.1575,
        "annual_supply_ton": 41200.0,
        "corn_area_ha": 49800.0,
        "initial_moisture_pct": 36.0,
        "harvest_cost_per_ton": 155000.0,
        "packing_cost_per_ton": 24000.0,
        "supply_variability": 0.09,
    },
    {
        "name": "Petani Jagung Sumenep Timur",
        "kabupaten": "Sumenep",
        "lon": 113.8655, "lat": -7.0156,
        "annual_supply_ton": 58900.0,
        "corn_area_ha": 71200.0,
        "initial_moisture_pct": 37.0,
        "harvest_cost_per_ton": 140000.0,
        "packing_cost_per_ton": 23000.0,
        "supply_variability": 0.11,
    },
    {
        "name": "Petani Jagung Sampang",
        "kabupaten": "Sampang",
        "lon": 113.2493, "lat": -7.1804,
        "annual_supply_ton": 28700.0,
        "corn_area_ha": 34600.0,
        "initial_moisture_pct": 39.0,
        "harvest_cost_per_ton": 160000.0,
        "packing_cost_per_ton": 26000.0,
        "supply_variability": 0.15,
    },
    {
        "name": "Petani Jagung Lamongan Selatan",
        "kabupaten": "Lamongan",
        "lon": 112.4145, "lat": -7.1230,
        "annual_supply_ton": 62800.0,
        "corn_area_ha": 75600.0,
        "initial_moisture_pct": 36.0,
        "harvest_cost_per_ton": 148000.0,
        "packing_cost_per_ton": 24000.0,
        "supply_variability": 0.08,
    },
    {
        "name": "Petani Jagung Tuban Barat",
        "kabupaten": "Tuban",
        "lon": 111.9060, "lat": -6.8983,
        "annual_supply_ton": 71300.0,
        "corn_area_ha": 86000.0,
        "initial_moisture_pct": 35.0,
        "harvest_cost_per_ton": 142000.0,
        "packing_cost_per_ton": 22000.0,
        "supply_variability": 0.07,
    },
    {
        "name": "Petani Jagung Bojonegoro Utara",
        "kabupaten": "Bojonegoro",
        "lon": 111.8814, "lat": -7.1503,
        "annual_supply_ton": 54200.0,
        "corn_area_ha": 65500.0,
        "initial_moisture_pct": 37.0,
        "harvest_cost_per_ton": 150000.0,
        "packing_cost_per_ton": 25000.0,
        "supply_variability": 0.10,
    },
    {
        "name": "Petani Jagung Jember Selatan",
        "kabupaten": "Jember",
        "lon": 113.7016, "lat": -8.1735,
        "annual_supply_ton": 48600.0,
        "corn_area_ha": 58700.0,
        "initial_moisture_pct": 38.0,
        "harvest_cost_per_ton": 155000.0,
        "packing_cost_per_ton": 26000.0,
        "supply_variability": 0.13,
    },
    {
        "name": "Petani Jagung Banyuwangi Barat",
        "kabupaten": "Banyuwangi",
        "lon": 114.3600, "lat": -8.2193,
        "annual_supply_ton": 39400.0,
        "corn_area_ha": 47600.0,
        "initial_moisture_pct": 36.0,
        "harvest_cost_per_ton": 152000.0,
        "packing_cost_per_ton": 24000.0,
        "supply_variability": 0.09,
    },
    {
        "name": "Petani Jagung Probolinggo Barat",
        "kabupaten": "Probolinggo",
        "lon": 113.2148, "lat": -7.7543,
        "annual_supply_ton": 33100.0,
        "corn_area_ha": 39900.0,
        "initial_moisture_pct": 37.0,
        "harvest_cost_per_ton": 158000.0,
        "packing_cost_per_ton": 25000.0,
        "supply_variability": 0.14,
    },
]

# ═══════════════════════════════════════════
# STEP 2: 5 PENGEPUL (Hubs)
# ═══════════════════════════════════════════
HUB_DATA = [
    {
        "name": "Pengepul KUD Madura — Bangkalan",
        "kabupaten": "Bangkalan",
        "lon": 112.7890, "lat": -7.0340,
        "max_capacity_ton_day": 120.0,
        "warehouse_area_m2": 400.0,
        "loading_cost_per_ton": 32000.0,
        "drying_energy_cost_per_ton": 12000.0,
        "storage_cost_per_m2_day": 450.0,
        "operating_cost_per_day": 680000.0,
        "shrinkage_rate": 0.19,
        "target_moisture_pct": 14.0,
        "supply_variability": 0.10,
    },
    {
        "name": "Pengepul KUD Sumenep",
        "kabupaten": "Sumenep",
        "lon": 113.8540, "lat": -7.0080,
        "max_capacity_ton_day": 180.0,
        "warehouse_area_m2": 600.0,
        "loading_cost_per_ton": 35000.0,
        "drying_energy_cost_per_ton": 14000.0,
        "storage_cost_per_m2_day": 500.0,
        "operating_cost_per_day": 820000.0,
        "shrinkage_rate": 0.17,
        "target_moisture_pct": 13.5,
        "supply_variability": 0.08,
    },
    {
        "name": "Pengepul KUD Pantura — Tuban",
        "kabupaten": "Tuban",
        "lon": 111.9000, "lat": -6.8850,
        "max_capacity_ton_day": 200.0,
        "warehouse_area_m2": 700.0,
        "loading_cost_per_ton": 38000.0,
        "drying_energy_cost_per_ton": 16000.0,
        "storage_cost_per_m2_day": 520.0,
        "operating_cost_per_day": 950000.0,
        "shrinkage_rate": 0.16,
        "target_moisture_pct": 14.0,
        "supply_variability": 0.06,
    },
    {
        "name": "Pengepul KUD Pantura — Lamongan",
        "kabupaten": "Lamongan",
        "lon": 112.4100, "lat": -7.1150,
        "max_capacity_ton_day": 150.0,
        "warehouse_area_m2": 500.0,
        "loading_cost_per_ton": 34000.0,
        "drying_energy_cost_per_ton": 13000.0,
        "storage_cost_per_m2_day": 480.0,
        "operating_cost_per_day": 750000.0,
        "shrinkage_rate": 0.18,
        "target_moisture_pct": 14.0,
        "supply_variability": 0.07,
    },
    {
        "name": "Pengepul KUD Timur — Jember",
        "kabupaten": "Jember",
        "lon": 113.6950, "lat": -8.1650,
        "max_capacity_ton_day": 130.0,
        "warehouse_area_m2": 450.0,
        "loading_cost_per_ton": 33000.0,
        "drying_energy_cost_per_ton": 14000.0,
        "storage_cost_per_m2_day": 460.0,
        "operating_cost_per_day": 700000.0,
        "shrinkage_rate": 0.20,
        "target_moisture_pct": 14.0,
        "supply_variability": 0.09,
    },
]

# ═══════════════════════════════════════════
# STEP 4: 1 PABRIK (Factory)
# ═══════════════════════════════════════════
FACTORY_DATA = [
    {
        "name": "Pabrik Bioetanol Gresik — Kawasan Industri",
        "kabupaten": "Gresik",
        "lon": 112.6560, "lat": -7.1607,
        "max_capacity_ton_day": 500.0,
        "ethanol_yield_liter_per_ton": 280.0,
        "processing_cost_per_ton": 850000.0,
        "depreciation_cost_per_day": 12500000.0,
        "investment_cost": 232500000000.0,  # ~Rp 232.5M (≈$15M)
    },
]

# ═══════════════════════════════════════════
# USERS: 22 users (1 admin + 1 analyst + 10 farmers + 5 hubs + 5 drivers)
# ═══════════════════════════════════════════
USERS_DATA = [
    # Admin
    {"username": "admin", "email": "admin@biochain.id", "password": "admin2026",
     "role": "admin", "full_name": "Administrator Sistem", "kabupaten": None, "phone": "08123456789"},
    # Analyst
    {"username": "analis_esdm", "email": "analis@esdm.go.id", "password": "biochain2026",
     "role": "analyst", "full_name": "Analis Kebijakan ESDM", "kabupaten": None, "phone": "08111222333"},
    # 10 Farmers
    {"username": "petani_bangkalan", "email": "petani1@biochain.id", "password": "jagung123",
     "role": "farmer", "full_name": "Pak Sugeng", "kabupaten": "Bangkalan", "phone": "08221001001", "farmer_id": 1},
    {"username": "petani_pamekasan", "email": "petani2@biochain.id", "password": "jagung123",
     "role": "farmer", "full_name": "Pak Hadi", "kabupaten": "Pamekasan", "phone": "08221001002", "farmer_id": 2},
    {"username": "petani_sumenep", "email": "petani3@biochain.id", "password": "jagung123",
     "role": "farmer", "full_name": "Bu Sari", "kabupaten": "Sumenep", "phone": "08221001003", "farmer_id": 3},
    {"username": "petani_sampang", "email": "petani4@biochain.id", "password": "jagung123",
     "role": "farmer", "full_name": "Pak Joko", "kabupaten": "Sampang", "phone": "08221001004", "farmer_id": 4},
    {"username": "petani_lamongan", "email": "petani5@biochain.id", "password": "jagung123",
     "role": "farmer", "full_name": "Pak Wahyu", "kabupaten": "Lamongan", "phone": "08221001005", "farmer_id": 5},
    {"username": "petani_tuban", "email": "petani6@biochain.id", "password": "jagung123",
     "role": "farmer", "full_name": "Pak Bambang", "kabupaten": "Tuban", "phone": "08221001006", "farmer_id": 6},
    {"username": "petani_bojonegoro", "email": "petani7@biochain.id", "password": "jagung123",
     "role": "farmer", "full_name": "Pak Darto", "kabupaten": "Bojonegoro", "phone": "08221001007", "farmer_id": 7},
    {"username": "petani_jember", "email": "petani8@biochain.id", "password": "jagung123",
     "role": "farmer", "full_name": "Bu Ningsih", "kabupaten": "Jember", "phone": "08221001008", "farmer_id": 8},
    {"username": "petani_banyuwangi", "email": "petani9@biochain.id", "password": "jagung123",
     "role": "farmer", "full_name": "Pak Surya", "kabupaten": "Banyuwangi", "phone": "08221001009", "farmer_id": 9},
    {"username": "petani_probolinggo", "email": "petani10@biochain.id", "password": "jagung123",
     "role": "farmer", "full_name": "Pak Rudi", "kabupaten": "Probolinggo", "phone": "08221001010", "farmer_id": 10},
    # 5 Hub operators
    {"username": "pengepul_bangkalan", "email": "hub1@biochain.id", "password": "kud2026",
     "role": "hub", "full_name": "Bu Siti KUD Bangkalan", "kabupaten": "Bangkalan", "phone": "08331001001", "hub_id": 1},
    {"username": "pengepul_sumenep", "email": "hub2@biochain.id", "password": "kud2026",
     "role": "hub", "full_name": "Pak Ahmad KUD Sumenep", "kabupaten": "Sumenep", "phone": "08331001002", "hub_id": 2},
    {"username": "pengepul_tuban", "email": "hub3@biochain.id", "password": "kud2026",
     "role": "hub", "full_name": "Bu Dewi KUD Tuban", "kabupaten": "Tuban", "phone": "08331001003", "hub_id": 3},
    {"username": "pengepul_lamongan", "email": "hub4@biochain.id", "password": "kud2026",
     "role": "hub", "full_name": "Pak Eko KUD Lamongan", "kabupaten": "Lamongan", "phone": "08331001004", "hub_id": 4},
    {"username": "pengepul_jember", "email": "hub5@biochain.id", "password": "kud2026",
     "role": "hub", "full_name": "Pak Wawan KUD Jember", "kabupaten": "Jember", "phone": "08331001005", "hub_id": 5},
    # 5 Drivers
    {"username": "sopir_01", "email": "sopir1@biochain.id", "password": "truk2026",
     "role": "driver", "full_name": "Pak Budi Sopir", "kabupaten": None, "phone": "08441001001"},
    {"username": "sopir_02", "email": "sopir2@biochain.id", "password": "truk2026",
     "role": "driver", "full_name": "Pak Agus Sopir", "kabupaten": None, "phone": "08441001002"},
    {"username": "sopir_03", "email": "sopir3@biochain.id", "password": "truk2026",
     "role": "driver", "full_name": "Pak Dedi Sopir", "kabupaten": None, "phone": "08441001003"},
    {"username": "sopir_04", "email": "sopir4@biochain.id", "password": "truk2026",
     "role": "driver", "full_name": "Pak Iwan Sopir", "kabupaten": None, "phone": "08441001004"},
    {"username": "sopir_05", "email": "sopir5@biochain.id", "password": "truk2026",
     "role": "driver", "full_name": "Pak Udin Sopir", "kabupaten": None, "phone": "08441001005"},
]


# ═══════════════════════════════════════════
# ARMADA: 2 kendaraan per hub (10 total) — raw input demo untuk Lapis 2 CVRP
# ═══════════════════════════════════════════
VEHICLE_DATA = [
    {"hub_id": 1, "vehicle_type": "engkel", "plate_number": "L 1001 KD", "capacity_ton": 5.0, "fuel_rate_l_per_km": 0.18, "fixed_charter_cost": 250000.0},
    {"hub_id": 1, "vehicle_type": "fuso", "plate_number": "L 1002 KD", "capacity_ton": 8.0, "fuel_rate_l_per_km": 0.28, "fixed_charter_cost": 400000.0},
    {"hub_id": 2, "vehicle_type": "engkel", "plate_number": "L 2001 KD", "capacity_ton": 5.0, "fuel_rate_l_per_km": 0.18, "fixed_charter_cost": 250000.0},
    {"hub_id": 2, "vehicle_type": "wingbox", "plate_number": "L 2002 KD", "capacity_ton": 20.0, "fuel_rate_l_per_km": 0.35, "fixed_charter_cost": 700000.0},
    {"hub_id": 3, "vehicle_type": "engkel", "plate_number": "L 3001 KD", "capacity_ton": 5.0, "fuel_rate_l_per_km": 0.18, "fixed_charter_cost": 250000.0},
    {"hub_id": 3, "vehicle_type": "fuso", "plate_number": "L 3002 KD", "capacity_ton": 8.0, "fuel_rate_l_per_km": 0.28, "fixed_charter_cost": 400000.0},
    {"hub_id": 4, "vehicle_type": "pickup", "plate_number": "L 4001 KD", "capacity_ton": 1.0, "fuel_rate_l_per_km": 0.10, "fixed_charter_cost": 120000.0},
    {"hub_id": 4, "vehicle_type": "engkel", "plate_number": "L 4002 KD", "capacity_ton": 5.0, "fuel_rate_l_per_km": 0.18, "fixed_charter_cost": 250000.0},
    {"hub_id": 5, "vehicle_type": "engkel", "plate_number": "L 5001 KD", "capacity_ton": 5.0, "fuel_rate_l_per_km": 0.18, "fixed_charter_cost": 250000.0},
    {"hub_id": 5, "vehicle_type": "fuso", "plate_number": "L 5002 KD", "capacity_ton": 8.0, "fuel_rate_l_per_km": 0.28, "fixed_charter_cost": 400000.0},
]


def _seed_vehicles_if_needed(db: Session) -> None:
    """Independen dari guard seed() utama — supaya DB yang sudah pernah di-seed
    (mis. Supabase produksi) tetap mendapat data armada demo setelah redeploy."""
    if db.query(Vehicle).count() > 0:
        return
    print("[Fleet] Seeding 10 demo Vehicle (2 per hub)...")
    for data in VEHICLE_DATA:
        db.add(Vehicle(
            owner_hub_id=data["hub_id"],
            vehicle_type=data["vehicle_type"],
            plate_number=data["plate_number"],
            capacity_ton=data["capacity_ton"],
            fuel_rate_l_per_km=data["fuel_rate_l_per_km"],
            fixed_charter_cost=data["fixed_charter_cost"],
            is_available_today=True,
        ))
    db.commit()


def seed() -> None:
    """Insert all seed data into the database."""
    init_db()

    with Session(engine) as db:
        _seed_vehicles_if_needed(db)

        # Check if already seeded
        if db.query(Farmer).count() > 0:
            print("[OK] Database already seeded. Skipping.")
            return

        print("[1/6] Seeding 10 Farmer data...")
        for data in FARMER_DATA:
            farmer = Farmer(
                name=data["name"],
                kabupaten=data["kabupaten"],
                latitude=data["lat"],
                longitude=data["lon"],
                annual_supply_ton=data["annual_supply_ton"],
                daily_supply_ton=round(data["annual_supply_ton"] / 365, 2),
                corn_area_ha=data.get("corn_area_ha"),
                initial_moisture_pct=data["initial_moisture_pct"],
                harvest_cost_per_ton=data["harvest_cost_per_ton"],
                packing_cost_per_ton=data["packing_cost_per_ton"],
                supply_variability=data["supply_variability"],
            )
            db.add(farmer)

        print("[2/6] Seeding 5 Hub data...")
        for data in HUB_DATA:
            hub = Hub(
                name=data["name"],
                kabupaten=data["kabupaten"],
                latitude=data["lat"],
                longitude=data["lon"],
                max_capacity_ton_day=data["max_capacity_ton_day"],
                warehouse_area_m2=data["warehouse_area_m2"],
                loading_cost_per_ton=data["loading_cost_per_ton"],
                drying_energy_cost_per_ton=data["drying_energy_cost_per_ton"],
                storage_cost_per_m2_day=data["storage_cost_per_m2_day"],
                operating_cost_per_day=data["operating_cost_per_day"],
                shrinkage_rate=data["shrinkage_rate"],
                target_moisture_pct=data["target_moisture_pct"],
                supply_variability=data["supply_variability"],
                current_load_ton=0.0,
                is_active=True,
            )
            db.add(hub)

        print("[3/6] Seeding 1 Factory data...")
        for data in FACTORY_DATA:
            factory = Factory(
                name=data["name"],
                kabupaten=data["kabupaten"],
                latitude=data["lat"],
                longitude=data["lon"],
                max_capacity_ton_day=data["max_capacity_ton_day"],
                ethanol_yield_liter_per_ton=data["ethanol_yield_liter_per_ton"],
                processing_cost_per_ton=data["processing_cost_per_ton"],
                depreciation_cost_per_day=data["depreciation_cost_per_day"],
                investment_cost=data["investment_cost"],
            )
            db.add(factory)

        print("[4/6] Seeding 22 User accounts...")
        for data in USERS_DATA:
            user = User(
                username=data["username"],
                email=data["email"],
                hashed_password=pwd_context.hash(data["password"]),
                role=data["role"],
                full_name=data["full_name"],
                kabupaten=data.get("kabupaten"),
                phone=data.get("phone"),
                farmer_id=data.get("farmer_id"),
                hub_id=data.get("hub_id"),
                is_active=True,
            )
            db.add(user)

        db.commit()  # Commit entities so IDs are assigned

        print("[5/6] Seeding dummy transactions...")
        today = date.today()
        random.seed(42)  # Deterministic

        # Dummy harvests (last 7 days, 3-5 per day)
        for day_offset in range(7):
            d = today - timedelta(days=day_offset)
            num_harvests = random.randint(3, 5)
            for _ in range(num_harvests):
                farmer_id = random.randint(1, 10)
                farmer = FARMER_DATA[farmer_id - 1]
                weight = random.randint(500, 2500)
                moisture = farmer["initial_moisture_pct"] + random.uniform(-2, 2)
                price = 850
                harvest = Harvest(
                    farmer_id=farmer_id,
                    gross_weight_kg=weight,
                    initial_moisture_pct=round(moisture, 1),
                    harvest_cost=round(weight / 1000 * farmer["harvest_cost_per_ton"]),
                    packing_cost=round(weight / 1000 * farmer["packing_cost_per_ton"]),
                    total_cost=round(weight / 1000 * (farmer["harvest_cost_per_ton"] + farmer["packing_cost_per_ton"])),
                    price_per_kg=price,
                    total_payment=weight * price,
                    harvest_date=d,
                    destination_hub_id=random.randint(1, 5),
                    status="delivered",
                    geo_lat=farmer["lat"] + random.uniform(-0.01, 0.01),
                    geo_long=farmer["lon"] + random.uniform(-0.01, 0.01),
                )
                db.add(harvest)

        # Dummy hub batches (last 5 days)
        batch_counter = 0
        for day_offset in range(5):
            d = today - timedelta(days=day_offset)
            for hub_id in range(1, 6):
                hub = HUB_DATA[hub_id - 1]
                total_input = random.randint(3000, 8000)
                shrinkage = hub["shrinkage_rate"]
                final_weight = round(total_input * (1 - shrinkage))
                batch_counter += 1
                batch = HubBatch(
                    hub_id=hub_id,
                    batch_code=f"BATCH-{d.strftime('%y%m%d')}-H{hub_id:02d}-{batch_counter:03d}",
                    total_input_kg=total_input,
                    input_moisture_pct=37.0,
                    num_farmers=random.randint(2, 4),
                    final_weight_kg=final_weight,
                    final_moisture_pct=hub["target_moisture_pct"],
                    shrinkage_kg=total_input - final_weight,
                    shrinkage_pct=round(shrinkage * 100, 1),
                    loading_cost=round(total_input / 1000 * hub["loading_cost_per_ton"]),
                    drying_cost=round(total_input / 1000 * hub["drying_energy_cost_per_ton"]),
                    storage_cost=round(hub["warehouse_area_m2"] * hub["storage_cost_per_m2_day"]),
                    shrinkage_cost=round((total_input - final_weight) * 850),
                    total_handling_cost=round(
                        total_input / 1000 * (hub["loading_cost_per_ton"] + hub["drying_energy_cost_per_ton"])
                        + hub["warehouse_area_m2"] * hub["storage_cost_per_m2_day"]
                        + (total_input - final_weight) * 850
                    ),
                    quality_grade=random.choice(["A", "A", "A", "B"]),
                    status="ready",
                    batch_date=d,
                    ready_date=d + timedelta(days=1),
                )
                db.add(batch)

        # Dummy shipments (last 3 days)
        shipment_counter = 0
        for day_offset in range(3):
            d = today - timedelta(days=day_offset)
            for hub_id in random.sample(range(1, 6), 3):
                hub = HUB_DATA[hub_id - 1]
                payload = random.uniform(16, 20)
                distance = random.uniform(40, 180)
                fuel = distance * 0.35 * 6800
                toll = distance * 450
                carbon = distance * 0.35 * 2.68
                shipment_counter += 1
                shipment = Shipment(
                    hub_batch_id=shipment_counter,
                    hub_id=hub_id,
                    factory_id=1,
                    truck_plate=f"L {random.randint(1000,9999)} AB",
                    driver_name=f"Sopir-{random.randint(1,5):02d}",
                    truck_capacity_ton=20.0,
                    payload_ton=round(payload, 1),
                    truck_utilization_pct=round(payload / 20 * 100, 1),
                    distance_km=round(distance, 1),
                    estimated_duration_hours=round(distance / 50, 1),
                    fuel_cost=round(fuel),
                    toll_cost=round(toll),
                    driver_cost=350000,
                    total_transport_cost=round(fuel + toll + 350000),
                    carbon_emitted_kg=round(carbon, 2),
                    carbon_tax_cost=round(carbon * 465),
                    status="delivered",
                    shipment_date=d,
                )
                db.add(shipment)

        # Dummy factory HPP logs
        for i in range(1, shipment_counter + 1):
            weight_received = random.uniform(15000, 19500)
            acquisition = weight_received * 850
            transport = random.uniform(500000, 1500000)
            processing = weight_received / 1000 * 850000
            depreciation = 12500000 / 3  # Pro-rata per batch
            total = acquisition + transport + processing + depreciation
            hpp_log = FactoryHppLog(
                shipment_id=i,
                factory_id=1,
                net_weight_received_kg=round(weight_received),
                acquisition_cost=round(acquisition),
                transport_cost=round(transport),
                processing_cost=round(processing),
                depreciation_cost=round(depreciation),
                total_cost=round(total),
                total_hpp_per_kg=round(total / weight_received),
                ethanol_produced_liter=round(weight_received / 1000 * 280),
                hpp_per_liter_ethanol=round(total / (weight_received / 1000 * 280)),
                farmer_share_pct=round(acquisition / total * 100, 1),
                hub_share_pct=round((total - acquisition - processing - depreciation) / total * 100, 1),
                received_date=today - timedelta(days=random.randint(0, 3)),
                quality_sample_result="pass",
            )
            db.add(hpp_log)

        # Dummy circularity logs (pupuk dari pabrik ke petani)
        for farmer_id in random.sample(range(1, 11), 5):
            circ = CircularityLog(
                source_type="factory",
                source_id=1,
                destination_farmer_id=farmer_id,
                product_type=random.choice(["pupuk_silika", "karbon_aktif", "kompos"]),
                quantity_kg=random.randint(100, 500),
                production_cost=random.randint(50000, 150000),
                market_value=random.randint(200000, 600000),
                farmer_saving=random.randint(150000, 450000),
                is_backhaul=True,
                transport_cost=0,
                delivery_date=today - timedelta(days=random.randint(0, 7)),
                status="received",
            )
            db.add(circ)

        db.commit()
        print("[6/6] Seeding complete! 22 users, 10 farmers, 5 hubs, 1 factory + transactions.")


if __name__ == "__main__":
    seed()
