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

from app.domain.agronomy.cost_profile import COST_FACTOR_EFFECTS
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


@dataclass(frozen=True)
class EconomicRecommendation:
    key: str
    question: str
    current_label: str
    target_label: str
    gain_sc_ha: float            # ganho de produtividade ao corrigir
    yield_gain_rs_ha: float      # esse ganho convertido a R$ (preço observado)
    cost_change_rs_ha: float     # variação de custo ao adotar a prática (R$/ha)
    net_gain_rs_ha: float        # ganho líquido = produtividade - custo
    rationale: str
    confidence: str


def economic_recommendations(
    profile: dict[str, str],
    personalized_point_sc_ha: float,
    price_per_bag: float,
    reference_cost_per_ha: float,
) -> list[EconomicRecommendation]:
    """Recomendações na linguagem do produtor: ganho LÍQUIDO em R$/ha.

    Para cada fator acionável abaixo do melhor nível, soma o ganho de produtividade
    (× preço) e subtrai a variação de custo de adotar a prática (matriz de custo,
    ADR-0022). Ordena pelo líquido — a métrica de decisão. Determinístico.
    """
    out: list[EconomicRecommendation] = []
    for key, value in profile.items():
        if key not in MANAGEABLE_FACTORS:
            continue
        factor = FACTORS.get(key)
        if factor is None or value not in factor.options:
            continue
        current = factor.options[value]
        best_value, best = max(factor.options.items(), key=lambda kv: kv[1].effect)
        if best.effect <= current.effect:
            continue
        gain_frac = (1.0 + best.effect) / (1.0 + current.effect) - 1.0
        gain_sc = personalized_point_sc_ha * gain_frac
        yield_gain_rs = gain_sc * price_per_bag

        cost_eff = COST_FACTOR_EFFECTS.get(key, {})
        cost_cur = cost_eff.get(value, (0.0, ""))[0]
        cost_best = cost_eff.get(best_value, (0.0, ""))[0]
        cost_change_frac = (1.0 + cost_best) / (1.0 + cost_cur) - 1.0
        cost_change_rs = cost_change_frac * reference_cost_per_ha

        out.append(EconomicRecommendation(
            key=key,
            question=factor.question,
            current_label=current.label,
            target_label=best.label,
            gain_sc_ha=round(gain_sc, 1),
            yield_gain_rs_ha=round(yield_gain_rs, 2),
            cost_change_rs_ha=round(cost_change_rs, 2),
            net_gain_rs_ha=round(yield_gain_rs - cost_change_rs, 2),
            rationale=factor.rationale,
            confidence=factor.confidence,
        ))
    out.sort(key=lambda r: r.net_gain_rs_ha, reverse=True)
    return out
