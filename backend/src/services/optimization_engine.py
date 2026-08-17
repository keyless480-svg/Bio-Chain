"""
services/optimization_engine.py — Multi-Objective MILP (Pyomo + HiGHS).

5-Step Circular Flow Optimization:
  min Z = Σᵢ Σⱼ (Pᵢ·Xᵢⱼ + Tᵢⱼ·Xᵢⱼ)    [Hulu→Pengepul]
        + Σⱼ Σₖ (Hⱼ·Yⱼₖ + Tⱼₖ·Yⱼₖ)    [Pengepul→Pabrik]
        + C_pabrik                          [Biaya Pabrik]
        + λ·Σ(EF·D·Yⱼₖ)                   [Green Penalty]
        + γ·Σ(Rⱼ)                          [Resilience Penalty]

With shrinkage constraint: Σ Xᵢⱼ × (1-sⱼ) = Yⱼₖ + ΔIⱼ
Buffer constraint: Iⱼₜ ≥ 0.2 × avg_daily_shipment

All costs in IDR (Rupiah).
"""
import time
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Tuple

import pyomo.environ as pyo
from pyomo.opt import SolverFactory, TerminationCondition

from src.services.spatial_service import build_cost_matrix, emission_kg_co2_per_ton, road_distance_km

logger = logging.getLogger(__name__)

DAYS_PER_YEAR = 365
ETHANOL_YIELD_LITER_PER_TON = 280.0


@dataclass
class FarmerNode:
    id: int
    lat: float
    lon: float
    supply: float              # ton/day
    harvest_cost_per_ton: float  # IDR/ton
    packing_cost_per_ton: float  # IDR/ton
    price_per_ton: float       # IDR/ton (buying price = 850 * 1000)
    supply_variability: float  # 0-1


@dataclass
class HubNode:
    id: int
    lat: float
    lon: float
    capacity: float            # ton/day
    loading_cost_per_ton: float  # IDR/ton
    drying_cost_per_ton: float   # IDR/ton
    storage_cost_per_day: float  # IDR/day
    operating_cost_per_day: float  # IDR/day
    shrinkage_rate: float      # 0-1 (e.g., 0.18)
    buffer_stock_pct: float    # 0-1 (e.g., 0.20)
    supply_variability: float  # 0-1


@dataclass
class FactoryNode:
    id: int
    lat: float
    lon: float
    capacity: float
    processing_cost_per_ton: float  # IDR/ton
    depreciation_per_day: float     # IDR/day


@dataclass
class OptimizationInput:
    farmers: List[FarmerNode]
    hubs: List[HubNode]
    factories: List[FactoryNode]
    lambda_green: float = 465.0          # IDR/kg CO2
    gamma_resilience: float = 500000.0   # IDR per unit risk
    carbon_tax_per_kg: float = 465.0     # IDR/kg CO2
    max_budget: Optional[float] = None
    emission_limit_ton_co2: Optional[float] = None
    solver_name: str = "appsi_highs"
    time_limit_seconds: int = 300
    # Variabel tambahan #2 (lihat blueprint arsitektur): degradasi mutu sebagai
    # fungsi waktu tempuh, bukan shrinkage_rate konstan. Estimasi waktu tempuh di
    # Lapis 1 dipakai sebagai proxy (belum ada urutan rute konkret — itu Lapis 2).
    degradation_rate_pct_per_hour: float = 0.4
    avg_truck_speed_kmph: float = 40.0


@dataclass
class RouteFlow:
    from_id: int
    to_id: int
    from_type: str       # 'farmer' | 'hub'
    to_type: str         # 'hub' | 'factory'
    flow_ton_day: float
    distance_km: float
    transport_cost_day: float     # IDR/day
    emission_kg_co2_day: float
    # ABC cost components
    fuel_cost_day: float = 0.0
    toll_cost_day: float = 0.0
    driver_cost_day: float = 0.0


