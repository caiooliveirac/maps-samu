"""
Cálculos de distância geoespacial.
Haversine é o fallback quando a zona não é encontrada na matriz.
"""

import math
from typing import Tuple


# Raio da Terra em km
EARTH_RADIUS_KM = 6371.0

# Velocidade média de ambulância em Salvador (km/h)
# Conservadora para não subestimar tempo
AVG_SPEED_NORMAL_KMH = 35.0
AVG_SPEED_RUSH_KMH = 18.0
AVG_SPEED_NIGHT_KMH = 50.0
AVG_SPEED_WEEKEND_KMH = 40.0

# Fator de correção rua vs linha reta (Manhattan factor)
# Salvador tem topografia irregular — fator alto
ROAD_FACTOR = 1.45


def haversine_km(
    lat1: float, lng1: float,
    lat2: float, lng2: float,
) -> float:
    """
    Distância em km entre dois pontos usando fórmula de Haversine.
    Retorna distância em linha reta.
    """
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def estimate_road_distance_km(
    lat1: float, lng1: float,
    lat2: float, lng2: float,
) -> float:
    """Distância estimada por estrada (Haversine × fator de correção)."""
    return haversine_km(lat1, lng1, lat2, lng2) * ROAD_FACTOR


def estimate_minutes(
    lat1: float, lng1: float,
    lat2: float, lng2: float,
    time_period: str,
) -> float:
    """
    Tempo estimado em minutos via Haversine + velocidade média.
    Usado como FALLBACK quando zona não encontrada na matriz.
    """
    road_km = estimate_road_distance_km(lat1, lng1, lat2, lng2)

    speed_map = {
        "NORMAL": AVG_SPEED_NORMAL_KMH,
        "MORNING_RUSH": AVG_SPEED_RUSH_KMH,
        "EVENING_RUSH": AVG_SPEED_RUSH_KMH,
        "NIGHT": AVG_SPEED_NIGHT_KMH,
        "WEEKEND": AVG_SPEED_WEEKEND_KMH,
    }
    speed = speed_map.get(time_period, AVG_SPEED_NORMAL_KMH)

    minutes = (road_km / speed) * 60
    return round(minutes, 1)


def find_nearest_zone(
    lat: float, lng: float,
    zones: list[Tuple[int, float, float, float]],
) -> int | None:
    """
    Encontra a zona mais próxima do ponto dado.
    zones: lista de (zone_id, center_lat, center_lng, radius_m)
    Retorna zone_id ou None se nenhuma zona estiver a menos de 2km.
    """
    best_id = None
    best_dist = float("inf")

    for zone_id, z_lat, z_lng, radius_m in zones:
        dist = haversine_km(lat, lng, z_lat, z_lng) * 1000  # para metros
        if dist < best_dist:
            best_dist = dist
            best_id = zone_id

    # Se o ponto mais próximo está a mais de 2km de qualquer zona, retorna None
    if best_dist > 2000:
        return None

    return best_id
