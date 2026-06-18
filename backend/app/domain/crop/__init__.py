"""Crop — calendário e fenologia.

Define as janelas temporais relativas à safra usadas pela engenharia de features.
Não é um preditor: serve para *delimitar* onde medir o estresse climático.
"""

from app.domain.crop.calendar import CropCalendar, SeasonWindows, SOYBEAN_RS

__all__ = ["CropCalendar", "SeasonWindows", "SOYBEAN_RS"]
