"""Previsão diária e motor de alertas agronômicos — nomeados e auditáveis.

Transforma a previsão (Open-Meteo Forecast) em **alertas com nome, janela e
evidência** — nunca um "score mágico" (coerente com ADR-0016). Previsão erra: a
confiança decai com o horizonte e os alertas de chuva usam a **probabilidade**
da fonte, jamais comunicados como certeza (ADR-0003).

Funções puras e determinísticas — sem I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

# -- limiares (documentados; ajustáveis) ------------------------------------
FROST_TMIN_C = 3.0           # risco de geada quando tmin ≤ 3 °C (cultura sensível)
FROST_SEVERE_TMIN_C = 1.0    # geada provável/forte
DRY_DAY_PRECIP_MM = 1.0      # dia "seco": chuva < 1 mm
DRY_DAY_PROB_MAX = 40.0      # …e probabilidade de chuva < 40%
DRY_SPELL_WATCH_DAYS = 5     # veranico em atenção a partir de 5 dias secos seguidos
DRY_SPELL_ALERT_DAYS = 7     # …e alerta a partir de 7
SPRAY_WIND_MAX_KMH = 15.0    # janela de pulverização: vento ≤ 15 km/h
SPRAY_PROB_MAX = 20.0        # …e probabilidade de chuva ≤ 20%
HEAVY_RAIN_MM = 30.0         # chuva intensa no dia
HEAVY_RAIN_PROB = 60.0       # …com probabilidade ≥ 60%


@dataclass(frozen=True)
class DailyForecast:
    day: date
    tmin: float
    tmax: float
    precipitation_mm: float
    precipitation_prob: float   # 0–100 (%)
    wind_max_kmh: float


@dataclass(frozen=True)
class Alert:
    code: str
    severity: str               # "info" | "atenção" | "alerta"
    title: str
    detail: str
    starts_on: date
    ends_on: date
    confidence: str             # "alta" | "média" | "baixa"
    evidence: dict = field(default_factory=dict)


def _confidence_for(horizon_index: int) -> str:
    """Confiança decai com o horizonte da previsão (dias a partir de hoje)."""
    if horizon_index <= 2:
        return "alta"
    if horizon_index <= 6:
        return "média"
    return "baixa"


def _frost_alerts(fc: list[DailyForecast]) -> list[Alert]:
    cold = [(i, d) for i, d in enumerate(fc) if d.tmin <= FROST_TMIN_C]
    if not cold:
        return []
    days = [d for _, d in cold]
    coldest = min(days, key=lambda d: d.tmin)
    severe = coldest.tmin <= FROST_SEVERE_TMIN_C
    idx0 = cold[0][0]
    return [
        Alert(
            code="geada",
            severity="alerta" if severe else "atenção",
            title="Risco de geada",
            detail=(
                f"Mínima prevista de {coldest.tmin:.1f} °C em {coldest.day.isoformat()}"
                f" ({len(days)} dia(s) com risco no horizonte). Avalie proteção/colheita."
            ),
            starts_on=days[0].day,
            ends_on=days[-1].day,
            confidence=_confidence_for(idx0),
            evidence={
                "min_tmin_c": round(coldest.tmin, 1),
                "n_days": len(days),
                "threshold_c": FROST_TMIN_C,
            },
        )
    ]


def _longest_dry_run(fc: list[DailyForecast]) -> tuple[int, int] | None:
    """Maior sequência de dias secos consecutivos; retorna (índice_início, comprimento)."""
    best_start = best_len = 0
    cur_start = cur_len = 0
    for i, d in enumerate(fc):
        is_dry = d.precipitation_mm < DRY_DAY_PRECIP_MM and d.precipitation_prob < DRY_DAY_PROB_MAX
        if is_dry:
            if cur_len == 0:
                cur_start = i
            cur_len += 1
            if cur_len > best_len:
                best_len, best_start = cur_len, cur_start
        else:
            cur_len = 0
    return (best_start, best_len) if best_len else None


def _dry_spell_alerts(fc: list[DailyForecast]) -> list[Alert]:
    run = _longest_dry_run(fc)
    if run is None or run[1] < DRY_SPELL_WATCH_DAYS:
        return []
    start, length = run
    window = fc[start:start + length]
    severe = length >= DRY_SPELL_ALERT_DAYS
    return [
        Alert(
            code="veranico",
            severity="alerta" if severe else "atenção",
            title="Veranico (estiagem) à vista",
            detail=(
                f"{length} dias seguidos sem chuva relevante previstos, de "
                f"{window[0].day.isoformat()} a {window[-1].day.isoformat()}. "
                "Atenção ao estresse hídrico, sobretudo no período reprodutivo."
            ),
            starts_on=window[0].day,
            ends_on=window[-1].day,
            confidence=_confidence_for(start),
            evidence={"dry_days": length, "threshold_days": DRY_SPELL_WATCH_DAYS},
        )
    ]


def _spray_window_alerts(fc: list[DailyForecast]) -> list[Alert]:
    good = [
        d for d in fc
        if d.wind_max_kmh <= SPRAY_WIND_MAX_KMH and d.precipitation_prob <= SPRAY_PROB_MAX
    ]
    if not good:
        return []
    return [
        Alert(
            code="janela_pulverizacao",
            severity="info",
            title="Boa janela de pulverização",
            detail=(
                f"{len(good)} dia(s) com vento baixo e baixa chance de chuva — "
                f"próximo em {good[0].day.isoformat()}."
            ),
            starts_on=good[0].day,
            ends_on=good[-1].day,
            confidence=_confidence_for(0),
            evidence={
                "good_days": [d.day.isoformat() for d in good[:5]],
                "wind_max_kmh": SPRAY_WIND_MAX_KMH,
                "prob_max": SPRAY_PROB_MAX,
            },
        )
    ]


def _heavy_rain_alerts(fc: list[DailyForecast]) -> list[Alert]:
    wet = [
        (i, d) for i, d in enumerate(fc)
        if d.precipitation_mm >= HEAVY_RAIN_MM and d.precipitation_prob >= HEAVY_RAIN_PROB
    ]
    if not wet:
        return []
    idx0, first = wet[0]
    heaviest = max((d for _, d in wet), key=lambda d: d.precipitation_mm)
    return [
        Alert(
            code="chuva_intensa",
            severity="atenção",
            title="Chuva intensa prevista",
            detail=(
                f"Até {heaviest.precipitation_mm:.0f} mm em {heaviest.day.isoformat()} "
                f"({heaviest.precipitation_prob:.0f}% de probabilidade). "
                "Pode afetar pulverização, colheita ou causar encharcamento."
            ),
            starts_on=first.day,
            ends_on=wet[-1][1].day,
            confidence=_confidence_for(idx0),
            evidence={
                "max_precip_mm": round(heaviest.precipitation_mm, 1),
                "prob_pct": round(heaviest.precipitation_prob, 0),
            },
        )
    ]


# Ordem de exibição: o que exige ação primeiro.
_SEVERITY_RANK = {"alerta": 0, "atenção": 1, "info": 2}


def build_alerts(fc: list[DailyForecast]) -> list[Alert]:
    """Aplica todas as regras e ordena por severidade. Determinístico."""
    alerts: list[Alert] = []
    alerts += _frost_alerts(fc)
    alerts += _dry_spell_alerts(fc)
    alerts += _heavy_rain_alerts(fc)
    alerts += _spray_window_alerts(fc)
    alerts.sort(key=lambda a: _SEVERITY_RANK.get(a.severity, 9))
    return alerts
