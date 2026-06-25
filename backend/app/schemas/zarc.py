"""DTOs do ZARC (janela oficial de plantio)."""

from __future__ import annotations

from pydantic import BaseModel


class WindowOut(BaseModel):
    start: str  # MM-DD
    end: str    # MM-DD


class ZarcWindowResponse(BaseModel):
    crop: str
    uf: str
    safra: str
    manejo: str
    portaria: str
    source: str
    fetched_at: str
    note: str
    municipality_code: int
    municipality_name: str
    windows_by_risk: dict[str, list[WindowOut]]
    disclaimer: str
    # Preenchidos só quando uma data é avaliada:
    planting_date: str | None = None
    within_zarc: bool | None = None
    risk_level: int | None = None
    interpretation: str | None = None
