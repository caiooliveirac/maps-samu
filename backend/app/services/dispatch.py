"""
Serviço de Despacho — o cérebro do MAPS-SAMU.

Fluxo:
1. Recebe coordenadas (ou geocodifica endereço)
2. Valida que está dentro de Salvador
3. Encontra a zona mais próxima
4. Consulta a matriz de tempo para a faixa horária atual
5. Se zona não encontrada → fallback Haversine
6. Retorna ranking de bases ordenado por tempo estimado
7. Loga ocorrência para auditoria

PRINCÍPIO: Nunca retornar erro vazio. Sempre retornar um ranking,
mesmo que impreciso (Haversine), para o plantonista decidir.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    BaseUnit, Ambulance, Zone, TimeMatrix, Occurrence,
    TimePeriod, AmbulanceStatus,
)
from app.schemas.dispatch import (
    DispatchRequest, DispatchResponse,
    BaseRanked, AmbulanceInfo, ErrorResponse,
)
from app.services.distance import (
    find_nearest_zone, estimate_minutes,
)
from app.services.geocoding import geocode_address
from app.services.time_period import get_current_time_period
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

BRT = timezone(timedelta(hours=-3))


async def dispatch(
    request: DispatchRequest,
    db: AsyncSession,
) -> DispatchResponse | ErrorResponse:
    """
    Pipeline principal de despacho.
    Garantia: SEMPRE retorna um ranking ou um erro claro.
    """

    # ── 1. Resolver coordenadas ──────────────────────────
    lat: Optional[float] = request.latitude
    lng: Optional[float] = request.longitude
    resolved_address: Optional[str] = None

    if not request.has_coordinates():
        if not request.has_address():
            return ErrorResponse(
                error="Coordenadas ou endereço são obrigatórios",
                code="MISSING_INPUT",
            )

        result = await geocode_address(request.address)
        if result is None:
            return ErrorResponse(
                error=f"Não foi possível localizar o endereço: {request.address}",
                detail="Tente clicar diretamente no mapa",
                code="GEOCODING_FAILED",
            )
        lat, lng, resolved_address = result
    else:
        resolved_address = request.address

    # ── 2. Validar que está em Salvador ──────────────────
    if not settings.is_inside_salvador(lat, lng):
        return ErrorResponse(
            error="Localização fora da área de cobertura de Salvador",
            detail=f"Coordenadas ({lat}, {lng}) fora do perímetro",
            code="OUT_OF_BOUNDS",
        )

    # ── 3. Faixa horária atual ───────────────────────────
    time_period_str = get_current_time_period()
    time_period = TimePeriod(time_period_str)

    # ── 4. Buscar todas as zonas para encontrar a mais próxima ─
    zones_result = await db.execute(
        select(Zone.id, Zone.center_lat, Zone.center_lng, Zone.radius_m, Zone.name)
    )
    zones_rows = zones_result.all()

    zone_id = None
    zone_name = None
    fallback_used = False

    if zones_rows:
        zones_tuples = [(z.id, z.center_lat, z.center_lng, z.radius_m) for z in zones_rows]
        zone_id = find_nearest_zone(lat, lng, zones_tuples)
        if zone_id:
            zone_name = next(
                (z.name for z in zones_rows if z.id == zone_id), None
            )

    # ── 5. Buscar bases com ambulâncias ──────────────────
    bases_result = await db.execute(
        select(BaseUnit)
        .where(BaseUnit.is_active == True)
        .options(selectinload(BaseUnit.ambulances))
    )
    bases = bases_result.scalars().all()

    if not bases:
        return ErrorResponse(
            error="Nenhuma base ativa encontrada no sistema",
            code="NO_BASES",
        )

    # ── 6. Calcular ranking ──────────────────────────────
    ranked: list[dict] = []

    if zone_id:
        # Caminho feliz: usa matriz pré-computada
        matrix_result = await db.execute(
            select(TimeMatrix)
            .where(
                TimeMatrix.zone_id == zone_id,
                TimeMatrix.time_period == time_period,
            )
            .order_by(TimeMatrix.estimated_minutes.asc())
        )
        matrix_rows = matrix_result.scalars().all()

        if matrix_rows:
            # Monta ranking a partir da matriz
            base_map = {b.id: b for b in bases}
            for entry in matrix_rows:
                base = base_map.get(entry.base_id)
                if base and base.is_active:
                    ranked.append({
                        "base": base,
                        "minutes": entry.estimated_minutes,
                    })
        else:
            fallback_used = True
    else:
        fallback_used = True

    # ── 7. Fallback: Haversine ───────────────────────────
    if fallback_used or not ranked:
        logger.warning(
            f"Usando fallback Haversine para ({lat}, {lng}), "
            f"zone_id={zone_id}, period={time_period_str}"
        )
        fallback_used = True
        ranked = []
        for base in bases:
            minutes = estimate_minutes(
                lat, lng,
                base.latitude, base.longitude,
                time_period_str,
            )
            ranked.append({"base": base, "minutes": minutes})

    # Ordenar por tempo
    ranked.sort(key=lambda x: x["minutes"])

    # ── 8. Montar resposta ───────────────────────────────
    bases_ranked = []
    for i, item in enumerate(ranked, 1):
        base = item["base"]
        ambulances = [
            AmbulanceInfo(
                ambulance_id=amb.id,
                ambulance_code=amb.code,
                ambulance_type=amb.ambulance_type.value,
                status=amb.status.value,
            )
            for amb in base.ambulances
        ]
        has_available = any(
            amb.status == AmbulanceStatus.AVAILABLE
            for amb in base.ambulances
        )
        bases_ranked.append(BaseRanked(
            rank=i,
            base_id=base.id,
            base_code=base.code,
            base_name=base.name,
            neighborhood=base.neighborhood,
            latitude=base.latitude,
            longitude=base.longitude,
            estimated_minutes=item["minutes"],
            ambulances=ambulances,
            has_available=has_available,
        ))

    # ── 9. Log da ocorrência (async, não bloqueia resposta) ──
    try:
        occurrence = Occurrence(
            latitude=lat,
            longitude=lng,
            address_input=request.address or resolved_address,
            zone_id=zone_id,
            time_period_used=time_period,
            recommended_base_id=ranked[0]["base"].id if ranked else bases[0].id,
            fallback_used=fallback_used,
        )
        db.add(occurrence)
        await db.commit()
    except Exception as e:
        logger.error(f"Falha ao salvar ocorrência: {e}")
        # NÃO falha o request por causa de log

    return DispatchResponse(
        occurrence_lat=lat,
        occurrence_lng=lng,
        resolved_address=resolved_address,
        time_period=time_period_str,
        zone_name=zone_name,
        fallback_used=fallback_used,
        bases_ranked=bases_ranked,
        total_bases=len(bases_ranked),
        timestamp=datetime.now(BRT).isoformat(),
    )
