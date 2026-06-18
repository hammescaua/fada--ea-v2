"""Decision Engine — única camada onde o LLM atua (orquestração/explicação/RAG).

No MVP, apenas a explicação em linguagem natural, com fallback determinístico
para funcionar 100% offline. O LLM nunca gera números (ADR-0002).
"""

from app.engine.explainer import Explainer, build_explainer

__all__ = ["Explainer", "build_explainer"]
