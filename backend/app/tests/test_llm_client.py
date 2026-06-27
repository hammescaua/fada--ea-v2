"""Cliente LLM: gratuito-primeiro, degradação graciosa (ADR-0029)."""

from app.core.config import settings
from app.engine.explainer import LLMExplainer, TemplateExplainer, build_explainer
from app.engine.llm_client import chat, provider, refine_narrative

_REGIONAL_PAYLOAD = {
    "municipality": "Horizontina",
    "season": "2026/27",
    "point_sc_ha": 60.0,
    "interval_sc_ha": [50.0, 70.0],
    "scenarios": [
        {"name": "normal", "yield_sc_ha": 60.0},
        {"name": "pessimista", "yield_sc_ha": 45.0},
        {"name": "otimista", "yield_sc_ha": 72.0},
    ],
    "planting_window": {
        "start": "2026-10-01", "end": "2026-12-15",
        "optimal_start": "2026-10-20", "optimal_end": "2026-11-20",
    },
    "risks": [{"description": "Risco de veranico em janeiro."}],
    "n_years": 12,
}


def test_provider_none_without_keys(monkeypatch):
    monkeypatch.setattr(settings, "free_llm_api_key", None)
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    assert provider() == "none"
    assert chat("s", "u") is None


def test_provider_prefers_free(monkeypatch):
    monkeypatch.setattr(settings, "free_llm_api_key", "free-key")
    monkeypatch.setattr(settings, "anthropic_api_key", "anthropic-key")
    assert settings.llm_provider == "free"


def test_build_explainer_falls_back_to_template(monkeypatch):
    monkeypatch.setattr(settings, "free_llm_api_key", None)
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    assert isinstance(build_explainer(), TemplateExplainer)


def test_build_explainer_uses_llm_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "free_llm_api_key", "free-key")
    assert isinstance(build_explainer(), LLMExplainer)


def test_llm_explainer_degrades_to_template_on_failure(monkeypatch):
    # Com chave mas sem rede, a chamada falha → texto determinístico (não quebra).
    monkeypatch.setattr(settings, "free_llm_api_key", "free-key")
    monkeypatch.setattr(settings, "free_llm_base_url", "http://127.0.0.1:9/v1")
    monkeypatch.setattr(settings, "llm_timeout_seconds", 0.2)
    text = LLMExplainer().explain(_REGIONAL_PAYLOAD)
    assert "Horizontina" in text and "60 sc/ha" in text


def test_refine_narrative_noop_without_llm(monkeypatch):
    monkeypatch.setattr(settings, "free_llm_api_key", None)
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    original = "Texto determinístico com 60 sc/ha."
    assert refine_narrative(original) == original
