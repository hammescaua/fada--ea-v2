"""Regras determinísticas de atenção (flags nomeadas e gated) + ranking multi-critério.

Limiares são constantes explícitas e auditáveis. Cada flag carrega evidência, N e
confiança. Nenhum score único (falsa precisão) — ADR-0016.
"""

from __future__ import annotations

import statistics

from app.domain.decisions.model import AttentionFlag, FieldAttention, FieldDecisionInput

# Limiares (explícitos, auditáveis).
COST_PER_HA_MEDIUM = 1.3      # × mediana da fazenda
COST_PER_HA_HIGH = 1.6
TARGET_GAP_MEDIUM = 0.15      # expectativa abaixo da meta
TARGET_GAP_HIGH = 0.25
BUDGET_OVER_HIGH = 1.15       # × orçamento planejado
BUDGET_NEAR_PCT = 90.0
REGION_BELOW_MEDIUM = -10.0   # bias vs região (%)
REGION_BELOW_HIGH = -20.0
STABILITY_UNSTABLE = 15.0     # desvio (%) dos resíduos ajustados ao clima
MIN_SEASONS_REGION = 2
MIN_SEASONS_STABILITY = 3


def _confidence(n: int) -> str:
    return "alta" if n >= 5 else "moderada" if n >= 3 else "exploratória"


def _field_flags(f: FieldDecisionInput, farm_cost_median: float | None) -> list[AttentionFlag]:
    flags: list[AttentionFlag] = []

    # 1) Custo/ha alto vs mediana da fazenda (relativo, rotulado).
    if f.actual_cost_per_ha and farm_cost_median and farm_cost_median > 0:
        ratio = f.actual_cost_per_ha / farm_cost_median
        if ratio >= COST_PER_HA_MEDIUM:
            sev = "alta" if ratio >= COST_PER_HA_HIGH else "média"
            flags.append(AttentionFlag(
                code="custo_ha_alto", severity=sev, confidence="alta",
                title="Custo por hectare elevado",
                detail=(f"Custo de R$ {f.actual_cost_per_ha:.0f}/ha — "
                        f"{round(100 * (ratio - 1))}% acima da mediana da fazenda "
                        f"(R$ {farm_cost_median:.0f}/ha)."),
                evidence={"cost_per_ha": round(f.actual_cost_per_ha, 2),
                          "farm_median": round(farm_cost_median, 2), "ratio": round(ratio, 2)},
            ))

    # 2) Expectativa abaixo da meta (estimativa regional vs target).
    if f.target_yield_sc_ha and f.expected_yield_sc_ha and f.target_yield_sc_ha > 0:
        gap = (f.target_yield_sc_ha - f.expected_yield_sc_ha) / f.target_yield_sc_ha
        if gap >= TARGET_GAP_MEDIUM:
            sev = "alta" if gap >= TARGET_GAP_HIGH else "média"
            flags.append(AttentionFlag(
                code="abaixo_da_meta", severity=sev, confidence="moderada",
                title="Distante da meta de produtividade",
                detail=(f"Expectativa de {f.expected_yield_sc_ha:.0f} sc/ha vs meta de "
                        f"{f.target_yield_sc_ha:.0f} sc/ha ({round(100 * gap)}% abaixo). "
                        "Estimativa regional tem incerteza."),
                evidence={"expected_sc_ha": round(f.expected_yield_sc_ha, 1),
                          "target_sc_ha": round(f.target_yield_sc_ha, 1),
                          "gap_pct": round(100 * gap, 1)},
            ))

    # 3) Orçamento estourado.
    if f.planned_total_cost and f.actual_total_cost and f.planned_total_cost > 0:
        ratio = f.actual_total_cost / f.planned_total_cost
        if ratio > 1.0:
            sev = "alta" if ratio >= BUDGET_OVER_HIGH else "média"
            flags.append(AttentionFlag(
                code="orcamento_estourado", severity=sev, confidence="alta",
                title="Orçamento estourado",
                detail=(f"Gasto de R$ {f.actual_total_cost:.0f} vs R$ "
                        f"{f.planned_total_cost:.0f} planejados "
                        f"({round(100 * (ratio - 1))}% acima)."),
                evidence={"actual": round(f.actual_total_cost, 2),
                          "planned": round(f.planned_total_cost, 2), "ratio": round(ratio, 2)},
            ))

    # 4) Orçamento quase esgotado com operações pendentes.
    if (f.pct_budget_consumed is not None and f.pct_budget_consumed >= BUDGET_NEAR_PCT
            and f.has_pending_planned and not f.over_budget):
        flags.append(AttentionFlag(
            code="orcamento_quase_esgotado", severity="média", confidence="alta",
            title="Orçamento quase esgotado com operações pendentes",
            detail=(f"{round(f.pct_budget_consumed)}% do orçamento consumido e ainda há "
                    "operações planejadas por executar."),
            evidence={"pct_budget_consumed": round(f.pct_budget_consumed, 1)},
        ))

    # 5) Historicamente abaixo da região (gated por N).
    if f.bias_vs_region_pct is not None and f.n_seasons >= MIN_SEASONS_REGION:
        if f.bias_vs_region_pct <= REGION_BELOW_MEDIUM:
            sev = "alta" if f.bias_vs_region_pct <= REGION_BELOW_HIGH else "média"
            flags.append(AttentionFlag(
                code="abaixo_da_regiao", severity=sev, confidence=_confidence(f.n_seasons),
                title="Historicamente abaixo da região",
                detail=(f"Em {f.n_seasons} safras, rende {abs(f.bias_vs_region_pct)}% abaixo "
                        "da expectativa regional ajustada ao clima."),
                evidence={"bias_vs_region_pct": f.bias_vs_region_pct, "n_seasons": f.n_seasons},
            ))

    # 6) Instabilidade histórica (gated por N).
    if f.stability_std_pct is not None and f.n_seasons >= MIN_SEASONS_STABILITY:
        if f.stability_std_pct >= STABILITY_UNSTABLE:
            flags.append(AttentionFlag(
                code="instavel", severity="média", confidence=_confidence(f.n_seasons),
                title="Produtividade instável",
                detail=(f"Desvio de {f.stability_std_pct}% nos resíduos ajustados ao clima "
                        f"({f.n_seasons} safras) — maior risco de variação."),
                evidence={"stability_std_pct": f.stability_std_pct, "n_seasons": f.n_seasons},
            ))

    return flags


