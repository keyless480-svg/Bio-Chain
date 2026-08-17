"""
models/fleet.py — Armada & penugasan rute untuk Lapis 2 (CVRP + Time Windows).
Vehicle = input raw dari Pengepul (fleet availability).
RouteAssignment/VehicleStop = output dari routing_engine.solve_daily_routes().
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from src.database import Base


class Vehicle(Base):
    """Armada milik pengepul atau pool independen — heterogen per tipe."""
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    owner_hub_id = Column(Integer, ForeignKey("hubs.id"), nullable=True)
    vehicle_type = Column(String(30), nullable=False)          # pickup|engkel|fuso|wingbox
    plate_number = Column(String(20), nullable=False)
    capacity_ton = Column(Float, nullable=False)
    fuel_rate_l_per_km = Column(Float, nullable=False)         # φᵥ
    fixed_charter_cost = Column(Float, nullable=False)         # C_v^fix (IDR/trip)
    min_road_class = Column(String(10), default="desa")        # desa|kabupaten|nasional — kompatibilitas akses
    is_available_today = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=True)


class RouteAssignment(Base):
    """Satu rute CVRP terselesaikan untuk satu kendaraan pada satu tanggal."""
    __tablename__ = "route_assignments"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    hub_id = Column(Integer, ForeignKey("hubs.id"), nullable=False)
    route_date = Column(DateTime(timezone=True), nullable=False)
    total_distance_km = Column(Float, default=0.0)
    total_fuel_cost = Column(Float, default=0.0)
    total_time_window_penalty = Column(Float, default=0.0)
    total_degradation_cost = Column(Float, default=0.0)
    total_carbon_tax = Column(Float, default=0.0)
    total_route_cost = Column(Float, default=0.0)
    status = Column(String(20), default="planned")             # planned|dispatched|completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VehicleStop(Base):
    """Satu titik jemput dalam urutan rute — sumber ETA/ATA untuk penalti time-window."""
    __tablename__ = "vehicle_stops"

    id = Column(Integer, primary_key=True, index=True)
    route_assignment_id = Column(Integer, ForeignKey("route_assignments.id"), nullable=False)
    sequence_no = Column(Integer, nullable=False)
    harvest_id = Column(Integer, ForeignKey("harvests.id"), nullable=True)
    farmer_id = Column(Integer, nullable=True)
    eta_minutes = Column(Integer, nullable=True)                # menit sejak start-of-day (rencana)
    ata_minutes = Column(Integer, nullable=True)                # menit sejak start-of-day (aktual, diisi sopir)
    status = Column(String(20), default="pending")              # pending|picked_up|skipped
