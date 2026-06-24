"""Leitor do artefato de janelas ZARC — runtime leve (ADR-0018)."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings
from app.domain.zarc import PlantingWindows


def _artifact_path(crop: str, uf: str) -> Path:
    return settings.data_dir / "zarc" / f"{crop}_{uf.lower()}.json"


class ZarcStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self._base = base_dir
        self._cache: dict[str, dict] = {}

    def _path(self, crop: str, uf: str) -> Path:
        if self._base is not None:
            return self._base / f"{crop}_{uf.lower()}.json"
        return _artifact_path(crop, uf)

    def _doc(self, crop: str, uf: str) -> dict | None:
        key = f"{crop}_{uf}"
        if key not in self._cache:
            path = self._path(crop, uf)
            self._cache[key] = json.loads(path.read_text()) if path.exists() else None
        return self._cache[key]

    def meta(self, crop: str, uf: str) -> dict | None:
        doc = self._doc(crop, uf)
        if doc is None:
            return None
        return {k: doc[k] for k in ("crop", "uf", "safra", "manejo", "portaria",
                                    "source", "fetched_at", "note")}

    def windows(self, crop: str, uf: str, municipality_code: int) -> PlantingWindows | None:
        doc = self._doc(crop, uf)
        if doc is None:
            return None
        entry = doc["municipalities"].get(str(municipality_code))
        if entry is None:
            return None
        by_risk = {
            int(r): [tuple(w) for w in wins]
            for r, wins in entry["windows_by_risk"].items()
        }
        return PlantingWindows(
            municipality_code=municipality_code,
            municipality_name=entry["name"],
            windows_by_risk=by_risk,
        )
