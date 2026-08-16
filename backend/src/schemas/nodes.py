"""
schemas/nodes.py — Pydantic schemas for spatial node GeoJSON responses.
Updated for 5-Step Flow fields.
"""
from pydantic import BaseModel
from typing import Optional, List, Any


class NodeFeature(BaseModel):
    """GeoJSON Feature for a single supply chain node."""
    type: str = "Feature"
    geometry: dict
    properties: dict


class NodeCollection(BaseModel):
    """GeoJSON FeatureCollection for all supply chain nodes."""
    type: str = "FeatureCollection"
    features: List[NodeFeature]


class FarmResponse(BaseModel):
    id: int
    name: str
    kabupaten: str
    latitude: float
    longitude: float
    annual_supply_ton: float
    daily_supply_ton: float
    corn_area_ha: Optional[float]
    initial_moisture_pct: float
    harvest_cost_per_ton: float
    packing_cost_per_ton: float
    supply_variability: float

    model_config = {"from_attributes": True}


class HubResponse(BaseModel):
    id: int
    name: str
    kabupaten: str
    latitude: float
    longitude: float
    max_capacity_ton_day: float
    current_load_ton: float
    is_active: bool
    warehouse_area_m2: float
    loading_cost_per_ton: float
    drying_energy_cost_per_ton: float
    storage_cost_per_m2_day: float
    operating_cost_per_day: float
    shrinkage_rate: float
    buffer_stock_pct: float
    supply_variability: float

    model_config = {"from_attributes": True}


class BiorefineryResponse(BaseModel):
    id: int
    name: str
    kabupaten: str
    latitude: float
    longitude: float
    max_capacity_ton_day: float
    ethanol_yield_liter_per_ton: float
    investment_cost: Optional[float]
    processing_cost_per_ton: float
    depreciation_cost_per_day: float

    model_config = {"from_attributes": True}


class AllNodesResponse(BaseModel):
    """Combined response with all node types + GeoJSON collection."""
    farms: List[FarmResponse]
    hubs: List[HubResponse]
    biorefineries: List[BiorefineryResponse]
    geojson: NodeCollection
