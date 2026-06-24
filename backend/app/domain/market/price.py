"""Domínio de mercado: preço da saca — value objects e estatísticas puras.

Princípio (ADR-0003, ADR-0011): o FADA **não prevê preço**. Aqui só representamos
preço *observado* de fonte oficial (CEPEA/ESALQ) e derivamos estatísticas
descritivas honestas (último, média, mínimo/máximo, variação) sobre a série já
coletada. Nada de forecast. Funções puras e determinísticas — sem I/O.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PricePoint:
    """Um preço observado num dia, em uma praça, na unidade da fonte."""

    day: date
    value: float  # R$ na unidade da fonte (ex.: BRL/sc60kg)


@dataclass(frozen=True)
class PriceSnapshot:
    """Série de preços observados de um produto numa praça, com proveniência.

    A série vem ordenada do mais antigo para o mais recente. ``fetched_at`` é a
    data em que o artefato foi coletado da fonte — distinta da data do último
    preço (``latest.day``), o que permite comunicar **defasagem** com honestidade.
    """

    crop: str
    source: str          # ex.: "CEPEA/ESALQ"
    place: str           # praça de referência (ex.: "Paranaguá/PR")
    unit: str            # ex.: "BRL/sc60kg"
    fetched_at: date
    series: tuple[PricePoint, ...]

    def __post_init__(self) -> None:
        if not self.series:
            raise ValueError("PriceSnapshot exige ao menos um ponto de preço.")

    @property
    def latest(self) -> PricePoint:
        return self.series[-1]


@dataclass(frozen=True)
class PriceSummary:
    """Estatística descritiva da série — honesta, sem extrapolação."""

    latest_value: float
    latest_day: date
    n_points: int
    window_days: int            # span coberto pela série (primeiro→último)
    mean_value: float
    min_value: float
    max_value: float
    change_pct: float           # variação % do primeiro ao último ponto
    staleness_days: int         # dias entre o último preço e a coleta (defasagem)
    is_stale: bool              # defasagem acima do tolerável


# Acima disto, o preço observado é velho demais para decisão sem ressalva.
STALENESS_TOLERANCE_DAYS = 7


def summarize(snapshot: PriceSnapshot, *, reference_day: date | None = None) -> PriceSummary:
    """Reduz a série a uma estatística descritiva. Determinística e pura.

    Args:
        snapshot: série observada com proveniência.
        reference_day: "hoje" para medir defasagem; default = ``fetched_at`` do
            snapshot (mantém a função pura/testável quando não há relógio).
    """
    pts = snapshot.series
    values = [p.value for p in pts]
    first, last = pts[0], pts[-1]
    ref = reference_day or snapshot.fetched_at

    change_pct = 0.0 if first.value == 0 else (last.value - first.value) / first.value * 100.0
    staleness = (ref - last.day).days

    return PriceSummary(
        latest_value=round(last.value, 2),
        latest_day=last.day,
        n_points=len(pts),
        window_days=(last.day - first.day).days,
        mean_value=round(statistics.fmean(values), 2),
        min_value=round(min(values), 2),
        max_value=round(max(values), 2),
        change_pct=round(change_pct, 2),
        staleness_days=staleness,
        is_stale=staleness > STALENESS_TOLERANCE_DAYS,
    )
