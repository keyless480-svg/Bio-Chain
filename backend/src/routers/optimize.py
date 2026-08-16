"""
routers/optimize.py — Optimization trigger endpoint.
POST /api/v1/optimize — Validates input, starts async task, returns task_id.
"""
import uuid
import threading
import logging
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_X, ST_Y

from src.database import get_db
from src.models.spatial import Farm, Hub, Biorefinery
from src.models.task import OptimizationTask
from src.schemas.optimization import OptimizeRequest, OptimizeResponse
from src.services.optimization_engine import (
    OptimizationInput, NodeInfo, run_optimization,
)
from src.routers.auth import get_current_user
from src.models.spatial import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/optimize", tags=["optimization"])


def _run_task_background(task_id: str, inp: OptimizationInput, db_url: str):
    """Background thread: runs MILP solver and writes result to DB."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        task = db.query(OptimizationTask).filter(OptimizationTask.task_id == task_id).first()
        task.status = "running"
        db.commit()

        result = run_optimization(inp)

        task.status = "completed" if result.status in ("optimal", "feasible") else result.status
        task.result_json = result.to_dict()
        task.total_annual_cost_usd = result.total_annual_cost_usd
        task.total_emission_ton_co2 = result.total_emission_ton_co2_year
        task.mesp_usd_per_liter = result.mesp_usd_per_liter
        task.solver_status = result.solver_status
        task.solve_time_seconds = result.solve_time_seconds
        task.error_message = result.error_message
        db.commit()
        logger.info(f"Task {task_id} completed: {result.status}")

    except Exception as exc:
        logger.exception(f"Background task {task_id} crashed")
        task = db.query(OptimizationTask).filter(OptimizationTask.task_id == task_id).first()
        if task:
            task.status = "failed"
            task.error_message = str(exc)
            db.commit()
    finally:
        db.close()


@router.post("", response_model=OptimizeResponse, status_code=202)
def start_optimization(
    req: OptimizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start async MILP optimization. Returns task_id for polling.
    Only 'analyst' role can trigger optimization.
    """
    if current_user.role not in ("analyst",):
        raise HTTPException(status_code=403, detail="Only analysts can run optimization.")

    # Load all nodes from DB
    farms_db = db.query(Farm).all()
    hubs_db = db.query(Hub).filter(Hub.is_active == True).all()
    bios_db = db.query(Biorefinery).all()

    if not farms_db or not hubs_db or not bios_db:
        raise HTTPException(status_code=400, detail="Database not seeded. Run seed_data.py first.")

    from src.config import get_settings
    settings = get_settings()

    # Build NodeInfo objects
    farms = [
        NodeInfo(
            id=f.id,
            lat=db.scalar(ST_Y(f.location)),
            lon=db.scalar(ST_X(f.location)),
            capacity=0,
            supply=f.daily_supply_ton,
        )
        for f in farms_db
    ]
    hubs = [
        NodeInfo(
            id=h.id,
            lat=db.scalar(ST_Y(h.location)),
            lon=db.scalar(ST_X(h.location)),
            capacity=h.max_capacity_ton_day,
            operating_cost=h.operating_cost_usd_day,
        )
        for h in hubs_db
    ]
    bios = [
        NodeInfo(
            id=b.id,
            lat=db.scalar(ST_Y(b.location)),
            lon=db.scalar(ST_X(b.location)),
            capacity=req.biorefinery_capacity_ton_day or b.max_capacity_ton_day,
        )
        for b in bios_db
    ]

    inp = OptimizationInput(
        farms=farms,
        hubs=hubs,
        biorefineries=bios,
        carbon_tax_usd_per_kg=req.carbon_tax_usd_per_kg,
        max_budget_usd=req.max_budget_usd,
        emission_limit_ton_co2=req.emission_limit_ton_co2,
        solver_name=req.solver_name,
        time_limit_seconds=req.time_limit_seconds,
    )

    # Create task record
    task_id = str(uuid.uuid4())
    task = OptimizationTask(
        task_id=task_id,
        status="pending",
        carbon_tax_usd_per_kg=req.carbon_tax_usd_per_kg,
        max_budget_usd=req.max_budget_usd,
        biorefinery_capacity_ton_day=req.biorefinery_capacity_ton_day,
        emission_limit_ton_co2=req.emission_limit_ton_co2,
    )
    db.add(task)
    db.commit()

    # Start background thread (no Celery dependency for simplicity)
    t = threading.Thread(
        target=_run_task_background,
        args=(task_id, inp, settings.database_url),
        daemon=True,
    )
    t.start()

    return OptimizeResponse(
        task_id=task_id,
        status="pending",
        message="Optimasi dimulai. Gunakan task_id untuk polling hasil.",
        estimated_wait_seconds=min(req.time_limit_seconds, 120),
    )
