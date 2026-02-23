"""
MAPS-SAMU — Sistema de Despacho Georreferenciado
SAMU Salvador, Bahia

Entry point do backend FastAPI.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.config import get_settings
from app.api.router import router

settings = get_settings()

# Logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="MAPS-SAMU Salvador",
    description="Sistema de despacho georreferenciado de ambulâncias",
    version="1.0.0",
    default_response_class=ORJSONResponse,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(router)


@app.on_event("startup")
async def startup():
    logging.getLogger(__name__).info("MAPS-SAMU backend started")
