"""Punto de entrada de la API."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.db import engine
from api.models import Base
from api.routers import games
from api.settings import settings
from data import map as map_catalog


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fase 0: creación directa de tablas. La Fase 1 migra a Alembic.
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


app = FastAPI(title=settings.title, version=settings.version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "version": settings.version}


@app.get("/map", tags=["meta"])
def read_map() -> dict:
    return {
        "nodes": [
            {
                "id": n.id,
                "label": n.label,
                "x": n.x,
                "y": n.y,
                "zone": n.zone,
                "public": n.public,
            }
            for n in map_catalog.NODES
        ],
        "edges": [{"a": e.a, "b": e.b} for e in map_catalog.EDGES],
        "zones": map_catalog.ZONE_LABELS,
        "zone_colors": map_catalog.ZONE_COLORS,
    }


# i18n (Fase 5): archivos de traducción.
_I18N_DIR = Path(__file__).resolve().parents[1] / "i18n"
if _I18N_DIR.exists():
    app.mount("/i18n", StaticFiles(directory=str(_I18N_DIR)), name="i18n")

# Cliente web (Fase 2): se sirve desde el mismo origen para evitar CORS.
_WEB_DIR = Path(__file__).resolve().parents[1] / "web"
if _WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_WEB_DIR), html=True), name="web")
