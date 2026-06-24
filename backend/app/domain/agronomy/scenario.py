"""Personalização sensível ao cenário climático — o solo interage com o ano.

No Noroeste do RS a variância de produtividade da soja é governada pelo estresse
hídrico reprodutivo (veranico). Logo, os fatores **de água** do talhão não pesam
igual em todo ano: solo arenoso/raso/compactado penaliza mais em **ano seco**
(cenário pessimista) e quase nada em ano úmido; drenagem ruim é o inverso (pesa
mais em ano **úmido**); irrigação vale muito no seco.

Aqui calculamos um multiplicador **por cenário** (pessimista/normal/otimista),
amplificando/atenuando o efeito dos fatores hídricos conforme o ano. Os demais
fatores (sanidade, fertilidade, cultivar) pesam igual nos três cenários.

Puro e determinístico. Mantém a referência: no cenário **normal** os pesos são 1,0,
de modo que o multiplicador normal coincide com o ajuste a priori (sem regressão
no ponto). Ver ADR-0023.
"""

from __future__ import annotations

from app.domain.agronomy.profile import (
    FACTORS,
    MAX_MULTIPLIER,
    MIN_MULTIPLIER,
)

SCENARIO_NAMES = ("pessimista", "normal", "otimista")

# Peso do efeito do fator por cenário. Default (não listado) = 1,0 em todos.
# Fatores "tampão de seca": efeito amplificado no seco, atenuado no úmido.
_DROUGHT = {"pessimista": 1.6, "normal": 1.0, "otimista": 0.4}
# Drenagem: problema de EXCESSO de água — amplificado no úmido.
_EXCESS = {"pessimista": 0.4, "normal": 1.0, "otimista": 1.6}

SCENARIO_WEIGHTS: dict[str, dict[str, float]] = {
    "textura_solo": _DROUGHT,
    "profundidade_solo": _DROUGHT,
    "compactacao": _DROUGHT,
    "materia_organica": _DROUGHT,   # MO melhora retenção de água
    "irrigacao": _DROUGHT,          # benefício concentrado no ano seco
    "drenagem": _EXCESS,
}

# Fatores cuja sensibilidade ao cenário é relevante (para explicação na UI).
WATER_FACTORS = frozenset(SCENARIO_WEIGHTS)


def scenario_multipliers(profile: dict[str, str]) -> dict[str, float]:
    """Multiplicador agregado por cenário (pessimista/normal/otimista). Limitado."""
    out: dict[str, float] = {}
    for scen in SCENARIO_NAMES:
        m = 1.0
        for key, value in profile.items():
            factor = FACTORS.get(key)
            if factor is None or value not in factor.options:
                continue
            effect = factor.options[value].effect
            weight = SCENARIO_WEIGHTS.get(key, {}).get(scen, 1.0)
            m *= 1.0 + effect * weight
        out[scen] = round(max(MIN_MULTIPLIER, min(MAX_MULTIPLIER, m)), 4)
    return out


def water_sensitivity_note(profile: dict[str, str]) -> str | None:
    """Mensagem honesta sobre a sensibilidade do talhão ao ano, se relevante."""
    mults = scenario_multipliers(profile)
    pess, opt = mults["pessimista"], mults["otimista"]
    if pess < 0.97 and pess < opt - 0.05:
        return ("Talhão sensível a veranico: em ano seco o risco de queda é maior "
                "(veja o cenário pessimista).")
    if opt < 0.97 and opt < pess - 0.05:
        return ("Talhão sensível a excesso de chuva: em ano úmido o risco é maior "
                "(drenagem).")
    return None
