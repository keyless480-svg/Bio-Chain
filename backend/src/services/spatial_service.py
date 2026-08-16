"""
services/spatial_service.py — Spatial computation utilities.
Computes distance, transport costs (BBM+tol+supir), emissions.
All costs in IDR (Rupiah).
"""
import math
from typing import List, Dict, Tuple

from src.config import get_settings

settings = get_settings()


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points (km)."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def road_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Estimate road distance using Haversine x road factor."""
    return haversine_km(lat1, lon1, lat2, lon2) * settings.road_factor


def fuel_cost_per_trip(distance_km: float) -> float:
    """BBM cost for one truck trip (IDR)."""
    return distance_km * settings.truck_fuel_per_km * settings.diesel_price_per_liter


def toll_cost_per_trip(distance_km: float) -> float:
    """Estimated toll cost (IDR)."""
    return distance_km * settings.toll_cost_per_km


def driver_cost_per_trip() -> float:
    """Driver wages + meal allowance per trip (IDR)."""
    return settings.driver_cost_per_trip


def carbon_emission_kg(distance_km: float) -> float:
    """CO2 emission for one truck trip (kg CO2)."""
    return distance_km * settings.truck_fuel_per_km * settings.co2_per_liter_diesel


def transport_cost_per_ton(distance_km: float) -> float:
    """Total transport cost per ton of cargo (IDR/ton)."""
    total_trip = fuel_cost_per_trip(distance_km) + toll_cost_per_trip(distance_km) + driver_cost_per_trip()
    return total_trip / settings.truck_capacity_ton


def emission_kg_co2_per_ton(distance_km: float) -> float:
    """CO2 emission per ton of cargo (kg CO2/ton)."""
    return carbon_emission_kg(distance_km) / settings.truck_capacity_ton


def full_transport_breakdown(distance_km: float) -> Dict[str, float]:
    """Full breakdown of transport costs for a trip."""
    fuel = fuel_cost_per_trip(distance_km)
    toll = toll_cost_per_trip(distance_km)
    driver = driver_cost_per_trip()
    emission = carbon_emission_kg(distance_km)
    carbon_tax = emission * settings.lambda_green
    return {
        "fuel_cost": fuel,
        "toll_cost": toll,
        "driver_cost": driver,
        "total_transport": fuel + toll + driver,
        "carbon_emitted_kg": emission,
        "carbon_tax_cost": carbon_tax,
    }


def check_truck_utilization(payload_ton: float) -> Tuple[bool, float]:
    """Check if truck utilization >= 95%. Returns (is_ok, utilization_pct)."""
    util = payload_ton / settings.truck_capacity_ton
    return util >= settings.truck_min_utilization_pct, round(util * 100, 1)


def build_cost_matrix(
    origins: List[Dict],
    destinations: List[Dict],
) -> Tuple[Dict[Tuple[int, int], float], Dict[Tuple[int, int], float]]:
    """
    Build transport cost (IDR/ton) and emission (kg CO2/ton) matrices.
    Returns (cost_matrix, emission_matrix).
    """
    cost_matrix = {}
    emission_matrix = {}
    for o in origins:
        for d in destinations:
            dist = road_distance_km(o["lat"], o["lon"], d["lat"], d["lon"])
            cost_matrix[(o["id"], d["id"])] = transport_cost_per_ton(dist)
            emission_matrix[(o["id"], d["id"])] = emission_kg_co2_per_ton(dist)
    return cost_matrix, emission_matrix


def build_distance_matrix(
    origins: List[Dict],
    destinations: List[Dict],
) -> Dict[Tuple[int, int], float]:
    """Build distance matrix (km)."""
    matrix = {}
    for o in origins:
        for d in destinations:
            matrix[(o["id"], d["id"])] = road_distance_km(o["lat"], o["lon"], d["lat"], d["lon"])
    return matrix
