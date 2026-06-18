"""Explicação em linguagem natural da estimativa regional.

Dois explainers intercambiáveis:
- ``TemplateExplainer``: determinístico, offline, sem dependências externas.
- ``ClaudeExplainer``: usa a API Anthropic quando há chave configurada.

Ambos recebem **apenas números já calculados pelo domínio** e os verbalizam. O LLM
não produz nem altera nenhum valor (ADR-0002).
"""

from __future__ import annotations

from typing import Protocol

from app.core.config import settings


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


class ClaudeExplainer:
    """Usa a API Anthropic (Claude) para uma explicação mais fluida.

    Só é instanciado quando há ``ANTHROPIC_API_KEY``. Importa o SDK preguiçosamente
    para não pesar no runtime padrão. Cai no template em caso de erro.
    """

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._fallback = TemplateExplainer()

    def explain(self, payload: dict) -> str:
        try:
            import anthropic  # import tardio (extra opcional [llm])

            client = anthropic.Anthropic(api_key=self._api_key)
            system = (
                "Você é um agrônomo explicando uma estimativa de produtividade a um "
                "agricultor brasileiro. Use linguagem clara e direta. NÃO invente nem "
                "altere nenhum número — use exclusivamente os valores fornecidos no JSON. "
                "Seja conciso (até ~6 frases)."
            )
            import json as _json

            msg = client.messages.create(
                model=self._model,
                max_tokens=500,
                system=system,
                messages=[{"role": "user", "content": _json.dumps(payload, ensure_ascii=False)}],
            )
            return msg.content[0].text
        except Exception:  # noqa: BLE001 — degrada para o template determinístico
            return self._fallback.explain(payload)


def build_explainer() -> Explainer:
    if settings.anthropic_api_key:
        return ClaudeExplainer(settings.anthropic_api_key, settings.llm_orchestrator_model)
    return TemplateExplainer()
