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

# Timeout curto para evitar travamento da aplicação quando OSRM está lento/offline
TIMEOUT = httpx.Timeout(2.0, connect=2.0)


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

        if data.get("code") != "Ok" or not data.get("routes"):
            logger.warning(f"OSRM returned non-Ok: {data.get('code')}")
            return None

        route = data["routes"][0]
        distance_km = route["distance"] / 1000.0
        duration_min = route["duration"] / 60.0

        return (distance_km, duration_min)

    except Exception as e:
        logger.warning(f"OSRM route query failed: {e}")
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
