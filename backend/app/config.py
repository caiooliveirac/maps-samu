"""
Configuração centralizada via variáveis de ambiente.
Falha rápido se algo essencial estiver faltando.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://samu:samu_secure_2024@db:5432/maps_samu"

    # CORS
    cors_origins: str = "http://localhost,http://localhost:3000"

    # Geocoding
    nominatim_url: str = "https://nominatim.openstreetmap.org"

    # OSRM (routing engine)
    osrm_url: str = "http://osrm:5000"
    osrm_timeout_seconds: float = 5.0

    # App
    log_level: str = "info"
    tz: str = "America/Bahia"

    # Salvador bounding box — rejeita coordenadas fora daqui
    salvador_lat_min: float = -13.0200
    salvador_lat_max: float = -12.8000
    salvador_lng_min: float = -38.5600
    salvador_lng_max: float = -38.3000

    class Config:
        env_file = ".env"
        extra = "ignore"

    def is_inside_salvador(self, lat: float, lng: float) -> bool:
        """Validação geográfica hard — rejeita pontos fora de Salvador."""
        return (
            self.salvador_lat_min <= lat <= self.salvador_lat_max
            and self.salvador_lng_min <= lng <= self.salvador_lng_max
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
