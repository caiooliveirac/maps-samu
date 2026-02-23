"""
Script de seed — roda no startup do container.

Idempotente: verifica se dados já existem antes de inserir.
Cria tabelas, popula bases, ambulâncias, zonas e matrizes de tempo.

A matriz de tempo é calculada via OSRM (routing real pelas ruas)
com fatores de correção por faixa horária e corredor de tráfego.
Fallback: Haversine, caso OSRM não esteja disponível.
"""

import asyncio
import logging
import math
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.config import get_settings
from app.models import Base
from app.models.models import (
    BaseUnit, Ambulance, Zone, TimeMatrix,
    TimePeriod, AmbulanceType, AmbulanceStatus,
)
from app.seed.bases_data import BASES, AMBULANCES
from app.seed.zones_data import ZONES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# ────────────────────────────────────────────
# Multiplicadores por faixa horária
# Aplicados sobre o tempo OSRM (condição livre/normal)
# ────────────────────────────────────────────

PERIOD_MULTIPLIERS = {
    TimePeriod.NORMAL: 1.0,          # baseline OSRM (velocidades normais)
    TimePeriod.MORNING_RUSH: 1.85,   # trânsito pesado
    TimePeriod.EVENING_RUSH: 1.85,   # trânsito pesado
    TimePeriod.NIGHT: 0.70,          # ruas vazias, mais rápido
    TimePeriod.WEEKEND: 0.85,        # trânsito leve
}

# ────────────────────────────────────────────
# Fallback: velocidades para Haversine (caso OSRM falhe)
# ────────────────────────────────────────────

SPEED_BY_PERIOD = {
    TimePeriod.NORMAL: 35.0,
    TimePeriod.MORNING_RUSH: 18.0,
    TimePeriod.EVENING_RUSH: 18.0,
    TimePeriod.NIGHT: 50.0,
    TimePeriod.WEEKEND: 40.0,
}

ROAD_FACTOR = 1.45

# ────────────────────────────────────────────
# Corredores de engarrafamento pesado
# ────────────────────────────────────────────

HEAVY_TRAFFIC_CORRIDORS = {
    # (parent_neighborhood da base, parent_neighborhood da zona)
    # Av. Paralela
    ("Paralela", "Boca do Rio"), ("Paralela", "Cabula"), ("Paralela", "Pituba"),
    ("Boca do Rio", "Paralela"), ("Boca do Rio", "Cabula"),
    # Av. Bonocô / Vasco da Gama
    ("Centenário", "Cidade Baixa"), ("Centenário", "Centro Histórico"),
    ("San Martin", "Cidade Baixa"), ("San Martin", "Centro"),
    # Av. ACM / Tancredo Neves
    ("Cabula", "Boca do Rio"), ("Cabula", "Pituba"),
    ("Pau Miúdo", "Centenário"), ("Pau Miúdo", "Centro"),
    # BR-324
    ("Cajazeiras", "Cabula"), ("Cajazeiras", "Pau Miúdo"),
    ("Cajazeiras", "Centro"), ("Cajazeiras", "Centro Histórico"),
    # Subúrbio → Centro
    ("Periperi", "Centro"), ("Periperi", "Centro Histórico"),
    ("Periperi", "Cidade Baixa"), ("Periperi", "San Martin"),
}

