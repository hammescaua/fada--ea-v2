"""Configuração da aplicação (12-factor: lida de variáveis de ambiente)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FADA_", env_file=".env", extra="ignore")

    app_name: str = "FADA — Farm AI Decision Agent"
    environment: str = "development"

    # Persistência (usado a partir da V1)
    database_url: str = "postgresql+psycopg://fada:fada@localhost:5432/fada"
    redis_url: str = "redis://localhost:6379/0"

    # LLM (Decision Engine — orquestração/explicação/RAG). Ver ADR-0002.
    anthropic_api_key: str | None = None
    llm_orchestrator_model: str = "claude-opus-4-8"
    llm_cheap_model: str = "claude-haiku-4-5-20251001"


settings = Settings()
