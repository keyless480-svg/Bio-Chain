"""
schemas/optimization.py — Pydantic schemas for the optimization API.
Updated for Multi-Objective 5-Step Flow.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class RouteFlowSchema(BaseModel):
    from_id: int
    to_id: int
    from_type: str
    to_type: str
    flow_ton_day: float
    distance_km: float
    transport_cost_day: float
    emission_kg_co2_day: float

class OptimizeRequest(BaseModel):
    """Parameters for the optimization run."""
    carbon_tax_usd_per_kg: Optional[float] = Field(0.03, description="Kept for backward compatibility, mapped to IDR")
    lambda_green: float = Field(465.0, description="Green penalty weight (IDR/kg CO2)")
    gamma_resilience: float = Field(500000.0, description="Resilience penalty weight")
    max_budget_usd: Optional[float] = None
    max_budget_idr: Optional[float] = None
    biorefinery_capacity_ton_day: Optional[float] = 500.0
    emission_limit_ton_co2: Optional[float] = None
    shrinkage_rate_override: Optional[float] = None
    buffer_stock_min_pct: Optional[float] = 0.20

class TaskResultResponse(BaseModel):
    """Response containing optimization results and task status."""
    task_id: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    solver_status: Optional[str] = None
    solve_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    
    result: Optional[Dict[str, Any]] = None

    # Key metrics summary for quick display
    total_annual_cost: Optional[float] = None
    total_emission_ton_co2: Optional[float] = None
    hpp_per_kg: Optional[float] = None
    hpp_per_liter_ethanol: Optional[float] = None
    fair_trade_margin_pct: Optional[float] = None
    buffer_stock_avg_pct: Optional[float] = None
