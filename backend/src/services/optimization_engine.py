"""
services/optimization_engine.py — Core MILP model using Pyomo.

Model: Hub-and-Spoke Supply Chain Optimization
Objective: Minimize Total Annual Cost (TAC)
  TAC = Transportation Cost (Farm→Hub) + Transportation Cost (Hub→Biorefinery)
        + Hub Operating Cost + Carbon Tax

Decision Variables:
  x[i, j]  — flow of corncob (ton/day) from farm i to hub j  (continuous ≥ 0)
  w[j, k]  — flow of corncob (ton/day) from hub j to biorefinery k (continuous ≥ 0)
  y[j]     — binary: hub j is open (1) or closed (0)

Constraints:
  1. Supply: Total outflow from farm i ≤ farm i daily supply
  2. Hub capacity: Total inflow to hub j ≤ hub j max capacity × y[j]
  3. Hub balance: Total outflow from hub j ≤ total inflow to hub j (mass balance)
  4. Biorefinery capacity: Total inflow to biorefinery k ≤ biorefinery capacity
  5. Emission limit: Total CO2 emission ≤ emission_limit (optional constraint)
  6. Demand: Total inflow to all biorefineries ≥ minimum_demand (optional)
"""
import time
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Tuple

import pyomo.environ as pyo
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition

from src.services.spatial_service import (
    build_cost_matrix,
    emission_kg_co2_per_ton,
    road_distance_km,
)

logger = logging.getLogger(__name__)

DAYS_PER_YEAR = 365
ETHANOL_YIELD_LITER_PER_TON = 280.0   # 2G bioethanol conversion factor


@dataclass
class NodeInfo:
    id: int
    lat: float
    lon: float
    capacity: float
    operating_cost: float = 0.0
    supply: float = 0.0


@dataclass
class OptimizationInput:
    farms: List[NodeInfo]
    hubs: List[NodeInfo]
    biorefineries: List[NodeInfo]
    carbon_tax_usd_per_kg: float = 0.03
    max_budget_usd: Optional[float] = None
    emission_limit_ton_co2: Optional[float] = None
    solver_name: str = "cbc"
    time_limit_seconds: int = 300


@dataclass
class RouteFlow:
    from_id: int
    to_id: int
    from_type: str      # 'farm' | 'hub'
    to_type: str        # 'hub' | 'biorefinery'
    flow_ton_day: float
    distance_km: float
    cost_usd_day: float
    emission_kg_co2_day: float


@dataclass
class OptimizationResult:
    status: str                  # 'optimal' | 'feasible' | 'infeasible' | 'timeout' | 'error'
    solver_status: str
    solve_time_seconds: float
    total_annual_cost_usd: float = 0.0
    transport_cost_usd_year: float = 0.0
    hub_operating_cost_usd_year: float = 0.0
    carbon_tax_cost_usd_year: float = 0.0
    total_emission_ton_co2_year: float = 0.0
    total_corncob_ton_day: float = 0.0
    total_ethanol_liter_year: float = 0.0
    mesp_usd_per_liter: float = 0.0       # Minimum Ethanol Selling Price
    open_hubs: List[int] = field(default_factory=list)
    routes: List[RouteFlow] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["routes"] = [asdict(r) for r in self.routes]
        return d


