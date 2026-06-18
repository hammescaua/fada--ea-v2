"""Definição da região-alvo do MVP: microrregião Três Passos (Noroeste RS).

Pool agroclimaticamente homogêneo usado para treino. Horizontina é o alvo de
referência, mas o modelo é treinado no painel dos 20 municípios para obter n
suficiente (ver ADR-0005).
"""

from __future__ import annotations

from dataclasses import dataclass

MICROREGION_TRES_PASSOS = 43002
HORIZONTINA_CODE = 4309605

# Faixa de anos de colheita do IBGE/PAM com cobertura (Open-Meteo cobre 1940+).
FIRST_HARVEST_YEAR = 1980
LAST_HARVEST_YEAR = 2024


@dataclass(frozen=True)
class TargetMunicipality:
    code: int
    name: str
    latitude: float
    longitude: float
