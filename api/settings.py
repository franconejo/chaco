"""Configuración de la API (variables de entorno / `.env`)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://chaco:chaco@localhost:5432/chaco"
    cors_origins: list[str] = ["*"]
    title: str = "Chaco — motor de simulación"
    version: str = "0.1.0"


settings = Settings()
