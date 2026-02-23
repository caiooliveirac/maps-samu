"""
Geocoding service — converte endereço textual em coordenadas.

Estratégia:
1. Nominatim (OpenStreetMap) como fonte primária
2. Timeout agressivo (3s) — se falhar, o plantonista pode clicar no mapa
3. Restrição a Salvador-BA para evitar resultados errados

Em produção, considerar hospedar Nominatim localmente para
eliminar dependência externa.
"""

import logging
from typing import Optional, Tuple

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Bounding box de Salvador para restringir resultados
SALVADOR_VIEWBOX = "-38.56,-13.02,-38.30,-12.80"


async def geocode_address(address: str) -> Optional[Tuple[float, float, str]]:
    """
    Geocodifica endereço para (lat, lng, display_name).
    Retorna None se não encontrar.

    Timeout de 3 segundos — em emergência, rapidez > perfeição.
    Se o geocoding falhar, o plantonista clica direto no mapa.
    """
    # Adiciona "Salvador, Bahia" se não estiver no endereço
    search_query = address
    if "salvador" not in address.lower():
        search_query = f"{address}, Salvador, Bahia, Brasil"

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(
                f"{settings.nominatim_url}/search",
                params={
                    "q": search_query,
                    "format": "json",
                    "limit": 1,
                    "viewbox": SALVADOR_VIEWBOX,
                    "bounded": 1,
                    "addressdetails": 1,
                    "countrycodes": "br",
                },
                headers={
                    "User-Agent": "SAMU-Salvador-Dispatch/1.0",
                },
            )
            response.raise_for_status()
            results = response.json()

        if not results:
            logger.warning(f"Geocoding: nenhum resultado para '{address}'")
            return None

        hit = results[0]
        lat = float(hit["lat"])
        lng = float(hit["lon"])
        display = hit.get("display_name", address)

        # Validação: está dentro de Salvador?
        if not settings.is_inside_salvador(lat, lng):
            logger.warning(
                f"Geocoding: resultado fora de Salvador ({lat}, {lng}) para '{address}'"
            )
            return None

        logger.info(f"Geocoding OK: '{address}' → ({lat}, {lng})")
        return (lat, lng, display)

    except httpx.TimeoutException:
        logger.error(f"Geocoding timeout (3s) para '{address}'")
        return None
    except Exception as e:
        logger.error(f"Geocoding error para '{address}': {e}")
        return None
