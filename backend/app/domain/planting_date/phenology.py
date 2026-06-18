"""Fenologia da soja por tempo térmico (Growing Degree Days).

A data de plantio desloca as janelas fenológicas de forma **não linear**: em meses
mais frios a planta acumula GDD mais devagar e a janela reprodutiva anda menos do
que o deslocamento da semeadura. Modelar isso por soma térmica (base 10 °C) é
mecanisticamente correto e reaproveita o índice de GDD já existente.

Limiares (GDD desde o plantio, base 10 °C) são parâmetros documentados, calibrados
para reproduzir aproximadamente a janela reprodutiva de treino na data-base
regional. Calibração fina por grupo de maturação exige dado de campo (ADR-0007).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.climate import DailyWeather


@dataclass(frozen=True)
class PhenologyStages:
    planting: date
    emergence: date
    r1_begin_flowering: date
    r6_full_seed: date

    @property
    def reproductive_window(self) -> tuple[date, date]:
        """Período crítico para estresse hídrico/térmico: R1 a R6."""
        return (self.r1_begin_flowering, self.r6_full_seed)


@dataclass(frozen=True)
class PhenologyModel:
    """Limiares de GDD (base 10 °C) acumulados desde o plantio."""

    base_temp: float = 10.0
    gdd_emergence: float = 110.0
    gdd_r1: float = 720.0  # início do florescimento
    gdd_r6: float = 1500.0  # grão cheio (fim do período crítico)

    def _reach(self, series: list[DailyWeather], planting: date, target_gdd: float) -> date:
        """Primeira data em que o GDD acumulado desde o plantio atinge ``target_gdd``."""
        acc = 0.0
        for d in series:
            if d.day < planting:
                continue
            acc += max(0.0, d.tmean - self.base_temp)
            if acc >= target_gdd:
                return d.day
        # Série insuficiente: retorna o último dia disponível (degradação graciosa).
        return series[-1].day

    def stages(self, series: list[DailyWeather], planting: date) -> PhenologyStages:
        return PhenologyStages(
            planting=planting,
            emergence=self._reach(series, planting, self.gdd_emergence),
            r1_begin_flowering=self._reach(series, planting, self.gdd_r1),
            r6_full_seed=self._reach(series, planting, self.gdd_r6),
        )


# Soja indeterminada típica do Noroeste RS (grupos ~5.5–6.2).
SOYBEAN_PHENOLOGY_RS = PhenologyModel()