@dataclass
class OptimizationResult:
    status: str
    solver_status: str
    solve_time_seconds: float
    # Cost breakdown (IDR/year)
    total_annual_cost: float = 0.0
    harvest_cost_year: float = 0.0       # Step 1: panen + karung
    hub_handling_cost_year: float = 0.0  # Step 2: loading + drying + storage
    shrinkage_cost_year: float = 0.0     # Step 2: biaya hantu
    transport_fh_cost_year: float = 0.0  # Step 1→2: transport farm→hub
    transport_hf_cost_year: float = 0.0  # Step 3: transport hub→factory
    factory_cost_year: float = 0.0       # Step 4: processing + depreciation
    green_penalty_year: float = 0.0      # Pajak karbon
    resilience_penalty_year: float = 0.0  # Penalti risiko
    degradation_penalty_year: float = 0.0  # Variabel #2: susut mutu akibat waktu tempuh
    # KPI
    total_emission_ton_co2_year: float = 0.0
    total_corncob_ton_day: float = 0.0
    total_corncob_after_shrinkage: float = 0.0
    total_ethanol_liter_year: float = 0.0
    total_shrinkage_ton_year: float = 0.0
    hpp_per_kg: float = 0.0              # IDR/kg
    hpp_per_liter_ethanol: float = 0.0   # IDR/liter
    fair_trade_margin_pct: float = 0.0
    buffer_stock_avg_pct: float = 0.0
    active_hubs: List[int] = field(default_factory=list)
    routes: List[RouteFlow] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["routes"] = [asdict(r) for r in self.routes]
        return d


