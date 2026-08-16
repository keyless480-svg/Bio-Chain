"""
schemas/nodes.py — Pydantic schemas for spatial node GeoJSON responses.
"""
from pydantic import BaseModel
from typing import Optional, List, Any


class NodeFeature(BaseModel):
    """GeoJSON Feature for a single supply chain node."""
    type: str = "Feature"
    geometry: dict                  # {"type": "Point", "coordinates": [lon, lat]}
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
    operating_cost_usd_day: float

    model_config = {"from_attributes": True}


class BiorefineryResponse(BaseModel):
    id: int
    name: str
    kabupaten: str
    latitude: float
    longitude: float
    max_capacity_ton_day: float
    ethanol_yield_liter_per_ton: float
    investment_cost_usd: Optional[float]

    model_config = {"from_attributes": True}


class AllNodesResponse(BaseModel):
    """Combined response with all node types + GeoJSON collection."""
    farms: List[FarmResponse]
    hubs: List[HubResponse]
    biorefineries: List[BiorefineryResponse]
    geojson: NodeCollection
