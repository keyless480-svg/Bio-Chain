"""
models/spatial.py — ORM models for supply chain nodes and users.
5-Step Circular Flow: Farmers(10) → Hubs(5) → Transport → Factory(1) → Circularity
All monetary values in IDR (Rupiah).
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.sql import func
from src.database import Base


class Farmer(Base):
    """
    Langkah 1 — Hulu: Petani Jagung (Source & Primary Sorting).
    10 titik petani di Jawa Timur.
    """
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    kabupaten = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    # Production
    annual_supply_ton = Column(Float, nullable=False)
    daily_supply_ton = Column(Float, nullable=False)
    corn_area_ha = Column(Float, nullable=True)
    initial_moisture_pct = Column(Float, default=37.0)  # Kadar air awal 35-40%
    # ABC Cost Components (IDR)
    harvest_cost_per_ton = Column(Float, default=150000.0)  # Rp/ton tenaga panen
    packing_cost_per_ton = Column(Float, default=25000.0)   # Rp/ton karung goni reusable
    # Resilience
    supply_variability = Column(Float, default=0.1)  # Std dev / mean historis (0-1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Hub(Base):
    """
    Langkah 2 — Konsolidasi: Pengepul / Cross-Docking Hub.
    5 titik pengepul dengan quality control & pengeringan.
    """
    __tablename__ = "hubs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    kabupaten = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    # Capacity
    max_capacity_ton_day = Column(Float, nullable=False)
    current_load_ton = Column(Float, default=0.0)
    warehouse_area_m2 = Column(Float, default=500.0)
    # ABC Cost Components (IDR)
    loading_cost_per_ton = Column(Float, default=35000.0)     # Rp/ton bongkar muat
    drying_energy_cost_per_ton = Column(Float, default=15000.0)  # Rp/ton oven biomassa (rendah, self-sustained)
    storage_cost_per_m2_day = Column(Float, default=500.0)    # Rp/m²/hari sewa gudang
    operating_cost_per_day = Column(Float, default=750000.0)  # Rp/hari overhead
    # Shrinkage & Quality
    shrinkage_rate = Column(Float, default=0.18)   # 15-20% air hilang
    target_moisture_pct = Column(Float, default=14.0)  # Target kadar air akhir
    # Resilience
    buffer_stock_pct = Column(Float, default=0.20)  # 20% minimum buffer
    supply_variability = Column(Float, default=0.08)  # Variabilitas historis
    energy_source = Column(String(100), default="biomassa_sisa")  # Zero fossil
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Factory(Base):
    """
    Langkah 4 — Hilir: Pabrik Bioetanol.
    1 pabrik sentral di kawasan industri.
    """
    __tablename__ = "factory"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    kabupaten = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    # Capacity
    max_capacity_ton_day = Column(Float, nullable=False)
    ethanol_yield_liter_per_ton = Column(Float, default=280.0)
    # ABC Cost Components (IDR)
    processing_cost_per_ton = Column(Float, default=850000.0)  # Listrik, overhead
    depreciation_cost_per_day = Column(Float, default=12500000.0)  # Depresiasi mesin
    investment_cost = Column(Float, nullable=True)  # CAPEX total
    # Weighbridge
    has_weighbridge = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    """
    System users with RBAC.
    Roles: admin(1) | analyst(1) | farmer(10) | hub(5) | driver(5)
    Supports 20+ users.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    hashed_password = Column(String(300), nullable=False)
    role = Column(String(50), nullable=False)  # admin|analyst|farmer|hub|driver
    full_name = Column(String(200), nullable=True)
    kabupaten = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    # Link to entity
    farmer_id = Column(Integer, nullable=True)  # FK to farmers.id if role=farmer
    hub_id = Column(Integer, nullable=True)      # FK to hubs.id if role=hub
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
