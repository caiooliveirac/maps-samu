"""
Script de seed — roda no startup do container.

Idempotente: verifica se dados já existem antes de inserir.
Cria tabelas, popula bases, ambulâncias, zonas e matrizes de tempo.

A matriz de tempo é calculada via Haversine com fatores de correção
por faixa horária e por corredor de tráfego de Salvador.
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
# Fatores de correção por faixa horária
# ────────────────────────────────────────────

# Velocidade média da ambulância (km/h) por faixa
SPEED_BY_PERIOD = {
    TimePeriod.NORMAL: 35.0,
    TimePeriod.MORNING_RUSH: 18.0,
    TimePeriod.EVENING_RUSH: 18.0,
    TimePeriod.NIGHT: 50.0,
    TimePeriod.WEEKEND: 40.0,
}

# Fator de correção rua vs linha reta (topografia de Salvador)
ROAD_FACTOR = 1.45

# Corredores de engarrafamento pesado: pares de zonas/bairros
# onde o trânsito é significativamente pior no rush
HEAVY_TRAFFIC_CORRIDORS = {
    # (parent_neighborhood da base, parent_neighborhood da zona)
    # Av. Paralela
    ("Brotas", "Pituba"), ("Brotas", "Imbuí"), ("Brotas", "Boca do Rio"),
    ("Pituba", "Brotas"), ("Pituba", "Cabula"),
    # Av. Bonocô
    ("Brotas", "Centro Histórico"), ("Brotas", "Itapagipe"),
    # Av. ACM
    ("Pituba", "Centro"), ("Pituba", "Liberdade"),
    # BR-324
    ("Cajazeiras", "Cabula"), ("Cajazeiras", "Liberdade"),
    ("Cajazeiras", "Centro"), ("Cajazeiras", "Centro Histórico"),
    # Subúrbio → Centro
    ("Periperi", "Centro"), ("Periperi", "Centro Histórico"),
    ("Periperi", "Brotas"), ("Periperi", "Liberdade"),
}

# Fator extra para corredores de engarrafamento durante rush
CORRIDOR_RUSH_PENALTY = 1.4


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distância em km entre dois pontos."""
    R = 6371.0
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_travel_minutes(
    base_lat: float, base_lng: float,
    zone_lat: float, zone_lng: float,
    base_neighborhood: str,
    zone_parent: str,
    period: TimePeriod,
) -> float:
    """
    Calcula tempo estimado de viagem em minutos.
    Leva em conta: distância, faixa horária, corredor de tráfego.
    """
    road_km = haversine_km(base_lat, base_lng, zone_lat, zone_lng) * ROAD_FACTOR
    speed = SPEED_BY_PERIOD[period]

    # Penalidade de corredor de engarrafamento no rush
    is_rush = period in (TimePeriod.MORNING_RUSH, TimePeriod.EVENING_RUSH)
    if is_rush and (base_neighborhood, zone_parent) in HEAVY_TRAFFIC_CORRIDORS:
        speed /= CORRIDOR_RUSH_PENALTY

    minutes = (road_km / speed) * 60

    # Mínimo de 2 minutos (tempo de acionamento + saída da base)
    return round(max(minutes, 2.0), 1)


async def run_seed():
    """Executa o seed completo."""
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        # Criar todas as tabelas
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

        # ── 4. Matrizes de tempo (bases × zonas × períodos) ──
        matrix_count = 0
        for period in TimePeriod:
            for zone in zone_objects:
                for code, base in base_objects.items():
                    minutes = compute_travel_minutes(
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

            # Flush por período para não estourar memória
            await db.flush()

        logger.info(f"  {matrix_count} entradas na matriz de tempo")

        await db.commit()
        logger.info("Seed concluído com sucesso!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_seed())
