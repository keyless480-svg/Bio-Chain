"""
models/spatial.py — ORM models for spatial supply chain nodes.
Uses standard floats for SQLite compatibility (no PostGIS required).
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from src.database import Base


class Farm(Base):
    """
    Represents a corn-producing farm/village (supply node).
    Coordinates sourced from BPS Jawa Timur kabupaten centroids.
    """
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)            # Desa/Kelurahan name
    kabupaten = Column(String(100), nullable=False)       # Administrative district
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    annual_supply_ton = Column(Float, nullable=False)     # Annual corncob supply (tons)
    daily_supply_ton = Column(Float, nullable=False)      # Daily corncob supply (tons)
    corn_area_ha = Column(Float, nullable=True)           # Harvest area (hectares)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Hub(Base):
    """
    Pre-processing Hub (Gudang KUD).
    Receives corncobs from farms, pre-processes, then ships to biorefinery.
    """
    __tablename__ = "hubs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)            # Hub/KUD name
    kabupaten = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    max_capacity_ton_day = Column(Float, nullable=False)  # Max processing capacity (ton/day)
    current_load_ton = Column(Float, default=0.0)         # Current warehouse load
    is_active = Column(Boolean, default=True)
    operating_cost_usd_day = Column(Float, nullable=False)  # Daily operating cost
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Biorefinery(Base):
    """
    Central Biorefinery (Pabrik Bioetanol).
    Converts processed corncob biomass into 2G bioethanol.
    """
    __tablename__ = "biorefineries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    kabupaten = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    max_capacity_ton_day = Column(Float, nullable=False)  # Processing capacity
    ethanol_yield_liter_per_ton = Column(Float, default=280.0)  # 2G yield factor
    investment_cost_usd = Column(Float, nullable=True)    # CAPEX
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    """
    System users with role-based access.
    Roles: analyst | farmer | collector | driver
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    hashed_password = Column(String(300), nullable=False)
    role = Column(String(50), nullable=False)             # analyst|farmer|collector|driver
    full_name = Column(String(200), nullable=True)
    kabupaten = Column(String(100), nullable=True)        # For farmers/collectors
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
