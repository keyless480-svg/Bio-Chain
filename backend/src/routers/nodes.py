"""
routers/nodes.py — Spatial node data endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.spatial import Farmer, Hub, Factory
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
    """Return all supply chain nodes with coordinates."""
    farms_db = db.query(Farmer).all()
    hubs_db = db.query(Hub).filter(Hub.is_active == True).all()
    bios_db = db.query(Factory).all()

    features = []
    
    farms_out = []
    for f in farms_db:
        farms_out.append(FarmResponse.model_validate(f))
        features.append(NodeFeature(
            geometry={"type": "Point", "coordinates": [f.longitude, f.latitude]},
            properties={"id": f.id, "type": "farm", "name": f.name,
                        "kabupaten": f.kabupaten, "supply_ton_day": f.daily_supply_ton},
        ))

    hubs_out = []
    for h in hubs_db:
        hubs_out.append(HubResponse.model_validate(h))
        features.append(NodeFeature(
            geometry={"type": "Point", "coordinates": [h.longitude, h.latitude]},
            properties={"id": h.id, "type": "hub", "name": h.name,
                        "kabupaten": h.kabupaten, "capacity": h.max_capacity_ton_day},
        ))

    bios_out = []
    for b in bios_db:
        bios_out.append(BiorefineryResponse.model_validate(b))
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
