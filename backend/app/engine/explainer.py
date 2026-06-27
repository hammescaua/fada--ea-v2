"""Explicação em linguagem natural da estimativa regional.

Dois explainers intercambiáveis:
- ``TemplateExplainer``: determinístico, offline, sem dependências externas.
- ``LLMExplainer``: usa o LLM ativo (gratuito ou Anthropic) quando há chave.

Ambos recebem **apenas números já calculados pelo domínio** e os verbalizam. O LLM
não produz nem altera nenhum valor (ADR-0002). Sem provedor (ou em erro), cai no
template determinístico.
"""

from __future__ import annotations

import json
from typing import Protocol

from app.core.config import settings
from app.engine.llm_client import chat

_SYSTEM = (
    "Você é um agrônomo explicando uma estimativa de produtividade a um agricultor "
    "brasileiro. Use linguagem clara e direta. NÃO invente nem altere nenhum número "
    "— use exclusivamente os valores fornecidos no JSON. Seja conciso (até ~6 frases)."
)


class Explainer(Protocol):
    def explain(self, payload: dict) -> str: ...


class TemplateExplainer:
    """Gera explicação determinística a partir do payload estruturado."""

    def explain(self, payload: dict) -> str:
        m = payload["municipality"]
        season = payload["season"]
        pt = payload["point_sc_ha"]
        lo, hi = payload["interval_sc_ha"]
        scn = {s["name"]: s["yield_sc_ha"] for s in payload["scenarios"]}
        pw = payload["planting_window"]
        main_risk = payload["risks"][0]["description"]

        return (
            f"Para {m} na safra {season}, a produtividade esperada de soja é de "
            f"cerca de {pt:.0f} sc/ha, com intervalo provável entre {lo:.0f} e "
            f"{hi:.0f} sc/ha. Em um ano climático normal a estimativa é "
            f"{scn['normal']:.0f} sc/ha; num ano adverso (seco) pode cair para "
            f"{scn['pessimista']:.0f} sc/ha, e num ano favorável chegar a "
            f"{scn['otimista']:.0f} sc/ha. A janela de semeadura recomendada para a "
            f"região vai de {pw['start']} a {pw['end']} (ideal entre "
            f"{pw['optimal_start']} e {pw['optimal_end']}). {main_risk} "
            f"Estimativa baseada em {payload['n_years']} anos de dados históricos "
            f"(IBGE/PAM) e clima de reanálise; valores são probabilísticos, não garantias."
        )


class LLMExplainer:
    """Verbaliza via LLM ativo (gratuito/Anthropic); cai no template em erro."""

    def __init__(self) -> None:
        self._fallback = TemplateExplainer()

    def explain(self, payload: dict) -> str:
        text = chat(_SYSTEM, json.dumps(payload, ensure_ascii=False))
        return text or self._fallback.explain(payload)


def build_explainer() -> Explainer:
    if settings.llm_provider != "none":
        return LLMExplainer()
    return TemplateExplainer()
