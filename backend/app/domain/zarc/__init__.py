"""Domínio ZARC — zoneamento agrícola de risco climático (janelas de plantio)."""

from __future__ import annotations

from app.domain.zarc.decendio import decendio_bounds, decendios_to_windows
from app.domain.zarc.windows import (
    RISK_LEVELS,
    PlantingWindows,
    in_window,
)

__all__ = [
    "RISK_LEVELS",
    "PlantingWindows",
    "decendio_bounds",
    "decendios_to_windows",
    "in_window",
]
