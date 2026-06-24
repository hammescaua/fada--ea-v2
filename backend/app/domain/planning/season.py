"""Síntese de margem pré-safra — combina produtividade, preço e custo de referência.

Puro e determinístico. Não inventa nada: usa os cenários de produtividade do modelo
regional, o preço **observado** (CEPEA) e o custo **de referência** (CONAB) para
projetar margem e ponto de equilíbrio *antes* da safra — apoio à decisão, não promessa.
"""

from __future__ import annotations

from app.domain.cost import calculate_break_even_yield, scenario_analysis


def season_margin(
    yield_scenarios: dict[str, float],
    expected_yield_sc_ha: float,
    price_per_bag: float,
    costs_per_ha: dict[str, float],
) -> dict:
    """Projeta margem por cenário e ponto de equilíbrio por conceito de custo.

    Args:
        yield_scenarios: {nome: sc/ha} (pessimista/normal/otimista).
        expected_yield_sc_ha: produtividade esperada (ponto).
        price_per_bag: preço da saca (R$/sc), observado.
        costs_per_ha: {"coe":.., "cot":.., "ct":..} custos de referência (R$/ha).

    A margem dos cenários é calculada sobre o **COT** (custo operacional total —
    o caixa mais depreciações), base usual para "fechei a conta da safra?".
    """
    cot = costs_per_ha["cot"]
    scenarios = scenario_analysis(cot, 1.0, price_per_bag, yield_scenarios)  # base 1 ha
    break_even = {
        k: calculate_break_even_yield(v, price_per_bag) for k, v in costs_per_ha.items()
    }
    exp_revenue = round(expected_yield_sc_ha * price_per_bag, 2)
    exp_profit = round(exp_revenue - cot, 2)
    return {
        "price_per_bag": price_per_bag,
        "cost_basis": "COT",
        "cost_per_ha_cot": cot,
        "break_even_yield_sc_ha": break_even,  # por conceito de custo (coe/cot/ct)
        "scenarios": scenarios,                # lucro/ha por cenário de produtividade
        "expected": {
            "yield_sc_ha": expected_yield_sc_ha,
            "revenue_per_ha": exp_revenue,
            "profit_per_ha": exp_profit,
            "margin_pct": round(100 * exp_profit / exp_revenue, 1) if exp_revenue else 0.0,
        },
    }
