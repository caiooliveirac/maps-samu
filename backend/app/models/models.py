"""
Modelos do domínio SAMU Salvador.

Hierarquia:
  Base (10) → Ambulância (12)
  Zona (~60 bairros/sub-bairros) → MatrizTempo (base × zona × faixa_horária)

A MatrizTempo é a tabela mais consultada — otimizada com índice composto.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    ForeignKey, Enum, DateTime, Index, Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.models import Base


# ────────────────────────────────────────────
# Enums
# ────────────────────────────────────────────

class TimePeriod(str, enum.Enum):
    """Faixas horárias para matrizes de tempo."""
    NORMAL = "NORMAL"               # 10h-16h dias úteis
    MORNING_RUSH = "MORNING_RUSH"   # 06h-09h dias úteis
    EVENING_RUSH = "EVENING_RUSH"   # 17h-20h dias úteis
    NIGHT = "NIGHT"                 # 21h-05h
    WEEKEND = "WEEKEND"             # Sábado e Domingo inteiro


class AmbulanceType(str, enum.Enum):
    """Tipo de ambulância SAMU."""
    USB = "USB"   # Unidade de Suporte Básico
    USA = "USA"   # Unidade de Suporte Avançado


class AmbulanceStatus(str, enum.Enum):
    """Status operacional."""
    AVAILABLE = "AVAILABLE"
    DISPATCHED = "DISPATCHED"
    MAINTENANCE = "MAINTENANCE"


# ────────────────────────────────────────────
# Base de Ambulância
# ────────────────────────────────────────────

class BaseUnit(Base):
    """Uma das 10 bases do SAMU em Salvador."""
    __tablename__ = "bases"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)      # ex: "BASE-01"
    name = Column(String(100), nullable=False)                   # ex: "Base Brotas"
    address = Column(Text, nullable=False)
    neighborhood = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    ambulances = relationship("Ambulance", back_populates="base", lazy="selectin")

    def __repr__(self):
        return f"<Base {self.code}: {self.name}>"


# ────────────────────────────────────────────
# Ambulância
# ────────────────────────────────────────────

class Ambulance(Base):
    """Uma das 12 ambulâncias."""
    __tablename__ = "ambulances"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)       # ex: "AMB-01"
    ambulance_type = Column(Enum(AmbulanceType), nullable=False)
    base_id = Column(Integer, ForeignKey("bases.id"), nullable=False)
    status = Column(
        Enum(AmbulanceStatus),
        default=AmbulanceStatus.AVAILABLE,
        nullable=False,
    )

    base = relationship("BaseUnit", back_populates="ambulances")

    def __repr__(self):
        return f"<Ambulance {self.code} @ Base {self.base_id}>"


# ────────────────────────────────────────────
# Zona (bairro / sub-bairro)
# ────────────────────────────────────────────

class Zone(Base):
    """
    Zona geográfica de Salvador.
    Bairros grandes são divididos em sub-zonas.
    O center_lat/center_lng é o ponto de referência para lookup.
    """
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)                   # ex: "Cajazeiras VIII"
    parent_neighborhood = Column(String(100), nullable=False)    # ex: "Cajazeiras"
    center_lat = Column(Float, nullable=False)
    center_lng = Column(Float, nullable=False)
    # Raio aproximado da zona em metros (para matching por proximidade)
    radius_m = Column(Float, default=500.0, nullable=False)

    def __repr__(self):
        return f"<Zone {self.name}>"


# ────────────────────────────────────────────
# Matriz de Tempo
# ────────────────────────────────────────────

class TimeMatrix(Base):
    """
    Tempo estimado em MINUTOS de uma base até uma zona,
    para uma determinada faixa horária.

    Esta é a tabela mais quente do sistema.
    Query principal: WHERE zone_id = ? AND time_period = ? ORDER BY estimated_minutes
    """
    __tablename__ = "time_matrices"
    __table_args__ = (
        UniqueConstraint("base_id", "zone_id", "time_period", name="uq_matrix_entry"),
        Index("ix_matrix_lookup", "zone_id", "time_period", "estimated_minutes"),
    )

    id = Column(Integer, primary_key=True)
    base_id = Column(Integer, ForeignKey("bases.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    time_period = Column(Enum(TimePeriod), nullable=False)
    estimated_minutes = Column(Float, nullable=False)

    base = relationship("BaseUnit", lazy="joined")
    zone = relationship("Zone", lazy="joined")


# ────────────────────────────────────────────
# Ocorrência (log de despachos)
# ────────────────────────────────────────────

class Occurrence(Base):
    """Log de cada consulta de despacho para auditoria e melhoria contínua."""
    __tablename__ = "occurrences"

    id = Column(Integer, primary_key=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address_input = Column(Text)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=True)
    time_period_used = Column(Enum(TimePeriod), nullable=False)
    recommended_base_id = Column(Integer, ForeignKey("bases.id"), nullable=False)
    fallback_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
