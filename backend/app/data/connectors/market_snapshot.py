"""Leitor do artefato de preço destilado (runtime leve, sem agrobr/pandas).

Segue a mesma filosofia do artefato do modelo (JSON inspecionável): o trabalho
pesado e instável (rede, parsing, cache duckdb do agrobr) acontece **offline** no
pipeline ``build_market_snapshot``; o runtime apenas lê um JSON pequeno e datado.
Degrada graciosamente: se o artefato não existe, retorna ``None`` — a API então
diz o que não sabe, nunca inventa preço.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from app.core.config import settings
from app.domain.market import PricePoint, PriceSnapshot


def _artifact_path(crop: str) -> Path:
    return settings.data_dir / "market" / f"{crop}_price.json"


class MarketSnapshotStore:
    """Carrega o snapshot de preço de um produto a partir do artefato em disco."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base = base_dir

    def _path(self, crop: str) -> Path:
        if self._base is not None:
            return self._base / f"{crop}_price.json"
        return _artifact_path(crop)

    def load(self, crop: str) -> PriceSnapshot | None:
        path = self._path(crop)
        if not path.exists():
            return None
        return _parse(json.loads(path.read_text()))


def _parse(doc: dict) -> PriceSnapshot:
    series = tuple(
        PricePoint(day=date.fromisoformat(p["day"]), value=float(p["value"]))
        for p in doc["series"]
    )
    return PriceSnapshot(
        crop=doc["crop"],
        source=doc["source"],
        place=doc["place"],
        unit=doc["unit"],
        fetched_at=date.fromisoformat(doc["fetched_at"]),
        series=series,
    )
