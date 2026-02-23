"""
Rotas da API.

Endpoints:
  POST /api/dispatch     → Consulta de despacho (endpoint principal)
  GET  /api/bases        → Lista todas as bases
  GET  /api/health       → Health check
"""

import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.models import BaseUnit, Zone, TimeMatrix, Ambulance
from app.schemas.dispatch import (
    DispatchRequest, DispatchResponse,
    HealthResponse, ErrorResponse, AmbulanceInfo,
    RoutePathRequest, RoutePathResponse,
)
from app.services.dispatch import dispatch
from app.services.osrm import get_route_with_geometry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["dispatch"])


# ────────────────────────────────────────────
# POST /api/dispatch — Endpoint principal
# ────────────────────────────────────────────

@router.post(
    "/dispatch",
    response_model=DispatchResponse,
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Consulta de despacho de ambulância",
    description="Recebe localização e retorna ranking de bases mais próximas",
)
async def dispatch_endpoint(
    request: DispatchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint de despacho — ZERO tolerância a falhas silenciosas.
    Sempre retorna um ranking ou um erro explícito.
    """
    # Validação: precisa de coordenadas ou endereço
    if not request.has_coordinates() and not request.has_address():
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Informe coordenadas (clique no mapa) ou endereço",
                "code": "MISSING_INPUT",
            },
        )

    result = await dispatch(request, db)

    if isinstance(result, ErrorResponse):
        raise HTTPException(
            status_code=400,
            detail=result.model_dump(),
        )

    return result


# ────────────────────────────────────────────
# GET /api/bases — Lista bases para o mapa
# ────────────────────────────────────────────

@router.get("/bases", summary="Lista todas as bases ativas")
async def list_bases(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BaseUnit)
        .where(BaseUnit.is_active == True)
        .options(selectinload(BaseUnit.ambulances))
    )
    bases = result.scalars().all()

    return [
        {
            "id": b.id,
            "code": b.code,
            "name": b.name,
            "neighborhood": b.neighborhood,
            "address": b.address,
            "latitude": b.latitude,
            "longitude": b.longitude,
            "ambulances": [
                {
                    "id": a.id,
                    "code": a.code,
                    "type": a.ambulance_type.value,
                    "status": a.status.value,
                }
                for a in b.ambulances
            ],
        }
        for b in bases
    ]


# ────────────────────────────────────────────
# GET /api/health — Health check
# ────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health(db: AsyncSession = Depends(get_db)):
    try:
        bases_count = (await db.execute(select(func.count(BaseUnit.id)))).scalar() or 0
        zones_count = (await db.execute(select(func.count(Zone.id)))).scalar() or 0
        matrix_count = (await db.execute(select(func.count(TimeMatrix.id)))).scalar() or 0

        return HealthResponse(
            status="healthy",
            db="connected",
            bases_count=bases_count,
            zones_count=zones_count,
            matrix_entries=matrix_count,
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="degraded",
            db=f"error: {str(e)[:100]}",
            bases_count=0,
            zones_count=0,
            matrix_entries=0,
        )


@router.post(
    "/route",
    response_model=RoutePathResponse,
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Rota real OSRM para visualização no mapa",
)
async def route_path_endpoint(request: RoutePathRequest):
    result = await get_route_with_geometry(
        request.origin_lat,
        request.origin_lng,
        request.dest_lat,
        request.dest_lng,
    )

    if result is None:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Não foi possível calcular rota real para este trajeto",
                "code": "NO_ROUTE",
            },
        )

    distance_km, duration_minutes, coordinates = result
    return RoutePathResponse(
        distance_km=distance_km,
        duration_minutes=duration_minutes,
        coordinates=coordinates,
    )
