"""
routers/results.py — Optimization result polling endpoints.
GET /api/v1/results/{task_id} — Poll task status and retrieve results.
GET /api/v1/results           — List all tasks (analyst only).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.database import get_db
from src.models.task import OptimizationTask
from src.schemas.optimization import TaskResultResponse
from src.routers.auth import get_current_user
from src.models.spatial import User

router = APIRouter(prefix="/api/v1/results", tags=["results"])

@router.get("/{task_id}", response_model=TaskResultResponse)
def get_task_result(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Poll optimization task status. Returns result when completed."""
    task = db.query(OptimizationTask).filter(OptimizationTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    return TaskResultResponse(
        task_id=task.task_id,
        status=task.status,
        created_at=task.created_at,
        updated_at=task.updated_at,
        result=task.result_json if task.status == "completed" else None,
        total_annual_cost=task.total_annual_cost,
        total_emission_ton_co2=task.total_emission_ton_co2,
        hpp_per_kg=task.hpp_per_kg,
        hpp_per_liter_ethanol=task.hpp_per_liter_ethanol,
        fair_trade_margin_pct=task.fair_trade_margin_pct,
        buffer_stock_avg_pct=task.buffer_stock_avg_pct,
        solve_time_seconds=task.solve_time_seconds,
        solver_status=task.solver_status,
        error_message=task.error_message,
    )

@router.get("", response_model=List[TaskResultResponse])
def list_tasks(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List recent optimization tasks (analyst only)."""
    if current_user.role != "analyst":
        raise HTTPException(status_code=403, detail="Access denied.")

    tasks = (
        db.query(OptimizationTask)
        .order_by(OptimizationTask.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        TaskResultResponse(
            task_id=t.task_id,
            status=t.status,
            created_at=t.created_at,
            updated_at=t.updated_at,
            total_annual_cost=t.total_annual_cost,
            total_emission_ton_co2=t.total_emission_ton_co2,
            hpp_per_kg=t.hpp_per_kg,
            hpp_per_liter_ethanol=t.hpp_per_liter_ethanol,
            fair_trade_margin_pct=t.fair_trade_margin_pct,
            buffer_stock_avg_pct=t.buffer_stock_avg_pct,
            solve_time_seconds=t.solve_time_seconds,
            solver_status=t.solver_status,
            error_message=t.error_message,
        )
        for t in tasks
    ]
