"""Serviço de mercado: preço observado + estatística honesta (sem forecast).

Lê o snapshot destilado via :class:`MarketSnapshotStore` e devolve um payload
datado, com defasagem explícita. Não há previsão de preço — apenas o observado
da fonte oficial e descritivas sobre a série (ADR-0003/0011).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.data.connectors.market_snapshot import MarketSnapshotStore
from app.domain.market import PriceSnapshot, PriceSummary, summarize


class PriceUnavailable(Exception):
    """Não há artefato de preço para o produto (fonte não coletada ainda)."""


@dataclass
class MarketService:
    store: MarketSnapshotStore = field(default_factory=MarketSnapshotStore)

    def _snapshot(self, crop: str) -> PriceSnapshot:
        snap = self.store.load(crop)
        if snap is None:
            raise PriceUnavailable(crop)
        return snap

    def latest_price_per_bag(self, crop: str = "soja") -> float | None:
        """Último preço observado (R$/sc), ou ``None`` se indisponível.

        Conveniência para o Financeiro usar como default. Silencioso por design:
        a ausência de preço não deve quebrar o cálculo de custo.
        """
        snap = self.store.load(crop)
        return round(snap.latest.value, 2) if snap is not None else None

    def price(self, crop: str = "soja", *, today: date | None = None) -> dict:
        """Payload de preço para a API: último, série, descritivas e proveniência."""
        snap = self._snapshot(crop)
        summary = summarize(snap, reference_day=today or date.today())
        return {
            "crop": snap.crop,
            "source": snap.source,
            "place": snap.place,
            "unit": snap.unit,
            "fetched_at": snap.fetched_at,
            "summary": summary,
            "series": list(snap.series),
            "disclaimer": _disclaimer(snap, summary),
        }


def _disclaimer(snap: PriceSnapshot, summary: PriceSummary) -> str:
    base = (
        f"Preço observado da {snap.source} (praça {snap.place}); "
        f"última cotação em {summary.latest_day.isoformat()}. "
        "O FADA não prevê preço — mostra o observado e cenários de margem."
    )
    if summary.is_stale:
        base += (
            f" Atenção: cotação com {summary.staleness_days} dias de defasagem — "
            "atualize a fonte antes de decidir."
        )
    return base