CORRIDOR_RUSH_PENALTY = 1.4


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distância em km entre dois pontos (linha reta)."""
    R = 6371.0
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_travel_minutes_haversine(
    base_lat: float, base_lng: float,
    zone_lat: float, zone_lng: float,
    base_neighborhood: str,
    zone_parent: str,
    period: TimePeriod,
) -> float:
    """Fallback: Haversine × fator de correção."""
    road_km = haversine_km(base_lat, base_lng, zone_lat, zone_lng) * ROAD_FACTOR
    speed = SPEED_BY_PERIOD[period]
    is_rush = period in (TimePeriod.MORNING_RUSH, TimePeriod.EVENING_RUSH)
    if is_rush and (base_neighborhood, zone_parent) in HEAVY_TRAFFIC_CORRIDORS:
        speed /= CORRIDOR_RUSH_PENALTY
    minutes = (road_km / speed) * 60
    return round(max(minutes, 2.0), 1)


def adjust_osrm_minutes(
    osrm_minutes: float,
    base_neighborhood: str,
    zone_parent: str,
    period: TimePeriod,
) -> float:
    """
    Ajusta o tempo OSRM (free-flow) para a faixa horária.
    Aplica multiplicador de período + penalidade de corredor.
    """
    minutes = osrm_minutes * PERIOD_MULTIPLIERS[period]
    is_rush = period in (TimePeriod.MORNING_RUSH, TimePeriod.EVENING_RUSH)
    if is_rush and (base_neighborhood, zone_parent) in HEAVY_TRAFFIC_CORRIDORS:
        minutes *= CORRIDOR_RUSH_PENALTY
    return round(max(minutes, 2.0), 1)


async def fetch_osrm_matrix(base_objects, zone_objects):
    """
    Usa OSRM Table API para obter tempos reais de percurso.
    Uma única request para toda a matriz 10×74.

    Returns:
        Matriz [base_idx][zone_idx] de minutos (free-flow), ou None se falhar.
    """
    from app.services.osrm import get_table, is_healthy

    if not await is_healthy():
        logger.warning("OSRM não está respondendo")
        return None

    sources = [(b.latitude, b.longitude) for b in base_objects.values()]
    destinations = [(z.center_lat, z.center_lng) for z in zone_objects]

    logger.info(f"  Consultando OSRM Table API ({len(sources)}×{len(destinations)})...")
    matrix = await get_table(sources, destinations)

    if matrix is None:
        logger.warning("OSRM Table API falhou")
        return None

    # Verificar se temos dados válidos
    valid_cells = sum(
        1 for row in matrix for cell in row if cell is not None
    )
    total_cells = len(sources) * len(destinations)
    logger.info(f"  OSRM: {valid_cells}/{total_cells} rotas calculadas com sucesso")

    return matrix


async def run_seed():
    """Executa o seed completo."""
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tabelas criadas/verificadas")

    async with session_factory() as db:
        # ── Verificar se já tem dados ──
        count = (await db.execute(select(func.count(BaseUnit.id)))).scalar()
        if count and count > 0:
            logger.info(f"Seed já executado ({count} bases). Pulando.")
            return

        logger.info("Iniciando seed de dados...")

        # ── 1. Bases ──
        base_objects = {}
        for b in BASES:
            base = BaseUnit(**b)
            db.add(base)
            base_objects[b["code"]] = base
        await db.flush()
        logger.info(f"  {len(BASES)} bases inseridas")

        # ── 2. Ambulâncias ──
        for a in AMBULANCES:
            base = base_objects[a["base_code"]]
            amb = Ambulance(
                code=a["code"],
                ambulance_type=AmbulanceType(a["ambulance_type"]),
                base_id=base.id,
                status=AmbulanceStatus.AVAILABLE,
            )
            db.add(amb)
        await db.flush()
        logger.info(f"  {len(AMBULANCES)} ambulâncias inseridas")

        # ── 3. Zonas ──
        zone_objects = []
        for z in ZONES:
            zone = Zone(
                name=z["name"],
                parent_neighborhood=z["parent"],
                center_lat=z["lat"],
                center_lng=z["lng"],
                radius_m=float(z["radius"]),
            )
            db.add(zone)
            zone_objects.append(zone)
        await db.flush()
        logger.info(f"  {len(ZONES)} zonas inseridas")

        # ── 4. Matriz de tempo (bases × zonas × períodos) ─────
        # Tentar OSRM primeiro para tempos reais de percurso
        osrm_matrix = await fetch_osrm_matrix(base_objects, zone_objects)
        use_osrm = osrm_matrix is not None

        if use_osrm:
            logger.info("  ✓ Usando OSRM para tempos de percurso REAIS")
        else:
            logger.warning("  ✗ OSRM indisponível — usando Haversine (estimativa)")

        base_codes = list(base_objects.keys())
        matrix_count = 0

        for period in TimePeriod:
            for zone_idx, zone in enumerate(zone_objects):
                for base_idx, code in enumerate(base_codes):
                    base = base_objects[code]

                    if use_osrm:
                        osrm_mins = osrm_matrix[base_idx][zone_idx]
                        if osrm_mins is not None:
                            minutes = adjust_osrm_minutes(
                                osrm_mins,
                                base.neighborhood,
                                zone.parent_neighborhood,
                                period,
                            )
                        else:
                            # Rota impossível no OSRM → fallback Haversine
                            minutes = compute_travel_minutes_haversine(
                                base.latitude, base.longitude,
                                zone.center_lat, zone.center_lng,
                                base.neighborhood,
                                zone.parent_neighborhood,
                                period,
                            )
                    else:
                        minutes = compute_travel_minutes_haversine(
                            base.latitude, base.longitude,
                            zone.center_lat, zone.center_lng,
                            base.neighborhood,
                            zone.parent_neighborhood,
                            period,
                        )

                    entry = TimeMatrix(
                        base_id=base.id,
                        zone_id=zone.id,
                        time_period=period,
                        estimated_minutes=minutes,
                    )
                    db.add(entry)
                    matrix_count += 1

            await db.flush()

        logger.info(f"  {matrix_count} entradas na matriz de tempo")

        await db.commit()
        logger.info("Seed concluído com sucesso!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_seed())
