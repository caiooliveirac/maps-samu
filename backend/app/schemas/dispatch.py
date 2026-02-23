"""
Schemas de entrada e saída da API.
Validação rigorosa — em contexto de emergência, dados malformados não passam.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


# ────────────────────────────────────────────
# Request
# ────────────────────────────────────────────

class DispatchRequest(BaseModel):
    """
    Entrada do plantonista.
    Aceita coordenadas (clique no mapa) OU endereço textual.
    Pelo menos um deve ser fornecido.
    """
    latitude: Optional[float] = Field(None, ge=-13.1, le=-12.7, description="Latitude da ocorrência")
    longitude: Optional[float] = Field(None, ge=-38.6, le=-38.2, description="Longitude da ocorrência")
    address: Optional[str] = Field(None, min_length=3, max_length=500, description="Endereço textual")

    @field_validator("address")
    @classmethod
    def sanitize_address(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 3:
                raise ValueError("Endereço muito curto")
        return v

    def has_coordinates(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    def has_address(self) -> bool:
        return self.address is not None and len(self.address.strip()) >= 3

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "latitude": -12.9714,
                    "longitude": -38.5124,
                },
                {
                    "address": "Rua da Graça, 100, Graça, Salvador"
                },
            ]
        }


class RoutePathRequest(BaseModel):
    """Entrada para cálculo de rota real no mapa."""
    origin_lat: float = Field(..., ge=-13.1, le=-12.7)
    origin_lng: float = Field(..., ge=-38.6, le=-38.2)
    dest_lat: float = Field(..., ge=-13.1, le=-12.7)
    dest_lng: float = Field(..., ge=-38.6, le=-38.2)


class RoutePathResponse(BaseModel):
    """Rota em coordenadas decodificadas para desenhar no mapa."""
    distance_km: float
    duration_minutes: float
    coordinates: list[list[float]]


# ────────────────────────────────────────────
# Response
# ────────────────────────────────────────────

class AmbulanceInfo(BaseModel):
    ambulance_id: int
    ambulance_code: str
    ambulance_type: str
    status: str


class BaseRanked(BaseModel):
    """Uma base ranqueada na resposta de despacho."""
    rank: int = Field(description="Posição no ranking (1 = mais próxima)")
    base_id: int
    base_code: str
    base_name: str
    neighborhood: str
    latitude: float
    longitude: float
    estimated_minutes: float = Field(description="Tempo estimado em minutos")
    ambulances: list[AmbulanceInfo]
    has_available: bool = Field(description="Tem ambulância disponível?")


class DispatchResponse(BaseModel):
    """Resposta completa de despacho."""
    occurrence_lat: float
    occurrence_lng: float
    resolved_address: Optional[str] = None
    time_period: str
    zone_name: Optional[str] = None
    fallback_used: bool = Field(
        False,
        description="True se usou Haversine ao invés de matriz pré-computada"
    )
    routing_mode: str = Field(
        "OSRM",
        description="OSRM | MIXED | FORMULA (fórmula fallback)"
    )
    osrm_refined_count: int = Field(0, ge=0)
    osrm_cache_count: int = Field(0, ge=0)
    fallback_formula_count: int = Field(0, ge=0)
    bases_ranked: list[BaseRanked]
    total_bases: int
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    db: str
    bases_count: int
    zones_count: int
    matrix_entries: int


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: str
