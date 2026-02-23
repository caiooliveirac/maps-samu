"""
Cliente OSRM — calcula rotas reais pelas ruas de Salvador.

Usa a instância local do OSRM (Open Source Routing Machine)
para obter distâncias e tempos de percurso reais.
"""

import logging
from typing import Optional, Tuple

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Timeout configurável para consultas de rota/matriz no OSRM
TIMEOUT = httpx.Timeout(
    settings.osrm_timeout_seconds,
    connect=min(settings.osrm_timeout_seconds, 3.0),
)


async def get_route(
    lat1: float, lng1: float,
    lat2: float, lng2: float,
) -> Optional[Tuple[float, float]]:
    """
    Consulta OSRM para rota entre dois pontos.

    Returns:
        (distance_km, duration_minutes) ou None se falhar.
    """
    # OSRM usa formato lng,lat (invertido)
    url = (
        f"{settings.osrm_url}/route/v1/driving/"
        f"{lng1},{lat1};{lng2},{lat2}"
        f"?overview=false&alternatives=false"
    )

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()

        data = response.json()

        if data.get("code") != "Ok":
            logger.warning(f"OSRM route returned code={data.get('code')}")
            return None

        routes = data.get("routes")
        if not routes or not isinstance(routes, list):
            logger.warning("OSRM route payload missing routes list")
            return None

        route = routes[0]
        if not isinstance(route, dict):
            logger.warning("OSRM route payload has invalid first route entry")
            return None

        distance = route.get("distance")
        duration = route.get("duration")
        if distance is None or duration is None:
            logger.warning("OSRM route payload missing distance/duration")
            return None

        distance_km = float(distance) / 1000.0
        duration_min = float(duration) / 60.0

        return (distance_km, duration_min)

    except Exception as e:
        logger.warning(f"OSRM route query failed: {e}")
        return None


async def get_route_with_geometry(
    lat1: float, lng1: float,
    lat2: float, lng2: float,
) -> Optional[Tuple[float, float, list[list[float]]]]:
    """
    Consulta OSRM e retorna distância, duração e geometria da rota.

    Returns:
        (distance_km, duration_minutes, [[lat, lng], ...]) ou None se falhar.
    """
    url = (
        f"{settings.osrm_url}/route/v1/driving/"
        f"{lng1},{lat1};{lng2},{lat2}"
        f"?overview=full&geometries=geojson&alternatives=false"
    )

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()

        data = response.json()

        if data.get("code") != "Ok":
            logger.warning(f"OSRM route geometry returned code={data.get('code')}")
            return None

        routes = data.get("routes")
        if not routes or not isinstance(routes, list):
            logger.warning("OSRM geometry payload missing routes list")
            return None

        route = routes[0]
        if not isinstance(route, dict):
            logger.warning("OSRM geometry payload has invalid first route entry")
            return None

        distance = route.get("distance")
        duration = route.get("duration")
        geometry = route.get("geometry") or {}
        coordinates = geometry.get("coordinates")

        if distance is None or duration is None or not coordinates:
            logger.warning("OSRM geometry payload missing distance/duration/coordinates")
            return None

        lat_lng_coords = []
        for coord in coordinates:
            if not isinstance(coord, list) or len(coord) < 2:
                continue
            lng, lat = coord[0], coord[1]
            lat_lng_coords.append([float(lat), float(lng)])

        if len(lat_lng_coords) < 2:
            logger.warning("OSRM geometry returned insufficient coordinates")
            return None

        distance_km = float(distance) / 1000.0
        duration_min = float(duration) / 60.0

        return (distance_km, duration_min, lat_lng_coords)

    except Exception as e:
        logger.warning(f"OSRM route geometry query failed: {e}")
        return None


async def get_table(
    sources: list[Tuple[float, float]],
    destinations: list[Tuple[float, float]],
) -> Optional[list[list[Optional[float]]]]:
    """
    Consulta OSRM Table API para matriz N×M de tempos.

    Args:
        sources: lista de (lat, lng) — origens (bases)
        destinations: lista de (lat, lng) — destinos (zonas)

    Returns:
        Matriz de durações em MINUTOS, ou None se falhar.
        Células individuais podem ser None (rota impossível).
    """
    # Montar string de coordenadas (lng,lat)
    all_coords = sources + destinations
    coords_str = ";".join(f"{lng},{lat}" for lat, lng in all_coords)

    src_indices = ";".join(str(i) for i in range(len(sources)))
    dst_indices = ";".join(
        str(i) for i in range(len(sources), len(all_coords))
    )

    url = (
        f"{settings.osrm_url}/table/v1/driving/{coords_str}"
        f"?sources={src_indices}&destinations={dst_indices}"
    )

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()

        data = response.json()

        if data.get("code") != "Ok":
            logger.warning(f"OSRM table returned: {data.get('code')}")
            return None

        # Converter segundos → minutos
        durations = [
            [
                (cell / 60.0 if cell is not None else None)
                for cell in row
            ]
            for row in data["durations"]
        ]

        return durations

    except Exception as e:
        logger.warning(f"OSRM table query failed: {e}")
        return None


async def is_healthy() -> bool:
    """Verifica se o OSRM está rodando e respondendo."""
    url = (
        f"{settings.osrm_url}/route/v1/driving/"
        f"-38.5124,-12.9714;-38.51,-12.97"
        f"?overview=false"
    )
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(3.0)) as client:
            response = await client.get(url)
            return response.status_code == 200
    except Exception:
        return False
