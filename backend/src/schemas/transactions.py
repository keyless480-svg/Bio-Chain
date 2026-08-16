"""
schemas/transactions.py — Pydantic schemas for transactional operations.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


# ── Harvest (Petani) ──
class HarvestCreate(BaseModel):
    farmer_id: int
    gross_weight_kg: float
    initial_moisture_pct: float
    harvest_date: date
    destination_hub_id: Optional[int] = None
    notes: Optional[str] = None

class HarvestResponse(HarvestCreate):
    id: int
    harvest_cost: float
    packing_cost: float
    total_cost: float
    price_per_kg: float
    total_payment: float
    status: str
    geo_lat: Optional[float]
    geo_long: Optional[float]
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Hub Batch (Pengepul) ──
class HubBatchCreate(BaseModel):
    hub_id: int
    total_input_kg: float
    input_moisture_pct: float
    num_farmers: int
    batch_date: date
    quality_grade: str = "A"
    notes: Optional[str] = None

class HubBatchResponse(HubBatchCreate):
    id: int
    batch_code: str
    final_weight_kg: Optional[float]
    final_moisture_pct: Optional[float]
    shrinkage_kg: Optional[float]
    shrinkage_pct: Optional[float]
    loading_cost: float
    drying_cost: float
    storage_cost: float
    shrinkage_cost: float
    total_handling_cost: float
    status: str
    ready_date: Optional[date]
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Shipment (Driver) ──
class ShipmentCreate(BaseModel):
    hub_batch_id: int
    hub_id: int
    factory_id: int = 1
    truck_plate: str
    payload_ton: float
    distance_km: float
    shipment_date: date
    notes: Optional[str] = None

class ShipmentResponse(ShipmentCreate):
    id: int
    driver_name: Optional[str]
    truck_capacity_ton: float
    truck_utilization_pct: float
    estimated_duration_hours: Optional[float]
    fuel_cost: float
    toll_cost: float
    driver_cost: float
    total_transport_cost: float
    carbon_emitted_kg: float
    carbon_tax_cost: float
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Factory HPP (Pabrik) ──
class FactoryHppCreate(BaseModel):
    shipment_id: int
    factory_id: int = 1
    net_weight_received_kg: float
    received_date: date
    quality_sample_result: Optional[str] = "pass"
    notes: Optional[str] = None

class FactoryHppResponse(FactoryHppCreate):
    id: int
    weight_difference_kg: Optional[float]
    acquisition_cost: float
    transport_cost: float
    processing_cost: float
    depreciation_cost: float
    total_cost: float
    total_hpp_per_kg: float
    ethanol_produced_liter: Optional[float]
    hpp_per_liter_ethanol: Optional[float]
    farmer_share_pct: Optional[float]
    hub_share_pct: Optional[float]
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Circularity (Waste to Value) ──
class CircularityCreate(BaseModel):
    source_type: str = "factory"
    source_id: int = 1
    destination_farmer_id: int
    product_type: str
    quantity_kg: float
    delivery_date: date

class CircularityResponse(CircularityCreate):
    id: int
    production_cost: float
    market_value: float
    farmer_saving: float
    truck_plate: Optional[str]
    is_backhaul: bool
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}
