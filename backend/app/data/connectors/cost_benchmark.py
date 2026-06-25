"""Leitor do artefato de benchmark de custo (CONAB) — runtime leve.

Mesma filosofia do artefato de modelo/preço (ADR-0018): coleta pesada offline no
pipeline ``build_cost_benchmark``; runtime só lê um JSON pequeno e datado.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings
from app.domain.benchmark import CostBenchmark, CostComponent


def _artifact_path(crop: str, uf: str) -> Path:
    return settings.data_dir / "benchmarks" / f"{crop}_{uf.lower()}_cost.json"


class CostBenchmarkStore:
    """Carrega o benchmark de custo de uma cultura/UF a partir do artefato."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base = base_dir

    def _path(self, crop: str, uf: str) -> Path:
        if self._base is not None:
            return self._base / f"{crop}_{uf.lower()}_cost.json"
        return _artifact_path(crop, uf)

    def load(self, crop: str, uf: str) -> CostBenchmark | None:
        path = self._path(crop, uf)
        if not path.exists():
            return None
        return _parse(json.loads(path.read_text()))


def _parse(doc: dict) -> CostBenchmark:
    components = tuple(
        CostComponent(
            item=c["item"],
            value_per_ha=float(c["value_per_ha"]),
            share_pct=float(c["share_pct"]),
        )
        for c in doc.get("components", [])
    )
    return CostBenchmark(
        crop=doc["crop"],
        uf=doc["uf"],
        safra=doc["safra"],
        technology=doc["technology"],
        source=doc["source"],
        fetched_at=doc["fetched_at"],
        coe_per_ha=float(doc["coe_per_ha"]),
        cot_per_ha=float(doc["cot_per_ha"]),
        ct_per_ha=float(doc["ct_per_ha"]),
        components=components,
    )
