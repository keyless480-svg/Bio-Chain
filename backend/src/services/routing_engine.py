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

Solver: heuristik konstruktif (nearest-neighbor, truk terbesar dulu) + perbaikan
2-opt per rute — bukan solver MILP/constraint-programming eksternal. Pilihan ini
disengaja: OR-Tools (native C++, puluhan MB) terbukti membuat fungsi serverless
di Vercel gagal invoke sama sekali (lihat riwayat commit). Untuk ukuran masalah
di sini (puluhan titik per klaster hub, bukan ribuan), heuristik konstruktif +
2-opt biasanya mendekati optimal dan cukup untuk kebutuhan operasional harian —
trade-off standar dalam literatur VRP ketika ukuran masalah kecil dan keandalan
deployment lebih penting daripada optimalitas eksak.
"""
import logging
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

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


def _dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return road_distance_km(a[0], a[1], b[0], b[1])


def _route_total_km(depot: Tuple[float, float], order: List[StopDemand]) -> float:
    if not order:
        return 0.0
    total = _dist(depot, (order[0].lat, order[0].lon))
    for a, b in zip(order, order[1:]):
        total += _dist((a.lat, a.lon), (b.lat, b.lon))
    total += _dist((order[-1].lat, order[-1].lon), depot)
    return total


def _two_opt(depot: Tuple[float, float], order: List[StopDemand]) -> List[StopDemand]:
    """Perbaikan lokal standar: coba balik tiap sub-segmen, simpan bila total
    jarak turun. O(n^2) per pass — cukup cepat untuk puluhan titik per klaster."""
    if len(order) < 3:
        return order

    best = order[:]
    best_km = _route_total_km(depot, best)
    improved = True
    while improved:
        improved = False
        for i in range(len(best) - 1):
            for j in range(i + 1, len(best)):
                candidate = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                candidate_km = _route_total_km(depot, candidate)
                if candidate_km + 1e-9 < best_km:
                    best, best_km = candidate, candidate_km
                    improved = True
    return best


def _greedy_assign(
    depot: Tuple[float, float],
    demands: List[StopDemand],
    fleet: List[FleetVehicle],
) -> List[Tuple[FleetVehicle, List[StopDemand]]]:
    """Truk kapasitas terbesar dulu (konsolidasi maksimal, minimkan jumlah trip
    berbayar), lalu nearest-neighbor dari titik terakhir untuk mengisi tiap truk
    sampai kapasitasnya habis atau tidak ada titik tersisa yang muat."""
    remaining = demands[:]
    assignments: List[Tuple[FleetVehicle, List[StopDemand]]] = []

    for vehicle in sorted(fleet, key=lambda v: v.capacity_ton, reverse=True):
        if not remaining:
            break
        route: List[StopDemand] = []
        load = 0.0
        current = depot
        while True:
            candidates = [d for d in remaining if load + d.weight_ton <= vehicle.capacity_ton]
            if not candidates:
                break
            nearest = min(candidates, key=lambda d: _dist(current, (d.lat, d.lon)))
            route.append(nearest)
            remaining.remove(nearest)
            load += nearest.weight_ton
            current = (nearest.lat, nearest.lon)
        if route:
            assignments.append((vehicle, route))

    if remaining:
        logger.warning(
            f"CVRP: {len(remaining)} titik jemput tidak terangkut — "
            f"total demand melebihi total kapasitas armada tersedia hari ini."
        )
    return assignments


def solve_daily_routes(
    depot: Tuple[float, float],
    demands: List[StopDemand],
    fleet: List[FleetVehicle],
) -> List[RouteResult]:
    """CVRP + Time Windows heterogen untuk satu klaster hub pada satu hari.

    Mengembalikan list kosong bila tidak ada demand atau tidak ada armada.
    Titik yang tidak muat di armada manapun (total demand > total kapasitas)
    tetap tidak terangkut — status Harvest-nya tidak berubah, akan otomatis
    ikut batch berikutnya.
    """
    settings = get_settings()

    if not demands or not fleet:
        return []

    assignments = _greedy_assign(depot, demands, fleet)

    results = []
    for vehicle, order in assignments:
        order = _two_opt(depot, order)

        stops: List[RouteStopResult] = []
        tw_penalty = 0.0
        degradation_cost = 0.0
        elapsed_min = 0.0
        current = depot

        for seq, stop in enumerate(order, start=1):
            leg_km = _dist(current, (stop.lat, stop.lon))
            elapsed_min += (leg_km / settings.avg_truck_speed_kmph) * 60.0
            arrival = int(round(elapsed_min))

            stops.append(RouteStopResult(
                node_id=stop.node_id, farmer_id=stop.farmer_id,
                sequence_no=seq, eta_minutes=arrival,
            ))
            # Variabel #1: penalti time-window
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
            current = (stop.lat, stop.lon)

        total_km = _route_total_km(depot, order)
        fuel_liters = total_km * vehicle.fuel_rate_l_per_km
        fuel_cost = fuel_liters * vehicle.fuel_price_per_liter
        # Variabel #3: pajak karbon arc-level (BBM aktual, bukan proxy per-ton rata-rata)
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
