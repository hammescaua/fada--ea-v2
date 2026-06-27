"""Leitor do catálogo de crédito rural (Plano Safra) — runtime leve (ADR-0030).

Catálogo de **referência** datado e citado. Runtime só lê o JSON pequeno; degrada
graciosamente (lista vazia se ausente). As taxas são referência, não oferta.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings

_PATH = settings.data_dir / "credit" / "plano_safra.json"


class CreditStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _PATH
        self._doc: dict | None = None

    def _data(self) -> dict:
        if self._doc is None:
            self._doc = json.loads(self._path.read_text()) if self._path.exists() else {}
        return self._doc

    def meta(self) -> dict:
        d = self._data()
        return {k: d.get(k) for k in ("source", "fetched_at", "safra", "note")}

    def lines(self) -> list[dict]:
        return list(self._data().get("lines", []))
