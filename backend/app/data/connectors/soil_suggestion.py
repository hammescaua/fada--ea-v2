"""Leitor do artefato de sugestão de solo (EMBRAPA) — runtime leve (ADR-0028).

Coleta pesada (WFS EMBRAPA) acontece offline no pipeline ``build_soil_suggestions``;
o runtime só lê o JSON pequeno. Degrada graciosamente (None se ausente).
"""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings

_PATH = settings.data_dir / "geo" / "soil_suggestions.json"


class SoilSuggestionStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _PATH
        self._doc: dict | None = None

    def _data(self) -> dict:
        if self._doc is None:
            self._doc = json.loads(self._path.read_text()) if self._path.exists() else {}
        return self._doc

    def meta(self) -> dict:
        d = self._data()
        return {k: d.get(k) for k in ("source", "fetched_at", "note")}

    def for_municipality(self, municipality_code: int) -> dict | None:
        entry = self._data().get("municipalities", {}).get(str(municipality_code))
        if entry is None:
            return None
        return {**self.meta(), **entry}
