"""
Async database engine e session factory.
Pool configurado para respostas rápidas.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=20,          # Conexões mantidas abertas
    max_overflow=10,       # Burst para picos de demanda
    pool_timeout=5,        # Falha rápido se pool cheio
    pool_recycle=300,      # Recicla a cada 5min
    pool_pre_ping=True,    # Verifica conexão antes de usar
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Dependency injection para rotas FastAPI."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
