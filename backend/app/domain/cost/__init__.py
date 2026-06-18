"""Cost — engine financeiro determinístico (o "Cost Agent", feito certo).

Funções puras que dobram a timeline de eventos em custo total, custo/ha, custo/saca,
break-even e análise de cenários de lucro. Nenhum LLM participa (ADR-0002). Preço da
saca é input do produtor, não previsão de mercado (ADR-0011).
"""

from app.domain.cost.engine import (
    CostBreakdown,
    ScenarioResult,
    calculate_break_even_yield,
    calculate_cost_per_bag,
    calculate_cost_per_hectare,
    calculate_total_cost,
    cost_breakdown,
    count_applications,
    scenario_analysis,
)

__all__ = [
    "CostBreakdown",
    "ScenarioResult",
    "calculate_total_cost",
    "calculate_cost_per_hectare",
    "calculate_cost_per_bag",
    "calculate_break_even_yield",
    "scenario_analysis",
    "cost_breakdown",
    "count_applications",
]