def run_optimization(inp: OptimizationInput) -> OptimizationResult:
    """
    Execute the MILP optimization model and return results.
    This function is designed to be called from a background thread.
    """
    t_start = time.time()

    try:
        # ─── Build spatial cost/emission matrices ───────────────────────────
        farm_nodes = [{"id": f.id, "lat": f.lat, "lon": f.lon} for f in inp.farms]
        hub_nodes  = [{"id": h.id, "lat": h.lat, "lon": h.lon} for h in inp.hubs]
        bio_nodes  = [{"id": b.id, "lat": b.lat, "lon": b.lon} for b in inp.biorefineries]

        cost_fh, emit_fh = build_cost_matrix(farm_nodes, hub_nodes)    # farm→hub
        cost_hb, emit_hb = build_cost_matrix(hub_nodes, bio_nodes)     # hub→biorefinery
        dist_fh = {(f["id"], h["id"]): road_distance_km(f["lat"], f["lon"], h["lat"], h["lon"])
                   for f in farm_nodes for h in hub_nodes}
        dist_hb = {(h["id"], b["id"]): road_distance_km(h["lat"], h["lon"], b["lat"], b["lon"])
                   for h in hub_nodes for b in bio_nodes}

        farm_map = {f.id: f for f in inp.farms}
        hub_map  = {h.id: h for h in inp.hubs}
        bio_map  = {b.id: b for b in inp.biorefineries}

        F = [f.id for f in inp.farms]
        H = [h.id for h in inp.hubs]
        B = [b.id for b in inp.biorefineries]

        # ─── Build Pyomo Model ──────────────────────────────────────────────
        model = pyo.ConcreteModel(name="BioChain-Opt")

        # Sets
        model.F = pyo.Set(initialize=F)
        model.H = pyo.Set(initialize=H)
        model.B = pyo.Set(initialize=B)

        # Variables
        model.x = pyo.Var(model.F, model.H, domain=pyo.NonNegativeReals)   # farm→hub flow
        model.w = pyo.Var(model.H, model.B, domain=pyo.NonNegativeReals)   # hub→bioref flow
        model.y = pyo.Var(model.H, domain=pyo.Binary)                      # hub open/close

        # ─── Objective: Minimize TAC ─────────────────────────────────────
        def objective_rule(m):
            # Transport cost: farm→hub (USD/ton·day × ton/day × 365 days)
            transport_fh = sum(
                cost_fh[(i, j)] * m.x[i, j] * DAYS_PER_YEAR
                for i in m.F for j in m.H
            )
            # Transport cost: hub→biorefinery
            transport_hb = sum(
                cost_hb[(j, k)] * m.w[j, k] * DAYS_PER_YEAR
                for j in m.H for k in m.B
            )
            # Hub operating cost (only open hubs)
            hub_ops = sum(
                hub_map[j].operating_cost * m.y[j] * DAYS_PER_YEAR
                for j in m.H
            )
            # Carbon tax: emission × tax rate × 1000 (kg→ton conversion)
            carbon_cost = sum(
                emit_fh[(i, j)] * m.x[i, j] * DAYS_PER_YEAR * inp.carbon_tax_usd_per_kg
                for i in m.F for j in m.H
            ) + sum(
                emit_hb[(j, k)] * m.w[j, k] * DAYS_PER_YEAR * inp.carbon_tax_usd_per_kg
                for j in m.H for k in m.B
            )
            return transport_fh + transport_hb + hub_ops + carbon_cost

        model.TAC = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

        # ─── Constraints ─────────────────────────────────────────────────
        # C1: Farm supply constraint (cannot exceed daily supply)
        def farm_supply_rule(m, i):
            return sum(m.x[i, j] for j in m.H) <= farm_map[i].supply
        model.c_farm_supply = pyo.Constraint(model.F, rule=farm_supply_rule)

        # C2: Hub capacity (only if open)
        def hub_capacity_rule(m, j):
            return sum(m.x[i, j] for i in m.F) <= hub_map[j].capacity * m.y[j]
        model.c_hub_capacity = pyo.Constraint(model.H, rule=hub_capacity_rule)

        # C3: Hub mass balance (outflow ≤ inflow)
        def hub_balance_rule(m, j):
            inflow = sum(m.x[i, j] for i in m.F)
            outflow = sum(m.w[j, k] for k in m.B)
            return outflow <= inflow
        model.c_hub_balance = pyo.Constraint(model.H, rule=hub_balance_rule)

        # C4: Biorefinery capacity
        def bio_capacity_rule(m, k):
            return sum(m.w[j, k] for j in m.H) <= bio_map[k].capacity
        model.c_bio_capacity = pyo.Constraint(model.B, rule=bio_capacity_rule)

        # C5 (optional): Emission limit (ton CO2/year)
        if inp.emission_limit_ton_co2 is not None:
            def emission_limit_rule(m):
                total_emission_kg = sum(
                    emit_fh[(i, j)] * m.x[i, j] * DAYS_PER_YEAR for i in m.F for j in m.H
                ) + sum(
                    emit_hb[(j, k)] * m.w[j, k] * DAYS_PER_YEAR for j in m.H for k in m.B
                )
                return total_emission_kg / 1000 <= inp.emission_limit_ton_co2
            model.c_emission_limit = pyo.Constraint(rule=emission_limit_rule)

        # C6 (optional): Budget constraint
        if inp.max_budget_usd is not None:
            model.c_budget = pyo.Constraint(
                expr=model.TAC <= inp.max_budget_usd
            )

        # ─── Solve ───────────────────────────────────────────────────────
        solver = SolverFactory(inp.solver_name)
        if not solver.available():
            logger.error(f"Solver '{inp.solver_name}' not available.")
            return OptimizationResult(
                status="error",
                solver_status="solver_unavailable",
                solve_time_seconds=time.time() - t_start,
                error_message=f"Solver '{inp.solver_name}' not found. Install coinor-cbc.",
            )

        # Set solver options
        solver.options["seconds"] = inp.time_limit_seconds  # CBC time limit

        logger.info(f"Starting MILP solve with {inp.solver_name}...")
        solve_result = solver.solve(model, tee=False)
        solve_time = time.time() - t_start

        # ─── Parse solver status ─────────────────────────────────────────
        sol_status = solve_result.solver.status
        term_cond = solve_result.solver.termination_condition

        if term_cond == TerminationCondition.infeasible:
            return OptimizationResult(
                status="infeasible",
                solver_status=str(term_cond),
                solve_time_seconds=solve_time,
                error_message="Problem is infeasible. Relax constraints (budget, emission limit).",
            )

        is_optimal = term_cond == TerminationCondition.optimal
        is_feasible = term_cond in (
            TerminationCondition.maxTimeLimit,
            TerminationCondition.maxIterations,
            TerminationCondition.feasible,
        )

        if not (is_optimal or is_feasible):
            return OptimizationResult(
                status="error",
                solver_status=str(term_cond),
                solve_time_seconds=solve_time,
                error_message=f"Solver returned unexpected status: {term_cond}",
            )

        # ─── Extract results ─────────────────────────────────────────────
        tac = pyo.value(model.TAC)
        open_hubs = [j for j in H if pyo.value(model.y[j]) > 0.5]

        # Transport costs breakdown
        tc_fh = sum(
            cost_fh[(i, j)] * pyo.value(model.x[i, j]) * DAYS_PER_YEAR
            for i in F for j in H
        )
        tc_hb = sum(
            cost_hb[(j, k)] * pyo.value(model.w[j, k]) * DAYS_PER_YEAR
            for j in H for k in B
        )
        hub_ops_cost = sum(
            hub_map[j].operating_cost * pyo.value(model.y[j]) * DAYS_PER_YEAR
            for j in H
        )
        carbon_cost = sum(
            emit_fh[(i, j)] * pyo.value(model.x[i, j]) * DAYS_PER_YEAR * inp.carbon_tax_usd_per_kg
            for i in F for j in H
        ) + sum(
            emit_hb[(j, k)] * pyo.value(model.w[j, k]) * DAYS_PER_YEAR * inp.carbon_tax_usd_per_kg
            for j in H for k in B
        )

        # Total emissions (ton CO2/year)
        total_emission_kg = sum(
            emit_fh[(i, j)] * pyo.value(model.x[i, j]) * DAYS_PER_YEAR for i in F for j in H
        ) + sum(
            emit_hb[(j, k)] * pyo.value(model.w[j, k]) * DAYS_PER_YEAR for j in H for k in B
        )
        total_emission_ton = total_emission_kg / 1000

        # Total corncob throughput
        total_corncob = sum(
            sum(pyo.value(model.w[j, k]) for k in B) for j in H
        )
        total_ethanol = total_corncob * DAYS_PER_YEAR * ETHANOL_YIELD_LITER_PER_TON

        # MESP: TAC / total ethanol produced
        mesp = tac / total_ethanol if total_ethanol > 0 else 0.0

        # Build route list (flows > threshold)
        FLOW_THRESHOLD = 0.01  # ton/day — filter near-zero flows
        routes: List[RouteFlow] = []

        for i in F:
            for j in H:
                flow = pyo.value(model.x[i, j])
                if flow > FLOW_THRESHOLD:
                    routes.append(RouteFlow(
                        from_id=i, to_id=j,
                        from_type="farm", to_type="hub",
                        flow_ton_day=round(flow, 4),
                        distance_km=round(dist_fh[(i, j)], 2),
                        cost_usd_day=round(cost_fh[(i, j)] * flow, 4),
                        emission_kg_co2_day=round(emit_fh[(i, j)] * flow, 4),
                    ))

        for j in H:
            for k in B:
                flow = pyo.value(model.w[j, k])
                if flow > FLOW_THRESHOLD:
                    routes.append(RouteFlow(
                        from_id=j, to_id=k,
                        from_type="hub", to_type="biorefinery",
                        flow_ton_day=round(flow, 4),
                        distance_km=round(dist_hb[(j, k)], 2),
                        cost_usd_day=round(cost_hb[(j, k)] * flow, 4),
                        emission_kg_co2_day=round(emit_hb[(j, k)] * flow, 4),
                    ))

        return OptimizationResult(
            status="optimal" if is_optimal else "feasible",
            solver_status=str(term_cond),
            solve_time_seconds=round(solve_time, 2),
            total_annual_cost_usd=round(tac, 2),
            transport_cost_usd_year=round(tc_fh + tc_hb, 2),
            hub_operating_cost_usd_year=round(hub_ops_cost, 2),
            carbon_tax_cost_usd_year=round(carbon_cost, 2),
            total_emission_ton_co2_year=round(total_emission_ton, 4),
            total_corncob_ton_day=round(total_corncob, 4),
            total_ethanol_liter_year=round(total_ethanol, 2),
            mesp_usd_per_liter=round(mesp, 6),
            open_hubs=open_hubs,
            routes=routes,
        )

    except Exception as exc:
        logger.exception("Optimization engine error")
        return OptimizationResult(
            status="error",
            solver_status="exception",
            solve_time_seconds=time.time() - t_start,
            error_message=str(exc),
        )
