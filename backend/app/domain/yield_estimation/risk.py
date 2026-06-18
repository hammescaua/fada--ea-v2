"""Riscos climáticos derivados da climatologia e dos cenários.

Cada risco é quantificado em termos do impacto na produtividade (sc/ha e %),
ancorado em dados históricos do município — não em afirmações genéricas.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.yield_estimation.predictor import YieldEstimate


@dataclass(frozen=True)
class ClimaticRisk:
    factor: str
    severity: str  # baixo | moderado | alto
    description: str
    metric: dict[str, float]


def _severity(pct_drop: float) -> str:
    if pct_drop >= 25:
        return "alto"
    if pct_drop >= 10:
        return "moderado"
    return "baixo"


def assess_climatic_risks(estimate: YieldEstimate) -> list[ClimaticRisk]:
    normal = next(s for s in estimate.scenarios if s.name == "normal")
    pessimist = next(s for s in estimate.scenarios if s.name == "pessimista")
    feats = estimate.climatology["features"]

    drop_sc = round(normal.yield_sc_ha - pessimist.yield_sc_ha, 1)
    drop_pct = round(100 * drop_sc / normal.yield_sc_ha, 1) if normal.yield_sc_ha else 0.0

    deficit = feats["water_deficit_reproductive_mm"]
    dry = feats["dry_spell_longest_reproductive_days"]
    hot = feats["hot_days_reproductive"]

    risks = [
        ClimaticRisk(
            factor="deficit_hidrico_reprodutivo",
            severity=_severity(drop_pct),
            description=(
                "Déficit hídrico no período reprodutivo (enchimento de grãos) é o "
                f"principal risco. Em anos adversos (~1 a cada 10) o déficit chega a "
                f"{round(deficit['p90'])} mm (mediana {round(deficit['p50'])} mm), "
                f"reduzindo a produtividade em ~{drop_sc} sc/ha ({drop_pct}%)."
            ),
            metric={
                "deficit_mediano_mm": round(deficit["p50"], 1),
                "deficit_adverso_mm": round(deficit["p90"], 1),
                "perda_potencial_sc_ha": drop_sc,
                "perda_potencial_pct": drop_pct,
            },
        ),
        ClimaticRisk(
            factor="veranico_reprodutivo",
            severity="moderado" if dry["p90"] >= 10 else "baixo",
            description=(
                f"Veranicos: em anos secos a maior sequência sem chuva no reprodutivo "
                f"atinge {round(dry['p90'])} dias (mediana {round(dry['p50'])} dias)."
            ),
            metric={"veranico_mediano_dias": round(dry["p50"], 1),
                    "veranico_adverso_dias": round(dry["p90"], 1)},
        ),
        ClimaticRisk(
            factor="estresse_termico",
            severity="moderado" if hot["p90"] >= 15 else "baixo",
            description=(
                f"Estresse térmico: em anos quentes há até {round(hot['p90'])} dias "
                f">35 °C no reprodutivo (mediana {round(hot['p50'])} dias)."
            ),
            metric={"dias_quentes_medianos": round(hot["p50"], 1),
                    "dias_quentes_adversos": round(hot["p90"], 1)},
        ),
    ]
    return risks
