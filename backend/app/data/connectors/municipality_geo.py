"""Lookup offline de centroide de município (lat/lon) — runtime leve.

Destilado do dataset de features para evitar uma chamada de rede ao IBGE só para
obter coordenadas. Cobre a região do MVP; ausente → ``None`` (degradação graciosa).
"""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings

_PATH = settings.data_dir / "geo" / "municipality_centroids.json"


class MunicipalityCentroidStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _PATH
        self._cache: dict[str, dict] | None = None

    def _data(self) -> dict[str, dict]:
        if self._cache is None:
            self._cache = json.loads(self._path.read_text()) if self._path.exists() else {}
        return self._cache

    def latlon(self, municipality_code: int) -> tuple[float, float] | None:
        entry = self._data().get(str(municipality_code))
        if not entry:
            return None
        return float(entry["lat"]), float(entry["lon"])
