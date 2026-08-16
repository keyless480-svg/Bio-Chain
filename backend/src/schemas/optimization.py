"""
schemas/optimization.py — Pydantic schemas for optimization API.
Enforces validation: no negative economic params, coordinates within Jawa Timur.
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Any
from datetime import datetime


# ─── Jawa Timur Bounding Box (WGS84) ────────────────────────────────────────
JATIM_LON_MIN = 110.0
JATIM_LON_MAX = 115.5
JATIM_LAT_MIN = -8.8
JATIM_LAT_MAX = -6.8


class OptimizeRequest(BaseModel):
    """
    Parameters for a new optimization run.
    All economic values must be non-negative.
    """
    carbon_tax_usd_per_kg: float = Field(
        default=0.03,
        ge=0.0,
        description="Carbon tax rate in USD per kg CO2e. Default: NEK standard 0.03.",
    )
    max_budget_usd: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Maximum annual budget constraint (USD). Null = unconstrained.",
    )
    biorefinery_capacity_ton_day: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Override biorefinery capacity (ton/day). Null = use database value.",
    )
    emission_limit_ton_co2: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Annual emission cap (ton CO2). Null = unconstrained.",
    )
    solver_name: str = Field(
        default="cbc",
        pattern="^(cbc|glpk|cplex|gurobi)$",
        description="MILP solver to use.",
    )
    time_limit_seconds: int = Field(
        default=300,
        ge=30,
        le=600,
        description="Solver time limit in seconds (30–600).",
    )


class OptimizeResponse(BaseModel):
    """Response from POST /api/v1/optimize — returns task_id for polling."""
    task_id: str
    status: str
    message: str
    estimated_wait_seconds: int = 60


class TaskResultResponse(BaseModel):
    """Response from GET /api/v1/results/{task_id}."""
    task_id: str
    status: str          # pending | running | completed | failed | timeout
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    # Available when status == 'completed'
    result: Optional[Any] = None
    total_annual_cost_usd: Optional[float] = None
    total_emission_ton_co2: Optional[float] = None
    mesp_usd_per_liter: Optional[float] = None
    solve_time_seconds: Optional[float] = None
    solver_status: Optional[str] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class ScenarioSummary(BaseModel):
    """Summary card for the scenario builder UI."""
    carbon_tax_usd_per_kg: float
    total_annual_cost_usd: float
    total_emission_ton_co2_year: float
    mesp_usd_per_liter: float
    total_ethanol_liter_year: float
    open_hubs_count: int
    status: str
