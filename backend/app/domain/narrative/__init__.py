"""Geração de leitura em linguagem natural das projeções (determinística)."""

from __future__ import annotations

from app.domain.narrative.season import narrate_brief
from app.domain.narrative.estimate import narrate_estimate

__all__ = ["narrate_brief", "narrate_estimate"]
