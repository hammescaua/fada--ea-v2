"""Insight Engine determinístico (regras + estatística, com evidence gating).

Cada insight declara N (safras) e tamanho de efeito; nada é emitido sem suporte
mínimo. Sem LLM, sem inferência fraca (ADR-0014).
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from app.domain.insights.summary import FieldSeasonRecord, FieldSummary, yield_anomaly_zscore

# Limiares de evidência (ajustáveis).
MIN_SEASONS_RANK = 2       # comparar talhões exige >= 2 safras por talhão
MIN_SEASONS_STABILITY = 3  # estabilidade exige >= 3 safras
MIN_SEASONS_TREND = 3
MIN_SEASONS_ANOMALY = 4
STABILITY_GAP = 1.3        # "menos estável" precisa de 1.3x o desvio do "mais estável"
ANOMALY_Z = 2.0


@dataclass(frozen=True)
class Insight:
    type: str
    scope: str                 # "farm" | "field"
    title: str
    detail: str
    evidence: dict
    confidence: str            # "alta" | "moderada" | "exploratória"
    field_id: int | None = None


def _confidence(n: int) -> str:
    return "alta" if n >= 5 else "moderada" if n >= 3 else "exploratória"


def _eligible(summaries: list[FieldSummary], min_seasons: int) -> list[FieldSummary]:
    return [s for s in summaries if s.n_seasons >= min_seasons]


def performance_ranking(summaries: list[FieldSummary]) -> list[Insight]:
    elig = _eligible(summaries, MIN_SEASONS_RANK)
    if len(elig) < 2:
        return []
    farm_mean = statistics.fmean(s.mean_rel_residual for s in elig)
    ranked = sorted(elig, key=lambda s: s.mean_rel_residual, reverse=True)
    best, worst = ranked[0], ranked[-1]
    out = []
    for s, kind in ((best, "best"), (worst, "worst")):
        delta_farm = round(100 * (s.mean_rel_residual - farm_mean), 1)
        word = "acima" if delta_farm >= 0 else "abaixo"
        out.append(Insight(
            type=f"{kind}_field_yield", scope="field", field_id=s.field_id,
            title=f"Talhão {'de maior' if kind == 'best' else 'de menor'} produtividade: "
                  f"{s.field_name}",
            detail=(f"{s.field_name} rende {abs(delta_farm)}% {word} da média da fazenda "
                    f"({s.bias_percentage:+}% vs. região), em {s.n_seasons} safras."),
            evidence={"n_seasons": s.n_seasons, "delta_vs_farm_pct": delta_farm,
                      "bias_vs_region_pct": s.bias_percentage},
            confidence=_confidence(s.n_seasons),
        ))
    return out


def stability_ranking(summaries: list[FieldSummary]) -> list[Insight]:
    elig = [s for s in _eligible(summaries, MIN_SEASONS_STABILITY)
            if s.yield_stability_std is not None]
    if len(elig) < 2:
        return []
    ranked = sorted(elig, key=lambda s: s.yield_stability_std)  # menor std = mais estável
    most, least = ranked[0], ranked[-1]
    if least.yield_stability_std < STABILITY_GAP * max(most.yield_stability_std, 1e-9):
        return []  # diferença não é marcante o bastante para afirmar
    return [
        Insight(
            type="most_stable_field", scope="field", field_id=most.field_id,
            title=f"Talhão mais estável: {most.field_name}",
            detail=(f"{most.field_name} é o mais consistente "
                    f"(desvio de {round(100 * most.yield_stability_std, 1)}% nos resíduos "
                    f"ajustados ao clima, {most.n_seasons} safras)."),
            evidence={"n_seasons": most.n_seasons,
                      "stability_std_pct": round(100 * most.yield_stability_std, 1)},
            confidence=_confidence(most.n_seasons),
        ),
        Insight(
            type="least_stable_field", scope="field", field_id=least.field_id,
            title=f"Talhão menos estável: {least.field_name}",
            detail=(f"{least.field_name} apresenta a menor estabilidade "
                    f"(desvio de {round(100 * least.yield_stability_std, 1)}%, "
                    f"{least.n_seasons} safras) — maior risco de variação."),
            evidence={"n_seasons": least.n_seasons,
                      "stability_std_pct": round(100 * least.yield_stability_std, 1)},
            confidence=_confidence(least.n_seasons),
        ),
    ]


def cost_trends(summaries: list[FieldSummary]) -> list[Insight]:
    out = []
    for s in summaries:
        t = s.cost_trend
        if not t or t["direction"] == "stable" or abs(t["net_change_pct"]) < 10:
            continue
        word = "crescendo" if t["direction"] == "rising" else "caindo"
        out.append(Insight(
            type="cost_trend", scope="field", field_id=s.field_id,
            title=f"Custo {word} no talhão {s.field_name}",
            detail=(f"O custo/ha do {s.field_name} está {word} há {t['n']} safras "
                    f"({t['net_change_pct']:+}% de {t['first_year']} a {t['last_year']})."),
            evidence={"n_seasons": t["n"], "net_change_pct": t["net_change_pct"],
                      "monotonic": t["monotonic"]},
            confidence="alta" if t["monotonic"] and t["n"] >= 4 else "moderada",
        ))
    return out


def yield_anomalies(records_by_field: dict[int, list[FieldSeasonRecord]]) -> list[Insight]:
    out = []
    for recs in records_by_field.values():
        recs = sorted(recs, key=lambda r: r.harvest_year)
        z = yield_anomaly_zscore([r.rel_residual for r in recs], MIN_SEASONS_ANOMALY)
        if z is None or abs(z) < ANOMALY_Z:
            continue
        latest = recs[-1]
        word = "muito acima" if z > 0 else "muito abaixo"
        out.append(Insight(
            type="yield_anomaly", scope="field", field_id=latest.field_id,
            title=f"Anomalia no talhão {latest.field_name} ({latest.harvest_year})",
            detail=(f"A safra {latest.harvest_year} do {latest.field_name} ficou {word} "
                    f"da norma do talhão (z={round(z, 1)})."),
            evidence={"n_seasons": len(recs), "zscore": round(z, 2),
                      "harvest_year": latest.harvest_year},
            confidence=_confidence(len(recs)),
        ))
    return out


def farm_vs_region(all_records: list[FieldSeasonRecord]) -> list[Insight]:
    if len({r.harvest_year for r in all_records}) < MIN_SEASONS_TREND:
        return []
    bias = round(100 * statistics.fmean(r.rel_residual for r in all_records), 1)
    n = len(all_records)
    word = "acima" if bias >= 0 else "abaixo"
    return [Insight(
        type="farm_vs_region", scope="farm",
        title="Desempenho da fazenda vs. região",
        detail=(f"No conjunto ({n} registros de talhão-safra), a fazenda rende "
                f"{abs(bias)}% {word} da expectativa regional ajustada ao clima."),
        evidence={"n_records": n, "bias_vs_region_pct": bias},
        confidence=_confidence(n),
    )]


_PRIORITY = {"alta": 0, "moderada": 1, "exploratória": 2}


def generate_insights(
    summaries: list[FieldSummary],
    records_by_field: dict[int, list[FieldSeasonRecord]],
) -> list[Insight]:
    """Roda todas as regras gated e ordena por confiança (alta primeiro)."""
    all_records = [r for recs in records_by_field.values() for r in recs]
    insights = (
        performance_ranking(summaries)
        + stability_ranking(summaries)
        + cost_trends(summaries)
        + yield_anomalies(records_by_field)
        + farm_vs_region(all_records)
    )
    return sorted(insights, key=lambda i: _PRIORITY[i.confidence])
