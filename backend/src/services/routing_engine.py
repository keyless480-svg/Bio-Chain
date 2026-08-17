"""
services/routing_engine.py — Lapis 2: Heterogeneous CVRP + Time Windows (Green-VRP).

Menerima titik jemput konkret (Harvest yang sudah tercatat, dikelompokkan per hub
sebagai depot) dan armada yang tersedia hari itu, lalu mengeluarkan rute optimal
per kendaraan: urutan kunjungan, ETA per titik, dan breakdown biaya (BBM, pajak
karbon arc-level, penalti time-window, degradasi mutu akibat waktu tunggu).

Lapis 1 (optimization_engine.py) memutuskan KEMANA barang mengalir (farm -> hub
mana). Lapis 2 di sini memutuskan BAGAIMANA armada benar-benar mengambilnya hari
itu. Keduanya tidak saling menimpa: Lapis 2 hanya mewujudkan realisasi fisik dari
alokasi yang sudah diputuskan Lapis 1 (lihat catatan pengikat di dokumentasi
arsitektur — Σᵥ x[v,i,j] = x[i,j]).
"""
import logging
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

from ortools.constraint_solver import routing_enums_pb2, pywrapcp

from src.services.spatial_service import road_distance_km
from src.config import get_settings

logger = logging.getLogger(__name__)

CO2_PER_LITER_SOLAR = 2.68  # kg CO2/liter — IPCC Tier 2, sama dengan config.py co2_per_liter_diesel


@dataclass
class StopDemand:
    """Satu titik jemput konkret — biasanya 1 Harvest dari 1 petani."""
    node_id: int              # id sumber (mis. harvest_id)
    farmer_id: Optional[int]
    lat: float
    lon: float
    weight_ton: float
    price_per_ton: float           # untuk biaya degradasi mutu
    window_open_min: int           # menit sejak start-of-day (00:00)
    window_close_min: int


@dataclass
class FleetVehicle:
    vehicle_id: int
    capacity_ton: float
    fuel_rate_l_per_km: float      # φᵥ, liter/km
    fixed_charter_cost: float      # C_v^fix, IDR/trip
    fuel_price_per_liter: float
    carbon_tax_per_kg: float       # λ, IDR/kg CO2


@dataclass
class RouteStopResult:
    node_id: int
    farmer_id: Optional[int]
    sequence_no: int
    eta_minutes: int


@dataclass
class RouteResult:
    vehicle_id: int
    stops: List[RouteStopResult] = field(default_factory=list)
    distance_km: float = 0.0
    fuel_cost: float = 0.0
    carbon_tax: float = 0.0
    time_window_penalty: float = 0.0
    degradation_cost: float = 0.0
    total_route_cost: float = 0.0


def _build_distance_matrix(depot: Tuple[float, float], stops: List[StopDemand]) -> List[List[float]]:
    """Matriks jarak km, index 0 = depot (hub). Titik ganti mudah dengan Distance Matrix
    API sungguhan (Google/OSRM) — signature fungsi ini sengaja tidak berubah kalau itu terjadi."""
    points = [depot] + [(s.lat, s.lon) for s in stops]
    n = len(points)
    return [
        [road_distance_km(points[i][0], points[i][1], points[j][0], points[j][1]) for j in range(n)]
        for i in range(n)
    ]


