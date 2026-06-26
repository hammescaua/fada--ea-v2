"""Frescor das fontes públicas — honestidade visível (ADR-0018).

Cada artefato datado (preço, custo, ZARC, solo) é distilado offline. Aqui
reportamos, de forma determinística e graciosa, a idade de cada fonte e um
rótulo de frescor, para que o agricultor saiba *quão atual* é cada número.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from app.core.config import settings

# (rótulo, caminho relativo a data_dir, validade em dias antes de "envelhecer")
_SOURCES: list[tuple[str, str, int]] = [
    ("Preço da soja", "market/soja_price.json", 7),
    ("Custo de produção", "benchmarks/soja_rs_cost.json", 120),
    ("Janela de plantio (ZARC)", "zarc/soja_rs.json", 365),
    ("Solo (EMBRAPA)", "geo/soil_suggestions.json", 3650),
]


def _read(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def _age_days(fetched_at: str | None, today: date) -> int | None:
    if not fetched_at:
        return None
    try:
        return (today - date.fromisoformat(fetched_at)).days
    except ValueError:
        return None


def data_sources_health(today: date | None = None) -> list[dict]:
    today = today or date.today()
    out: list[dict] = []
    for label, rel, max_age in _SOURCES:
        doc = _read(settings.data_dir / rel)
        present = bool(doc)
        fetched_at = doc.get("fetched_at")
        age = _age_days(fetched_at, today)
        if not present:
            status = "ausente"
        elif age is None:
            status = "ok"
        elif age <= max_age:
            status = "atual"
        else:
            status = "desatualizado"
        out.append(
            {
                "label": label,
                "source": doc.get("source"),
                "fetched_at": fetched_at,
                "age_days": age,
                "status": status,
            }
        )
    return out
