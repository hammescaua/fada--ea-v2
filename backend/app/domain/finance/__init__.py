"""Domínio financeiro — crédito rural e comparação de 2ª safra (ADR-0030)."""

from app.domain.finance.credit import FinancingSummary, simulate_financing
from app.domain.finance.rotation import CropMargin, CropOption, compare_options

__all__ = [
    "CropMargin",
    "CropOption",
    "FinancingSummary",
    "compare_options",
    "simulate_financing",
]
