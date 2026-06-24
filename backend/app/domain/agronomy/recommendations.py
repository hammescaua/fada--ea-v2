"""Recomendações acionáveis a partir do Perfil Agronômico — o que vale corrigir.

Transforma os fatores limitantes do perfil em **ação priorizada**: para cada fator
que o produtor *pode mudar* (manejo/correção) e que está abaixo do melhor nível,
calcula o ganho de produtividade ao corrigi-lo. Objetivo e honesto: usa os mesmos
efeitos auditáveis do perfil (ADR-0022); fatores estruturais (textura, profundidade)
ficam de fora — não adianta "recomendar" o que não dá para mudar na safra.

Puro e determinístico.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.agronomy.profile import FACTORS

# Fatores acionáveis (manejo/correção) — excluem estruturais (solo/relevo) e capital.
MANAGEABLE_FACTORS: frozenset[str] = frozenset({
    "janela_plantio", "populacao", "inoculacao", "tratamento_semente", "fungicida",
    "manejo_pragas", "manejo_daninhas", "rotacao", "plantio_direto",
    "acidez_corrigida", "fertilidade_p", "fertilidade_k", "compactacao", "cultivar",
})


@dataclass(frozen=True)
class Recommendation:
    key: str
    question: str
    current_label: str
    target_label: str
    gain_pct: float          # ganho de produtividade ao corrigir (%)
    gain_sc_ha: float        # ganho aproximado em sc/ha
    rationale: str
    confidence: str


def recommendations(
    profile: dict[str, str], personalized_point_sc_ha: float
) -> list[Recommendation]:
    """Lista priorizada (maior ganho primeiro) do que corrigir no talhão.

    Considera só fatores acionáveis cujo nível atual está abaixo do melhor
    disponível. O ganho é o efeito marginal de trocar o nível atual pelo melhor.
    """
    out: list[Recommendation] = []
    for key, value in profile.items():
        if key not in MANAGEABLE_FACTORS:
            continue
        factor = FACTORS.get(key)
        if factor is None or value not in factor.options:
            continue
        current = factor.options[value]
        best_value, best = max(factor.options.items(), key=lambda kv: kv[1].effect)
        if best.effect <= current.effect:
            continue  # já no melhor nível acionável
        # Ganho marginal multiplicativo ao trocar atual -> melhor.
        gain_frac = (1.0 + best.effect) / (1.0 + current.effect) - 1.0
        out.append(Recommendation(
            key=key,
            question=factor.question,
            current_label=current.label,
            target_label=best.label,
            gain_pct=round(gain_frac * 100, 1),
            gain_sc_ha=round(personalized_point_sc_ha * gain_frac, 1),
            rationale=factor.rationale,
            confidence=factor.confidence,
        ))
    out.sort(key=lambda r: r.gain_sc_ha, reverse=True)
    return out
