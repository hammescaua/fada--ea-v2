"""Crédito rural — matemática de financiamento determinística (ADR-0030).

Tudo aqui é cálculo puro: dado principal, taxa, prazo e sistema (Price/SAC),
produz o cronograma resumido. As taxas/linhas do Plano Safra entram como
**referência** (artefato datado e citado) que o produtor confirma — nunca um
número inventado. O LLM não participa (ADR-0002).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FinancingSummary:
    principal: float
    annual_rate_pct: float
    term_months: int
    system: str  # "price" | "sac"
    first_installment: float
    last_installment: float
    total_paid: float
    total_interest: float
    interest_over_principal_pct: float


def _monthly_rate(annual_rate_pct: float) -> float:
    """Taxa mensal equivalente (juros compostos) a partir da taxa anual em %."""
    return (1 + annual_rate_pct / 100) ** (1 / 12) - 1


def simulate_financing(
    principal: float,
    annual_rate_pct: float,
    term_months: int,
    system: str = "price",
) -> FinancingSummary:
    """Resume um financiamento. ``system``: 'price' (parcela fixa) ou 'sac' (decrescente)."""
    if principal <= 0:
        raise ValueError("principal deve ser positivo")
    if term_months <= 0:
        raise ValueError("term_months deve ser positivo")
    if annual_rate_pct < 0:
        raise ValueError("annual_rate_pct não pode ser negativo")
    system = system.lower()
    if system not in ("price", "sac"):
        raise ValueError("system deve ser 'price' ou 'sac'")

    i = _monthly_rate(annual_rate_pct)
    n = term_months

    if i == 0:  # sem juros (linha subsidiada a 0%): parcelas iguais
        installments = [principal / n] * n
    elif system == "price":
        pmt = principal * (i * (1 + i) ** n) / ((1 + i) ** n - 1)
        installments = [pmt] * n
    else:  # SAC: amortização constante, juros sobre saldo decrescente
        amort = principal / n
        installments = [amort + (principal - amort * k) * i for k in range(n)]

    total_paid = sum(installments)
    total_interest = total_paid - principal
    return FinancingSummary(
        principal=round(principal, 2),
        annual_rate_pct=round(annual_rate_pct, 4),
        term_months=n,
        system=system,
        first_installment=round(installments[0], 2),
        last_installment=round(installments[-1], 2),
        total_paid=round(total_paid, 2),
        total_interest=round(total_interest, 2),
        interest_over_principal_pct=round(100 * total_interest / principal, 1),
    )