def run_optimization(inp: OptimizationInput) -> OptimizationResult:
    """Execute the multi-objective MILP model."""
    t_start = time.time()

    try:
        # Build spatial matrices
        farm_nodes = [{"id": f.id, "lat": f.lat, "lon": f.lon} for f in inp.farmers]
        hub_nodes = [{"id": h.id, "lat": h.lat, "lon": h.lon} for h in inp.hubs]
        fac_nodes = [{"id": k.id, "lat": k.lat, "lon": k.lon} for k in inp.factories]

        cost_fh, emit_fh = build_cost_matrix(farm_nodes, hub_nodes)
        cost_hf, emit_hf = build_cost_matrix(hub_nodes, fac_nodes)
        dist_fh = {(f["id"], h["id"]): road_distance_km(f["lat"], f["lon"], h["lat"], h["lon"])
                   for f in farm_nodes for h in hub_nodes}
        dist_hf = {(h["id"], k["id"]): road_distance_km(h["lat"], h["lon"], k["lat"], k["lon"])
                   for h in hub_nodes for k in fac_nodes}

        farm_map = {f.id: f for f in inp.farmers}
        hub_map = {h.id: h for h in inp.hubs}
        fac_map = {k.id: k for k in inp.factories}

        F = [f.id for f in inp.farmers]
        H = [h.id for h in inp.hubs]
        K = [k.id for k in inp.factories]

        # ── Pyomo Model ──
        model = pyo.ConcreteModel(name="BioChain-5Step")
        model.F = pyo.Set(initialize=F)
        model.H = pyo.Set(initialize=H)
        model.K = pyo.Set(initialize=K)

        # Decision variables
        model.x = pyo.Var(model.F, model.H, domain=pyo.NonNegativeReals)  # Farmer→Hub flow
        model.y = pyo.Var(model.H, model.K, domain=pyo.NonNegativeReals)  # Hub→Factory flow
        model.z = pyo.Var(model.H, domain=pyo.Binary)                     # Hub open/close
        model.b = pyo.Var(model.H, domain=pyo.NonNegativeReals)           # Buffer stock at hub

        # ── Objective: Minimize Z ──
        def objective_rule(m):
            # Step 1: Biaya Hulu (harvest + packing + acquisition)
            hulu_cost = sum(
                (farm_map[i].harvest_cost_per_ton + farm_map[i].packing_cost_per_ton) * m.x[i, j] * DAYS_PER_YEAR
                for i in m.F for j in m.H
            )
            # Transport Farm→Hub
            transport_fh = sum(
                cost_fh[(i, j)] * m.x[i, j] * DAYS_PER_YEAR
                for i in m.F for j in m.H
            )
            # Step 2: Hub handling (loading + drying + storage + operating)
            hub_handling = sum(
                (hub_map[j].loading_cost_per_ton + hub_map[j].drying_cost_per_ton)
                * sum(m.x[i, j] for i in m.F) * DAYS_PER_YEAR
                + hub_map[j].storage_cost_per_day * m.z[j] * DAYS_PER_YEAR
                + hub_map[j].operating_cost_per_day * m.z[j] * DAYS_PER_YEAR
                for j in m.H
            )
            # Shrinkage cost (biaya hantu: lost weight × price per kg × 1000 kg/ton)
            shrinkage_cost = sum(
                hub_map[j].shrinkage_rate * sum(m.x[i, j] for i in m.F) * 850000.0 * DAYS_PER_YEAR
                for j in m.H
            )
            # Step 3: Transport Hub→Factory
            transport_hf = sum(
                cost_hf[(j, k)] * m.y[j, k] * DAYS_PER_YEAR
                for j in m.H for k in m.K
            )
            # Step 4: Factory processing + depreciation
            factory_cost = sum(
                fac_map[k].processing_cost_per_ton * sum(m.y[j, k] for j in m.H) * DAYS_PER_YEAR
                + fac_map[k].depreciation_per_day * DAYS_PER_YEAR
                for k in m.K
            )
            # Green Penalty: λ × emission (kg CO2) from all transport
            green_penalty = inp.lambda_green * (
                sum(emit_fh[(i, j)] * m.x[i, j] * DAYS_PER_YEAR for i in m.F for j in m.H)
                + sum(emit_hf[(j, k)] * m.y[j, k] * DAYS_PER_YEAR for j in m.H for k in m.K)
            )
            # Resilience Penalty: γ × supply_variability for each active hub
            resilience_penalty = inp.gamma_resilience * sum(
                hub_map[j].supply_variability * m.z[j] for j in m.H
            )
            # Degradation Penalty (Variabel #2): waktu tempuh (proxy jarak/kecepatan) ×
            # laju kenaikan kadar air × nilai muatan. Farm→Hub pakai harga beli petani;
            # Hub→Factory pakai harga pasar bonggol kering (dianggap sama, 850/kg).
            degradation_penalty = (inp.degradation_rate_pct_per_hour / 100.0) * (
                sum(
                    (dist_fh[(i, j)] / inp.avg_truck_speed_kmph) * m.x[i, j]
                    * farm_map[i].price_per_ton * DAYS_PER_YEAR
                    for i in m.F for j in m.H
                )
                + sum(
                    (dist_hf[(j, k)] / inp.avg_truck_speed_kmph) * m.y[j, k]
                    * 850000.0 * DAYS_PER_YEAR
                    for j in m.H for k in m.K
                )
            )
            return (hulu_cost + transport_fh + hub_handling + shrinkage_cost
                    + transport_hf + factory_cost + green_penalty + resilience_penalty
                    + degradation_penalty)

        model.OBJ = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

        # ── Constraints ──
        # C1: Farm supply limit
        def farm_supply_rule(m, i):
            return sum(m.x[i, j] for j in m.H) <= farm_map[i].supply
        model.c_farm = pyo.Constraint(model.F, rule=farm_supply_rule)

        # C2: Hub capacity (only if open)
        def hub_cap_rule(m, j):
            return sum(m.x[i, j] for i in m.F) <= hub_map[j].capacity * m.z[j]
        model.c_hub_cap = pyo.Constraint(model.H, rule=hub_cap_rule)

        # C3: Hub mass balance WITH SHRINKAGE
        # Outflow = Inflow × (1 - shrinkage) - buffer
        def hub_balance_rule(m, j):
            inflow = sum(m.x[i, j] for i in m.F)
            outflow = sum(m.y[j, k] for k in m.K)
            return outflow <= inflow * (1 - hub_map[j].shrinkage_rate) - m.b[j]
        model.c_hub_balance = pyo.Constraint(model.H, rule=hub_balance_rule)

        # C4: Buffer stock constraint (≥ 20% of avg daily shipment)
        def buffer_rule(m, j):
            daily_ship = sum(m.y[j, k] for k in m.K)
            return m.b[j] >= hub_map[j].buffer_stock_pct * daily_ship
        model.c_buffer = pyo.Constraint(model.H, rule=buffer_rule)

        # C5: Factory capacity
        def fac_cap_rule(m, k):
            return sum(m.y[j, k] for j in m.H) <= fac_map[k].capacity
        model.c_fac_cap = pyo.Constraint(model.K, rule=fac_cap_rule)

        # C6 (optional): Emission limit
        if inp.emission_limit_ton_co2 is not None:
            def emission_rule(m):
                total_kg = (
                    sum(emit_fh[(i, j)] * m.x[i, j] * DAYS_PER_YEAR for i in m.F for j in m.H)
                    + sum(emit_hf[(j, k)] * m.y[j, k] * DAYS_PER_YEAR for j in m.H for k in m.K)
                )
                return total_kg / 1000 <= inp.emission_limit_ton_co2
            model.c_emission = pyo.Constraint(rule=emission_rule)

        # C7 (optional): Budget constraint
        if inp.max_budget is not None:
            model.c_budget = pyo.Constraint(expr=model.OBJ <= inp.max_budget)

        # ── Solve ──
        solver = SolverFactory(inp.solver_name)
        if not solver.available():
            return OptimizationResult(
                status="error", solver_status="solver_unavailable",
                solve_time_seconds=time.time() - t_start,
                error_message=f"Solver '{inp.solver_name}' not found. Install highspy.",
            )

        if hasattr(solver, 'options'):
            solver.options["time_limit"] = inp.time_limit_seconds

        logger.info(f"Starting MILP solve with {inp.solver_name}...")
        solve_result = solver.solve(model, tee=False)
        solve_time = time.time() - t_start

        term_cond = solve_result.solver.termination_condition
        if term_cond == TerminationCondition.infeasible:
            return OptimizationResult(
                status="infeasible", solver_status=str(term_cond),
                solve_time_seconds=solve_time,
                error_message="Model tidak layak (infeasible). Kurangi batasan emisi/anggaran.",
            )

        is_optimal = term_cond == TerminationCondition.optimal
        is_feasible = term_cond in (
            TerminationCondition.maxTimeLimit, TerminationCondition.feasible,
            TerminationCondition.maxIterations,
        )
        if not (is_optimal or is_feasible):
            return OptimizationResult(
                status="error", solver_status=str(term_cond),
                solve_time_seconds=solve_time,
                error_message=f"Status solver tak terduga: {term_cond}",
            )

        # ── Extract Results ──
        active_hubs = [j for j in H if pyo.value(model.z[j]) > 0.5]

        # Cost breakdowns
        harvest_cost = sum(
            (farm_map[i].harvest_cost_per_ton + farm_map[i].packing_cost_per_ton)
            * pyo.value(model.x[i, j]) * DAYS_PER_YEAR
            for i in F for j in H
        )
        transport_fh = sum(
            cost_fh[(i, j)] * pyo.value(model.x[i, j]) * DAYS_PER_YEAR
            for i in F for j in H
        )
        hub_handling = sum(
            (hub_map[j].loading_cost_per_ton + hub_map[j].drying_cost_per_ton)
            * sum(pyo.value(model.x[i, j]) for i in F) * DAYS_PER_YEAR
            + (hub_map[j].storage_cost_per_day + hub_map[j].operating_cost_per_day)
            * pyo.value(model.z[j]) * DAYS_PER_YEAR
            for j in H
        )
        shrinkage_cost = sum(
            hub_map[j].shrinkage_rate * sum(pyo.value(model.x[i, j]) for i in F) * 850000.0 * DAYS_PER_YEAR
            for j in H
        )
        transport_hf = sum(
            cost_hf[(j, k)] * pyo.value(model.y[j, k]) * DAYS_PER_YEAR
            for j in H for k in K
        )
        factory_cost = sum(
            fac_map[k].processing_cost_per_ton * sum(pyo.value(model.y[j, k]) for j in H) * DAYS_PER_YEAR
            + fac_map[k].depreciation_per_day * DAYS_PER_YEAR
            for k in K
        )
        green_penalty = inp.lambda_green * (
            sum(emit_fh[(i, j)] * pyo.value(model.x[i, j]) * DAYS_PER_YEAR for i in F for j in H)
            + sum(emit_hf[(j, k)] * pyo.value(model.y[j, k]) * DAYS_PER_YEAR for j in H for k in K)
        )
        resilience_penalty = inp.gamma_resilience * sum(
            hub_map[j].supply_variability * pyo.value(model.z[j]) for j in H
        )
        degradation_penalty = (inp.degradation_rate_pct_per_hour / 100.0) * (
            sum(
                (dist_fh[(i, j)] / inp.avg_truck_speed_kmph) * pyo.value(model.x[i, j])
                * farm_map[i].price_per_ton * DAYS_PER_YEAR
                for i in F for j in H
            )
            + sum(
                (dist_hf[(j, k)] / inp.avg_truck_speed_kmph) * pyo.value(model.y[j, k])
                * 850000.0 * DAYS_PER_YEAR
                for j in H for k in K
            )
        )
        tac = pyo.value(model.OBJ)

        # Emissions
        total_emission_kg = (
            sum(emit_fh[(i, j)] * pyo.value(model.x[i, j]) * DAYS_PER_YEAR for i in F for j in H)
            + sum(emit_hf[(j, k)] * pyo.value(model.y[j, k]) * DAYS_PER_YEAR for j in H for k in K)
        )

        # Throughput
        total_inflow = sum(sum(pyo.value(model.x[i, j]) for i in F) for j in H)
        total_to_factory = sum(sum(pyo.value(model.y[j, k]) for k in K) for j in H)
        total_shrinkage = total_inflow - total_to_factory - sum(pyo.value(model.b[j]) for j in H)
        total_ethanol = total_to_factory * DAYS_PER_YEAR * ETHANOL_YIELD_LITER_PER_TON

        # HPP
        hpp_per_kg = tac / (total_to_factory * DAYS_PER_YEAR * 1000) if total_to_factory > 0 else 0
        hpp_per_liter = tac / total_ethanol if total_ethanol > 0 else 0

        # Fair trade margin (farmer share of total cost)
        acquisition_cost = sum(
            farm_map[i].price_per_ton * pyo.value(model.x[i, j]) * DAYS_PER_YEAR
            for i in F for j in H
        )
        fair_trade = acquisition_cost / tac * 100 if tac > 0 else 0

        # Buffer stock average
        total_buffer = sum(pyo.value(model.b[j]) for j in H)
        buffer_avg = total_buffer / total_to_factory * 100 if total_to_factory > 0 else 0

        # Build routes
        FLOW_THRESHOLD = 0.01
        routes = []
        for i in F:
            for j in H:
                flow = pyo.value(model.x[i, j])
                if flow > FLOW_THRESHOLD:
                    routes.append(RouteFlow(
                        from_id=i, to_id=j,
                        from_type="farmer", to_type="hub",
                        flow_ton_day=round(flow, 4),
                        distance_km=round(dist_fh[(i, j)], 2),
                        transport_cost_day=round(cost_fh[(i, j)] * flow, 2),
                        emission_kg_co2_day=round(emit_fh[(i, j)] * flow, 4),
                    ))
        for j in H:
            for k in K:
                flow = pyo.value(model.y[j, k])
                if flow > FLOW_THRESHOLD:
                    routes.append(RouteFlow(
                        from_id=j, to_id=k,
                        from_type="hub", to_type="factory",
                        flow_ton_day=round(flow, 4),
                        distance_km=round(dist_hf[(j, k)], 2),
                        transport_cost_day=round(cost_hf[(j, k)] * flow, 2),
                        emission_kg_co2_day=round(emit_hf[(j, k)] * flow, 4),
                    ))

        return OptimizationResult(
            status="optimal" if is_optimal else "feasible",
            solver_status=str(term_cond),
            solve_time_seconds=round(solve_time, 2),
            total_annual_cost=round(tac, 0),
            harvest_cost_year=round(harvest_cost, 0),
            hub_handling_cost_year=round(hub_handling, 0),
            shrinkage_cost_year=round(shrinkage_cost, 0),
            transport_fh_cost_year=round(transport_fh, 0),
            transport_hf_cost_year=round(transport_hf, 0),
            factory_cost_year=round(factory_cost, 0),
            green_penalty_year=round(green_penalty, 0),
            resilience_penalty_year=round(resilience_penalty, 0),
            degradation_penalty_year=round(degradation_penalty, 0),
            total_emission_ton_co2_year=round(total_emission_kg / 1000, 4),
            total_corncob_ton_day=round(total_inflow, 4),
            total_corncob_after_shrinkage=round(total_to_factory, 4),
            total_ethanol_liter_year=round(total_ethanol, 2),
            total_shrinkage_ton_year=round(total_shrinkage * DAYS_PER_YEAR, 2),
            hpp_per_kg=round(hpp_per_kg, 2),
            hpp_per_liter_ethanol=round(hpp_per_liter, 2),
            fair_trade_margin_pct=round(fair_trade, 2),
            buffer_stock_avg_pct=round(buffer_avg, 2),
            active_hubs=active_hubs,
            routes=routes,
        )

    except Exception as exc:
        logger.exception("Optimization engine error")
        return OptimizationResult(
            status="error", solver_status="exception",
            solve_time_seconds=time.time() - t_start,
            error_message=str(exc),
        )
