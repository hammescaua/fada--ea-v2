"""Janelas de plantio ZARC e avaliação de uma data — puro e determinístico.

Trabalha com janelas em 'MM-DD' (independentes de safra). A verificação trata
janelas que cruzam a virada do ano (ex.: 10-01 a 01-31, típica da soja no RS).
"""

from __future__ import annotations

from dataclasses import dataclass

# Níveis de risco do ZARC, do mais conservador ao menos.
RISK_LEVELS = (20, 30, 40)


def _to_md(value: str) -> tuple[int, int]:
    m, d = value.split("-")
    return int(m), int(d)


def in_window(month: int, day: int, start: str, end: str) -> bool:
    """A data (mês, dia) cai na janela [start, end]? Trata virada do ano."""
    s, e, x = _to_md(start), _to_md(end), (month, day)
    if s <= e:
        return s <= x <= e
    # janela com virada (start > end): vale se >= start OU <= end
    return x >= s or x <= e


@dataclass(frozen=True)
class PlantingWindows:
    """Janelas favoráveis por nível de risco para um município/cultura."""

    municipality_code: int
    municipality_name: str
    windows_by_risk: dict[int, list[tuple[str, str]]]  # risco -> [(start, end)]

    def best_risk_for(self, month: int, day: int) -> int | None:
        """Menor (mais seguro) nível de risco cuja janela contém a data; None se fora."""
        for risk in RISK_LEVELS:
            for start, end in self.windows_by_risk.get(risk, []):
                if in_window(month, day, start, end):
                    return risk
        return None

    def evaluate(self, month: int, day: int) -> dict:
        risk = self.best_risk_for(month, day)
        return {
            "within_zarc": risk is not None,
            "risk_level": risk,
            "interpretation": (
                f"Dentro da janela ZARC ao nível de risco {risk}% "
                "(quanto menor, mais conservador/seguro)."
                if risk is not None
                else "Fora da janela ZARC indicada — risco climático acima do zoneado."
            ),
        }
