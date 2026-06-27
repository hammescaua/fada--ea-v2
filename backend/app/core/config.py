"""Configuração da aplicação (12-factor: lida de variáveis de ambiente)."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Raiz do repositório (.../fada--ea-v1), dois níveis acima deste arquivo.
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FADA_", env_file=".env", extra="ignore")

    app_name: str = "FADA — Farm AI Decision Agent"
    environment: str = "development"

    # Camadas de dados (DVC): raw -> intermediate -> features -> models
    data_dir: Path = PROJECT_ROOT / "data"
    model_path: Path = PROJECT_ROOT / "data" / "models" / "soybean_regional_baseline.json"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "raw" / "cache"

    # Persistência. SQLite por padrão (rodável out-of-the-box); Postgres em produção
    # via FADA_DATABASE_URL. Ver ADR-0009.
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'data' / 'fada.db'}"
    redis_url: str = "redis://localhost:6379/0"

    # CORS — origens permitidas (CSV em FADA_CORS_ORIGINS; "*" libera todas em dev).
    cors_origins: str = "*"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # LLM (Decision Engine — orquestração/explicação/RAG). Ver ADR-0002 e ADR-0029.
    # O LLM só verbaliza/explica números já calculados pelo domínio; nunca os gera.
    # Opção 1 (gratuita, recomendada): endpoint OpenAI-compatible de provedor com free
    # tier (ex.: Groq). Basta uma chave grátis em FADA_FREE_LLM_API_KEY.
    free_llm_api_key: str | None = None
    free_llm_base_url: str = "https://api.groq.com/openai/v1"
    free_llm_model: str = "llama-3.3-70b-versatile"
    # Opção 2 (paga): Anthropic.
    anthropic_api_key: str | None = None
    llm_orchestrator_model: str = "claude-opus-4-8"
    llm_cheap_model: str = "claude-haiku-4-5-20251001"
    # Timeout duro de qualquer chamada LLM (degrada para determinístico ao estourar).
    llm_timeout_seconds: float = 12.0

    @property
    def llm_provider(self) -> str:
        """Provedor LLM ativo: gratuito > pago > nenhum (determinístico)."""
        if self.free_llm_api_key:
            return "free"
        if self.anthropic_api_key:
            return "anthropic"
        return "none"


settings = Settings()
