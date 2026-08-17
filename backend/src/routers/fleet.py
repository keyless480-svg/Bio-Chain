"""
routers/fleet.py — Armada (Pengepul raw input) & hasil rute Lapis 2 (CVRP).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from src.database import get_db
from src.models.fleet import Vehicle, RouteAssignment, VehicleStop
from src.models.spatial import Hub, User
from src.schemas.fleet import VehicleCreate, VehicleResponse, RouteAssignmentResponse
from src.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/fleet", tags=["fleet"])


@router.post("/vehicles", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def register_vehicle(
    vehicle: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pengepul: daftarkan armada yang tersedia hari ini (raw input untuk Lapis 2 CVRP)."""
    if current_user.role not in ("hub", "admin", "analyst"):
        raise HTTPException(status_code=403, detail="Hanya Pengepul/Admin/Analis yang dapat mendaftarkan armada.")

    if vehicle.owner_hub_id is not None:
        hub = db.query(Hub).filter(Hub.id == vehicle.owner_hub_id).first()
        if not hub:
            raise HTTPException(status_code=404, detail="Hub not found")

    new_vehicle = Vehicle(
        owner_hub_id=vehicle.owner_hub_id,
        vehicle_type=vehicle.vehicle_type,
        plate_number=vehicle.plate_number,
        capacity_ton=vehicle.capacity_ton,
        fuel_rate_l_per_km=vehicle.fuel_rate_l_per_km,
        fixed_charter_cost=vehicle.fixed_charter_cost,
        min_road_class=vehicle.min_road_class,
        is_available_today=vehicle.is_available_today,
        created_by=current_user.id,
    )
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return new_vehicle


@router.get("/vehicles", response_model=List[VehicleResponse])
def list_vehicles(
    hub_id: Optional[int] = None,
    available_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Vehicle).filter(Vehicle.is_active == True)
    if hub_id is not None:
        q = q.filter(Vehicle.owner_hub_id == hub_id)
    if available_only:
        q = q.filter(Vehicle.is_available_today == True)
    return q.order_by(Vehicle.created_at.desc()).all()


@router.get("/routes", response_model=List[RouteAssignmentResponse])
def list_routes(
    hub_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rute hasil Lapis 2 CVRP — dipanggil dashboard Pengepul/Sopir/Analis untuk visibilitas real-time."""
    q = db.query(RouteAssignment)
    if hub_id is not None:
        q = q.filter(RouteAssignment.hub_id == hub_id)
    routes = q.order_by(RouteAssignment.created_at.desc()).limit(limit).all()

    results = []
    for r in routes:
        stops = (
            db.query(VehicleStop)
            .filter(VehicleStop.route_assignment_id == r.id)
            .order_by(VehicleStop.sequence_no.asc())
            .all()
        )
        resp = RouteAssignmentResponse.model_validate(r)
        resp.stops = stops
        results.append(resp)
    return results


@router.get("/routes/{route_id}", response_model=RouteAssignmentResponse)
def get_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    route = db.query(RouteAssignment).filter(RouteAssignment.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    stops = (
        db.query(VehicleStop)
        .filter(VehicleStop.route_assignment_id == route.id)
        .order_by(VehicleStop.sequence_no.asc())
        .all()
    )
    resp = RouteAssignmentResponse.model_validate(route)
    resp.stops = stops
    return resp
