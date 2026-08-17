"""
config.py — Application settings loaded from environment variables.
Uses pydantic-settings for type-safe configuration.
All monetary defaults in IDR (Rupiah).
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:////tmp/biochain.db"

    # Security / JWT
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 hours for operational users

    # Optimization
    solver_timeout: int = 300
    milp_solver: str = "appsi_highs"
    # Green & Resilience weights
    lambda_green: float = 465.0          # IDR per kg CO2 (NEK Indonesia ~$0.03 × 15500)
    gamma_resilience: float = 500000.0   # IDR penalty per unit risk
    # Transport defaults
    diesel_price_per_liter: float = 6800.0   # Rp/liter Pertamina Dex
    truck_fuel_per_km: float = 0.35          # liter/km
    truck_capacity_ton: float = 20.0         # ton
    truck_min_utilization_pct: float = 0.95  # 95%
    co2_per_liter_diesel: float = 2.68       # kg CO2/liter
    toll_cost_per_km: float = 450.0          # Rp/km estimate
    driver_cost_per_trip: float = 350000.0   # Rp/trip (upah + uang makan)
    road_factor: float = 1.4                 # Haversine → road distance
    # Shrinkage & Buffer
    default_shrinkage_rate: float = 0.18     # 18% moisture loss
    buffer_stock_min_pct: float = 0.20       # 20% minimum
    # Corn price
    corn_price_per_kg: float = 850.0         # Rp/kg (harga beli tongkol)

    # CVRP / Lapis 2 — Vehicle Routing (Green-VRP + VRPTW)
    avg_truck_speed_kmph: float = 40.0                 # Kecepatan rata-rata jalan kabupaten
    degradation_rate_pct_per_hour: float = 0.4         # Kenaikan kadar air per jam tunggu (empiris)
    time_window_early_penalty_per_min: float = 500.0   # IDR/menit datang kepagian
    time_window_late_penalty_per_min: float = 1500.0   # IDR/menit datang kesorean
    factory_sla_penalty_per_min: float = 5000.0        # IDR/menit — pelanggaran SLA kontraktual pabrik
    factory_sla_deadline_minutes: int = 600            # batas waktu kedatangan ke pabrik (menit sejak start-of-day)
    cvrp_solver_time_limit_seconds: int = 20
    hub_window_open_min: int = 360                     # 06:00 — jam operasional default gudang pengepul
    hub_window_close_min: int = 1080                    # 18:00

    # CORS
    cors_origins: list[str] = ["*"]

    # Environment
    environment: str = "development"
    
    # Missing fields from .env
    carbon_tax_default: float = 0.03
    backend_url: str = "http://localhost:8000"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
