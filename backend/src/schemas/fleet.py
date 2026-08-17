"""
schemas/fleet.py — Pydantic schemas for fleet (Vehicle) input and route results.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Vehicle (Pengepul raw input: fleet availability) ──
class VehicleCreate(BaseModel):
    owner_hub_id: Optional[int] = None
    vehicle_type: str                    # pickup|engkel|fuso|wingbox
    plate_number: str
    capacity_ton: float
    fuel_rate_l_per_km: float
    fixed_charter_cost: float
    min_road_class: str = "desa"
    is_available_today: bool = True


class VehicleResponse(VehicleCreate):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Route results (Lapis 2 CVRP output) ──
class VehicleStopResponse(BaseModel):
    id: int
    sequence_no: int
    harvest_id: Optional[int]
    farmer_id: Optional[int]
    eta_minutes: Optional[int]
    ata_minutes: Optional[int]
    status: str
    model_config = {"from_attributes": True}


class RouteAssignmentResponse(BaseModel):
    id: int
    vehicle_id: int
    hub_id: int
    route_date: datetime
    total_distance_km: float
    total_fuel_cost: float
    total_time_window_penalty: float
    total_degradation_cost: float
    total_carbon_tax: float
    total_route_cost: float
    status: str
    stops: List[VehicleStopResponse] = []
    model_config = {"from_attributes": True}
