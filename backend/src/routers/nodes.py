"""
routers/nodes.py — Spatial node data endpoints.
GET /api/v1/nodes — Returns all farms, hubs, biorefineries as GeoJSON.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.spatial import Farm, Hub, Biorefinery
from src.schemas.nodes import (
    AllNodesResponse, FarmResponse, HubResponse,
    BiorefineryResponse, NodeCollection, NodeFeature,
)
from src.routers.auth import get_current_user
from src.models.spatial import User

router = APIRouter(prefix="/api/v1/nodes", tags=["nodes"])


@router.get("", response_model=AllNodesResponse)
def get_all_nodes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all supply chain nodes with coordinates (requires authentication)."""
    farms_db = db.query(Farm).all()
    hubs_db = db.query(Hub).filter(Hub.is_active == True).all()
    bios_db = db.query(Biorefinery).all()

    features = []
    farms_out = []
    for f in farms_db:
        farms_out.append(FarmResponse(
            id=f.id, name=f.name, kabupaten=f.kabupaten,
            latitude=f.latitude, longitude=f.longitude,
            annual_supply_ton=f.annual_supply_ton,
            daily_supply_ton=f.daily_supply_ton,
            corn_area_ha=f.corn_area_ha,
        ))
        features.append(NodeFeature(
            geometry={"type": "Point", "coordinates": [f.longitude, f.latitude]},
            properties={"id": f.id, "type": "farm", "name": f.name,
                        "kabupaten": f.kabupaten, "supply_ton_day": f.daily_supply_ton},
        ))

    hubs_out = []
    for h in hubs_db:
        hubs_out.append(HubResponse(
            id=h.id, name=h.name, kabupaten=h.kabupaten,
            latitude=h.latitude, longitude=h.longitude,
            max_capacity_ton_day=h.max_capacity_ton_day,
            current_load_ton=h.current_load_ton,
            is_active=h.is_active,
            operating_cost_usd_day=h.operating_cost_usd_day,
        ))
        features.append(NodeFeature(
            geometry={"type": "Point", "coordinates": [h.longitude, h.latitude]},
            properties={"id": h.id, "type": "hub", "name": h.name,
                        "kabupaten": h.kabupaten, "capacity": h.max_capacity_ton_day},
        ))

    bios_out = []
    for b in bios_db:
        bios_out.append(BiorefineryResponse(
            id=b.id, name=b.name, kabupaten=b.kabupaten,
            latitude=b.latitude, longitude=b.longitude,
            max_capacity_ton_day=b.max_capacity_ton_day,
            ethanol_yield_liter_per_ton=b.ethanol_yield_liter_per_ton,
            investment_cost_usd=b.investment_cost_usd,
        ))
        features.append(NodeFeature(
            geometry={"type": "Point", "coordinates": [b.longitude, b.latitude]},
            properties={"id": b.id, "type": "biorefinery", "name": b.name,
                        "kabupaten": b.kabupaten, "capacity": b.max_capacity_ton_day},
        ))

    return AllNodesResponse(
        farms=farms_out,
        hubs=hubs_out,
        biorefineries=bios_out,
        geojson=NodeCollection(features=features),
    )
