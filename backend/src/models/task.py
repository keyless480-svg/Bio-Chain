"""
models/task.py — ORM model for async optimization task tracking.
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
    task_id = Column(String(50), unique=True, index=True, nullable=False)  # UUID
    status = Column(String(20), default="pending")          # pending|running|completed|failed|timeout
    
    # Input parameters (stored for reproducibility)
    carbon_tax_usd_per_kg = Column(Float, nullable=True)
    max_budget_usd = Column(Float, nullable=True)
    biorefinery_capacity_ton_day = Column(Float, nullable=True)
    emission_limit_ton_co2 = Column(Float, nullable=True)
    
    # Results (stored as JSON)
    result_json = Column(JSON, nullable=True)               # Full optimization result
    
    # Metrics summary
    total_annual_cost_usd = Column(Float, nullable=True)
    total_emission_ton_co2 = Column(Float, nullable=True)
    mesp_usd_per_liter = Column(Float, nullable=True)       # Minimum Ethanol Selling Price
    solver_status = Column(String(50), nullable=True)       # Pyomo solver status string
    solve_time_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
