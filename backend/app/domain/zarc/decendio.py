"""Conversão de decêndios ZARC em janelas de data — puro e determinístico.

A tábua de risco do ZARC tem 36 decêndios (períodos de ~10 dias): dec1 = 1º
decêndio de janeiro … dec36 = 3º de dezembro. Cada célula traz o **nível de risco**
(20/30/40%) em que aquele decêndio é indicado para plantio (20% = mais conservador;
0 = não indicado). Aqui só convertemos índices de decêndio em intervalos de data
(MM-DD) e fundimos decêndios contíguos — inclusive na virada dez→jan.
"""

from __future__ import annotations

# Último dia de cada mês (season-agnostic; fevereiro = 28 por segurança).
_MONTH_LAST_DAY = {
    1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
    7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31,
}


def decendio_bounds(i: int) -> tuple[tuple[int, int], tuple[int, int]]:
    """Retorna ((mês_ini, dia_ini), (mês_fim, dia_fim)) do decêndio i (1..36)."""
    if not 1 <= i <= 36:
        raise ValueError(f"decêndio fora de 1..36: {i}")
    month = (i - 1) // 3 + 1
    decade = (i - 1) % 3
    start_day = decade * 10 + 1
    end_day = _MONTH_LAST_DAY[month] if decade == 2 else decade * 10 + 10
    return (month, start_day), (month, end_day)


def _md(t: tuple[int, int]) -> str:
    return f"{t[0]:02d}-{t[1]:02d}"


def decendios_to_windows(decendios: set[int]) -> list[tuple[str, str]]:
    """Funde decêndios favoráveis em janelas (start, end) no formato 'MM-DD'.

    Decêndios contíguos viram uma janela. Trata a virada do ano: se há sequência
    terminando em 36 e outra começando em 1, elas se unem (ex.: out→jan da soja).
    """
    if not decendios:
        return []
    ordered = sorted(decendios)
    runs: list[list[int]] = []
    for d in ordered:
        if runs and d == runs[-1][-1] + 1:
            runs[-1].append(d)
        else:
            runs.append([d])
    # Une a virada do ano (…,36) + (1,…) numa janela só.
    if len(runs) > 1 and runs[0][0] == 1 and runs[-1][-1] == 36:
        wrap = runs.pop()
        runs[0] = wrap + runs[0]
    return [(_md(decendio_bounds(r[0])[0]), _md(decendio_bounds(r[-1])[1])) for r in runs]
