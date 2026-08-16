"""
services/spatial_service.py — Spatial computation utilities.
Computes distance matrices between supply chain nodes using GeoPandas/Shapely.
Uses Euclidean approximation (road distance factor applied as multiplier).
"""
import math
from typing import List, Dict, Tuple
import numpy as np


# Road distance factor: straight-line distance * 1.4 ≈ road distance in Jawa Timur
ROAD_FACTOR = 1.4

# Truck fuel consumption: liters per km
TRUCK_FUEL_LITERS_PER_KM = 0.35

# Diesel price: USD per liter (approx Pertamina Dex retail)
DIESEL_PRICE_USD_PER_LITER = 0.68

# Truck payload: tons
TRUCK_PAYLOAD_TON = 20.0

# CO2 emission factor for diesel truck: kg CO2 per liter fuel
CO2_PER_LITER_DIESEL = 2.68


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points (Haversine formula).
    Returns distance in kilometers.
    """
    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def road_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Estimate road distance using Haversine × road factor.
    For production, replace with OSRM/Valhalla routing API.
    """
    return haversine_km(lat1, lon1, lat2, lon2) * ROAD_FACTOR


def transport_cost_usd_per_ton(distance_km: float) -> float:
    """
    Calculate transport cost per ton of corncob for a given distance.
    Formula: (distance_km × fuel_per_km × diesel_price) / payload_ton
    """
    fuel_cost_per_trip = distance_km * TRUCK_FUEL_LITERS_PER_KM * DIESEL_PRICE_USD_PER_LITER
    return fuel_cost_per_trip / TRUCK_PAYLOAD_TON


def emission_kg_co2_per_ton(distance_km: float) -> float:
    """
    Calculate CO2 emission per ton of cargo for a given road distance.
    Formula: (distance_km × fuel_per_km × CO2_per_liter) / payload_ton
    """
    emission_per_trip = distance_km * TRUCK_FUEL_LITERS_PER_KM * CO2_PER_LITER_DIESEL
    return emission_per_trip / TRUCK_PAYLOAD_TON


def build_distance_matrix(
    origins: List[Dict],  # [{"id": int, "lat": float, "lon": float}]
    destinations: List[Dict],
) -> Dict[Tuple[int, int], float]:
    """
    Build a full distance matrix (km) between origin and destination nodes.
    Returns dict keyed by (origin_id, destination_id).
    """
    matrix: Dict[Tuple[int, int], float] = {}
    for o in origins:
        for d in destinations:
            dist = road_distance_km(o["lat"], o["lon"], d["lat"], d["lon"])
            matrix[(o["id"], d["id"])] = dist
    return matrix


def build_cost_matrix(
    origins: List[Dict],
    destinations: List[Dict],
) -> Tuple[Dict[Tuple[int, int], float], Dict[Tuple[int, int], float]]:
    """
    Build transport cost (USD/ton) and emission (kg CO2/ton) matrices.
    Returns (cost_matrix, emission_matrix).
    """
    cost_matrix: Dict[Tuple[int, int], float] = {}
    emission_matrix: Dict[Tuple[int, int], float] = {}

    for o in origins:
        for d in destinations:
            dist = road_distance_km(o["lat"], o["lon"], d["lat"], d["lon"])
            cost_matrix[(o["id"], d["id"])] = transport_cost_usd_per_ton(dist)
            emission_matrix[(o["id"], d["id"])] = emission_kg_co2_per_ton(dist)

    return cost_matrix, emission_matrix