def solve_daily_routes(
    depot: Tuple[float, float],
    demands: List[StopDemand],
    fleet: List[FleetVehicle],
) -> List[RouteResult]:
    """CVRP + Time Windows heterogen untuk satu klaster hub pada satu hari.

    Mengembalikan list kosong bila tidak ada demand, tidak ada armada, atau
    solver tidak menemukan solusi feasible dalam batas waktu (mis. total
    demand melebihi total kapasitas armada tersedia).
    """
    settings = get_settings()

    if not demands or not fleet:
        return []

    n_stops = len(demands)
    dist_matrix = _build_distance_matrix(depot, demands)

    manager = pywrapcp.RoutingIndexManager(n_stops + 1, len(fleet), 0)
    routing = pywrapcp.RoutingModel(manager)

    # --- Biaya per-arc, per-kendaraan: BBM aktual + pajak karbon arc-level (Variabel #3) ---
    def make_cost_callback(vehicle: FleetVehicle):
        def cost_callback(from_index, to_index):
            i, j = manager.IndexToNode(from_index), manager.IndexToNode(to_index)
            km = dist_matrix[i][j]
            fuel_liters = km * vehicle.fuel_rate_l_per_km
            fuel_cost = fuel_liters * vehicle.fuel_price_per_liter
            carbon_kg = fuel_liters * CO2_PER_LITER_SOLAR
            carbon_tax = carbon_kg * vehicle.carbon_tax_per_kg
            return int(fuel_cost + carbon_tax)
        return cost_callback

    for v_idx, vehicle in enumerate(fleet):
        cb_index = routing.RegisterTransitCallback(make_cost_callback(vehicle))
        routing.SetArcCostEvaluatorOfVehicle(cb_index, v_idx)
        routing.SetFixedCostOfVehicle(int(vehicle.fixed_charter_cost), v_idx)

    # --- Kapasitas kendaraan (Qv) ---
    demand_weights_kg = [0] + [int(round(d.weight_ton * 1000)) for d in demands]

    def demand_callback(from_index):
        return demand_weights_kg[manager.IndexToNode(from_index)]

    demand_cb_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_cb_index,
        0,
        [int(round(v.capacity_ton * 1000)) for v in fleet],
        True,
        "Capacity",
    )

    # --- Waktu tempuh + time windows (Variabel #1) ---
    horizon_minutes = max(settings.factory_sla_deadline_minutes, 24 * 60)

    def time_callback(from_index, to_index):
        i, j = manager.IndexToNode(from_index), manager.IndexToNode(to_index)
        return int(round(dist_matrix[i][j] / settings.avg_truck_speed_kmph * 60))

    time_cb_index = routing.RegisterTransitCallback(time_callback)
    routing.AddDimension(time_cb_index, horizon_minutes, horizon_minutes, False, "Time")
    time_dim = routing.GetDimensionOrDie("Time")

    for i, d in enumerate(demands):
        index = manager.NodeToIndex(i + 1)
        time_dim.SetCumulVarSoftLowerBound(
            index, d.window_open_min, int(settings.time_window_early_penalty_per_min)
        )
        time_dim.SetCumulVarSoftUpperBound(
            index, d.window_close_min, int(settings.time_window_late_penalty_per_min)
        )

    # --- Solve ---
    search = pywrapcp.DefaultRoutingSearchParameters()
    search.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search.time_limit.FromSeconds(settings.cvrp_solver_time_limit_seconds)

    solution = routing.SolveWithParameters(search)
    if solution is None:
        logger.warning("CVRP: tidak ada solusi feasible (cek total demand vs total kapasitas armada)")
        return []

    return _extract_routes(manager, routing, solution, time_dim, demands, fleet, dist_matrix, settings)


def _extract_routes(manager, routing, solution, time_dim, demands, fleet, dist_matrix, settings) -> List[RouteResult]:
    results = []
    for v_idx, vehicle in enumerate(fleet):
        index = routing.Start(v_idx)
        stops: List[RouteStopResult] = []
        total_km = 0.0
        tw_penalty = 0.0
        degradation_cost = 0.0
        seq = 0

        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            arrival = solution.Value(time_dim.CumulVar(index))
            if node != 0:
                seq += 1
                stop = demands[node - 1]
                stops.append(RouteStopResult(
                    node_id=stop.node_id, farmer_id=stop.farmer_id,
                    sequence_no=seq, eta_minutes=arrival,
                ))
                # Variabel #1: penalti time-window, dihitung ulang dari ETA vs jendela
                if arrival < stop.window_open_min:
                    tw_penalty += (stop.window_open_min - arrival) * settings.time_window_early_penalty_per_min
                elif arrival > stop.window_close_min:
                    tw_penalty += (arrival - stop.window_close_min) * settings.time_window_late_penalty_per_min
                # Variabel #2: degradasi mutu sebagai fungsi waktu tunggu sejak jendela buka
                wait_hours = max(0, arrival - stop.window_open_min) / 60.0
                degradation_cost += (
                    stop.weight_ton * stop.price_per_ton
                    * (settings.degradation_rate_pct_per_hour / 100.0) * wait_hours
                )
            prev = index
            index = solution.Value(routing.NextVar(index))
            # Termasuk leg terakhir kembali ke depot — truk memang benar-benar menempuhnya.
            i, j = manager.IndexToNode(prev), manager.IndexToNode(index)
            total_km += dist_matrix[i][j]

        if not stops:
            continue

        fuel_liters = total_km * vehicle.fuel_rate_l_per_km
        fuel_cost = fuel_liters * vehicle.fuel_price_per_liter
        carbon_tax = fuel_liters * CO2_PER_LITER_SOLAR * vehicle.carbon_tax_per_kg

        results.append(RouteResult(
            vehicle_id=vehicle.vehicle_id,
            stops=stops,
            distance_km=round(total_km, 2),
            fuel_cost=round(fuel_cost, 0),
            carbon_tax=round(carbon_tax, 0),
            time_window_penalty=round(tw_penalty, 0),
            degradation_cost=round(degradation_cost, 0),
            total_route_cost=round(
                vehicle.fixed_charter_cost + fuel_cost + carbon_tax + tw_penalty + degradation_cost, 0
            ),
        ))
    return results
