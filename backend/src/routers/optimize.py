"""
routers/optimize.py — Optimization trigger endpoint.
Updated for 5-Step Circular Flow Multi-Objective MILP.
"""
import uuid
import threading
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.spatial import Farmer, Hub, Factory, User
from src.models.task import OptimizationTask
from src.models.transactions import Harvest
from src.models.fleet import Vehicle, RouteAssignment, VehicleStop
from src.schemas.optimization import OptimizeRequest, TaskResultResponse
from src.services.optimization_engine import (
    OptimizationInput, run_optimization, FarmerNode, HubNode, FactoryNode
)
from src.services.routing_engine import solve_daily_routes, StopDemand, FleetVehicle
from src.routers.auth import get_current_user
from src.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/optimize", tags=["optimization"])


def _run_layer2_for_active_hubs(db, active_hub_ids: list):
    """Lapis 2 — untuk setiap hub aktif hasil Lapis 1, kelompokkan Harvest yang
    sudah tercatat (destination_hub_id == hub, status == 'recorded') sebagai demand
    dan armada tersedia hari itu, lalu jalankan CVRP+TW. Tidak pernah membatalkan
    keputusan Lapis 1 — hanya mewujudkannya jadi rute fisik per armada."""
    settings = get_settings()
    routes_created = 0

    for hub_id in active_hub_ids:
        hub = db.query(Hub).filter(Hub.id == hub_id).first()
        if not hub:
            continue

        harvests = (
            db.query(Harvest)
            .filter(Harvest.destination_hub_id == hub_id, Harvest.status == "recorded")
            .all()
        )
        if not harvests:
            continue

        vehicles = (
            db.query(Vehicle)
            .filter(
                Vehicle.is_active == True,
                Vehicle.is_available_today == True,
                (Vehicle.owner_hub_id == hub_id) | (Vehicle.owner_hub_id.is_(None)),
            )
            .all()
        )
        if not vehicles:
            logger.info(f"Layer 2: hub {hub_id} punya {len(harvests)} panen tapi tidak ada armada tersedia hari ini.")
            continue

        demands = [
            StopDemand(
                node_id=h.id,
                farmer_id=h.farmer_id,
                lat=h.geo_lat, lon=h.geo_long,
                weight_ton=h.gross_weight_kg / 1000.0,
                price_per_ton=h.price_per_kg * 1000.0,
                window_open_min=settings.hub_window_open_min,
                window_close_min=settings.hub_window_close_min,
            )
            for h in harvests if h.geo_lat is not None and h.geo_long is not None
        ]
        fleet = [
            FleetVehicle(
                vehicle_id=v.id,
                capacity_ton=v.capacity_ton,
                fuel_rate_l_per_km=v.fuel_rate_l_per_km,
                fixed_charter_cost=v.fixed_charter_cost,
                fuel_price_per_liter=settings.diesel_price_per_liter,
                carbon_tax_per_kg=settings.lambda_green,
            )
            for v in vehicles
        ]
        if not demands:
            continue

        route_results = solve_daily_routes((hub.latitude, hub.longitude), demands, fleet)

        for rr in route_results:
            assignment = RouteAssignment(
                vehicle_id=rr.vehicle_id, hub_id=hub_id, route_date=datetime.now(timezone.utc),
                total_distance_km=rr.distance_km, total_fuel_cost=rr.fuel_cost,
                total_time_window_penalty=rr.time_window_penalty,
                total_degradation_cost=rr.degradation_cost, total_carbon_tax=rr.carbon_tax,
                total_route_cost=rr.total_route_cost, status="planned",
            )
            db.add(assignment)
            db.flush()  # perlu assignment.id sebelum membuat VehicleStop

            for stop in rr.stops:
                db.add(VehicleStop(
                    route_assignment_id=assignment.id, sequence_no=stop.sequence_no,
                    harvest_id=stop.node_id, farmer_id=stop.farmer_id,
                    eta_minutes=stop.eta_minutes, status="pending",
                ))
                harvest = db.query(Harvest).filter(Harvest.id == stop.node_id).first()
                if harvest:
                    harvest.status = "scheduled"
            routes_created += 1

    db.commit()
    logger.info(f"Layer 2 CVRP: {routes_created} rute armada dibuat.")