def attention_level(flags: list[AttentionFlag]) -> str:
    if any(fl.severity == "alta" for fl in flags):
        return "alta"
    if any(fl.severity == "média" for fl in flags):
        return "média"
    return "saudável"


_LEVEL_ORDER = {"alta": 0, "média": 1, "saudável": 2}


def evaluate(fields: list[FieldDecisionInput]) -> list[FieldAttention]:
    costs = [f.actual_cost_per_ha for f in fields if f.actual_cost_per_ha]
    median = statistics.median(costs) if costs else None
    out = [
        FieldAttention(
            field_id=f.field_id, field_name=f.field_name,
            flags=(fl := _field_flags(f, median)), attention_level=attention_level(fl),
        )
        for f in fields
    ]
    out.sort(key=lambda fa: (_LEVEL_ORDER[fa.attention_level], -len(fa.flags)))
    return out


def rankings(fields: list[FieldDecisionInput]) -> dict[str, list[dict]]:
    """Ranking multi-critério: uma dimensão por vez (sem blending)."""
    def rank(key, value_fn, reverse: bool) -> list[dict]:
        items = [
            {"field_id": f.field_id, "field_name": f.field_name, "value": round(v, 2)}
            for f in fields if (v := value_fn(f)) is not None
        ]
        return sorted(items, key=lambda x: x["value"], reverse=reverse)

    def target_gap(f: FieldDecisionInput):
        if f.target_yield_sc_ha and f.expected_yield_sc_ha and f.target_yield_sc_ha > 0:
            return 100 * (f.target_yield_sc_ha - f.expected_yield_sc_ha) / f.target_yield_sc_ha
        return None

    return {
        "custo_por_hectare": rank("cost", lambda f: f.actual_cost_per_ha, reverse=True),
        "distancia_da_meta_pct": rank("gap", target_gap, reverse=True),
        "pct_orcamento_consumido": rank("pct", lambda f: f.pct_budget_consumed, reverse=True),
        "desvio_vs_regiao_pct": rank("bias", lambda f: f.bias_vs_region_pct, reverse=False),
    }
