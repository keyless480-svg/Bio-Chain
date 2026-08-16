"""
models/task.py — ORM model for async optimization task tracking.
Updated for 5-Step Circular Flow multi-objective optimization.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.sql import func
from src.database import Base


class OptimizationTask(Base):
    """
    Tracks the lifecycle of an async MILP optimization job.
    Status transitions: pending → running → completed | failed | timeout
    """
    __tablename__ = "optimization_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), unique=True, index=True, nullable=False)
    status = Column(String(20), default="pending")

    # Input parameters (stored for reproducibility)
    carbon_tax_per_kg_co2 = Column(Float, nullable=True)  # IDR/kg CO2
    lambda_green = Column(Float, nullable=True)            # Green penalty weight
    gamma_resilience = Column(Float, nullable=True)        # Resilience penalty weight
    max_budget = Column(Float, nullable=True)              # IDR
    factory_capacity_ton_day = Column(Float, nullable=True)
    emission_limit_ton_co2 = Column(Float, nullable=True)
    shrinkage_rate_override = Column(Float, nullable=True)

    # Results (stored as JSON)
    result_json = Column(JSON, nullable=True)

    # Key metrics summary
    total_annual_cost = Column(Float, nullable=True)           # IDR/year
    total_emission_ton_co2 = Column(Float, nullable=True)
    hpp_per_kg = Column(Float, nullable=True)                  # IDR/kg
    hpp_per_liter_ethanol = Column(Float, nullable=True)       # IDR/liter
    green_penalty_cost = Column(Float, nullable=True)          # IDR/year
    resilience_penalty_cost = Column(Float, nullable=True)     # IDR/year
    total_shrinkage_ton = Column(Float, nullable=True)
    buffer_stock_avg_pct = Column(Float, nullable=True)
    fair_trade_margin_pct = Column(Float, nullable=True)
    solver_status = Column(String(50), nullable=True)
    solve_time_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