def _run_task_background(task_id: str, inp: OptimizationInput, db_url: str):
    """Background thread: runs MILP solver and writes result to DB."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        task = db.query(OptimizationTask).filter(OptimizationTask.task_id == task_id).first()
        if not task:
            return
            
        task.status = "running"
        db.commit()

        result = run_optimization(inp)

        task.status = "completed" if result.status in ("optimal", "feasible") else result.status
        task.result_json = result.to_dict()
        task.total_annual_cost = result.total_annual_cost
        task.total_emission_ton_co2 = result.total_emission_ton_co2_year
        task.hpp_per_kg = result.hpp_per_kg
        task.hpp_per_liter_ethanol = result.hpp_per_liter_ethanol
        task.green_penalty_cost = result.green_penalty_year
        task.resilience_penalty_cost = result.resilience_penalty_year
        task.total_shrinkage_ton = result.total_shrinkage_ton_year
        task.buffer_stock_avg_pct = result.buffer_stock_avg_pct
        task.fair_trade_margin_pct = result.fair_trade_margin_pct
        task.solver_status = result.solver_status
        task.solve_time_seconds = result.solve_time_seconds
        task.error_message = result.error_message
        db.commit()
        logger.info(f"Task {task_id} completed: {result.status}")

        if result.status in ("optimal", "feasible") and result.active_hubs:
            try:
                _run_layer2_for_active_hubs(db, result.active_hubs)
            except Exception:
                logger.exception(f"Layer 2 CVRP failed for task {task_id} — Layer 1 result is unaffected")

    except Exception as exc:
        logger.exception(f"Background task {task_id} crashed")
        task = db.query(OptimizationTask).filter(OptimizationTask.task_id == task_id).first()
        if task:
            task.status = "failed"
            task.error_message = str(exc)
            db.commit()
    finally:
        db.close()


@router.post("", response_model=dict, status_code=202)
def start_optimization(
    req: OptimizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start async multi-objective MILP optimization. 
    Only 'analyst' or 'admin' role can trigger optimization.
    """
    if current_user.role not in ("analyst", "admin"):
        raise HTTPException(status_code=403, detail="Only analysts or admins can run optimization.")

    farms_db = db.query(Farmer).filter(Farmer.is_active == True).all()
    hubs_db = db.query(Hub).filter(Hub.is_active == True).all()
    bios_db = db.query(Factory).all()

    if not farms_db or not hubs_db or not bios_db:
        raise HTTPException(status_code=400, detail="Database not seeded. Run seed_data.py first.")

    from src.config import get_settings
    settings = get_settings()

    # Mapping to Node objects
    farmers = [
        FarmerNode(
            id=f.id, lat=f.latitude, lon=f.longitude,
            supply=f.daily_supply_ton,
            harvest_cost_per_ton=f.harvest_cost_per_ton,
            packing_cost_per_ton=f.packing_cost_per_ton,
            price_per_ton=850000.0,  # 850 Rp/kg
            supply_variability=f.supply_variability
        ) for f in farms_db
    ]
    
    hubs = [
        HubNode(
            id=h.id, lat=h.latitude, lon=h.longitude,
            capacity=h.max_capacity_ton_day,
            loading_cost_per_ton=h.loading_cost_per_ton,
            drying_cost_per_ton=h.drying_energy_cost_per_ton,
            storage_cost_per_day=h.warehouse_area_m2 * h.storage_cost_per_m2_day,
            operating_cost_per_day=h.operating_cost_per_day,
            shrinkage_rate=req.shrinkage_rate_override if req.shrinkage_rate_override is not None else h.shrinkage_rate,
            buffer_stock_pct=req.buffer_stock_min_pct if req.buffer_stock_min_pct is not None else h.buffer_stock_pct,
            supply_variability=h.supply_variability
        ) for h in hubs_db
    ]
    
    factories = [
        FactoryNode(
            id=b.id, lat=b.latitude, lon=b.longitude,
            capacity=req.biorefinery_capacity_ton_day or b.max_capacity_ton_day,
            processing_cost_per_ton=b.processing_cost_per_ton,
            depreciation_per_day=b.depreciation_cost_per_day
        ) for b in bios_db
    ]

    inp = OptimizationInput(
        farmers=farmers,
        hubs=hubs,
        factories=factories,
        lambda_green=req.lambda_green,
        gamma_resilience=req.gamma_resilience,
        carbon_tax_per_kg=req.carbon_tax_usd_per_kg * 15500 if req.carbon_tax_usd_per_kg else req.lambda_green,
        max_budget=req.max_budget_idr,
        emission_limit_ton_co2=req.emission_limit_ton_co2,
        solver_name=settings.milp_solver,
        time_limit_seconds=settings.solver_timeout,
        degradation_rate_pct_per_hour=settings.degradation_rate_pct_per_hour,
        avg_truck_speed_kmph=settings.avg_truck_speed_kmph,
    )

    task_id = str(uuid.uuid4())
    task = OptimizationTask(
        task_id=task_id,
        status="pending",
        lambda_green=req.lambda_green,
        gamma_resilience=req.gamma_resilience,
        max_budget=req.max_budget_idr,
        factory_capacity_ton_day=req.biorefinery_capacity_ton_day,
        emission_limit_ton_co2=req.emission_limit_ton_co2,
        shrinkage_rate_override=req.shrinkage_rate_override,
    )
    db.add(task)
    db.commit()

    t = threading.Thread(
        target=_run_task_background,
        args=(task_id, inp, settings.database_url),
        daemon=True,
    )
    t.start()

    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Multi-Objective MILP Optimization started."
    }


@router.get("/status/{task_id}", response_model=TaskResultResponse)
def get_optimization_status(task_id: str, db: Session = Depends(get_db)):
    task = db.query(OptimizationTask).filter(OptimizationTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.status in ("pending", "running"):
        return TaskResultResponse(
        task_id=task.task_id,
        status=task.status,
        created_at=task.created_at,
    )
        
    if task.status == "failed" or not task.result_json:
        raise HTTPException(status_code=500, detail=task.error_message or "Unknown error")
        
    result = task.result_json
    return TaskResultResponse(
        task_id=task_id,
        status=task.status,
        created_at=task.created_at,
        updated_at=task.updated_at,
        solver_status=task.solver_status or "optimal",
        solve_time_seconds=task.solve_time_seconds or 0.0,
        result=result,
        total_annual_cost=result.get("total_annual_cost", 0.0),
        total_emission_ton_co2=result.get("total_emission_ton_co2_year", 0.0),
        hpp_per_kg=result.get("hpp_per_kg", 0.0),
        hpp_per_liter_ethanol=result.get("hpp_per_liter_ethanol", 0.0),
        fair_trade_margin_pct=result.get("fair_trade_margin_pct", 0.0),
        buffer_stock_avg_pct=result.get("buffer_stock_avg_pct", 0.0),
        error_message=task.error_message,
    )
