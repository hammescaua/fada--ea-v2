"""Ajuste de custo pelo Perfil Agronômico — personaliza a rentabilidade.

Companheiro do ajuste de produtividade (ADR-0022): o **mesmo** perfil do talhão
também desloca o **custo de referência** (CONAB), porque manejo e sistema mexem no
desembolso — irrigação encarece; cortar fungicida/inseticida barateia (e, no
módulo de produtividade, derruba o rendimento). A margem passa a capturar esse
trade-off: é exatamente o apoio à decisão ("vale cortar o fungicida?").

Só entram fatores com implicação de custo **clara e documentada**. Efeitos
relativos à fazenda típica do município (nível típico = 0). Puro/determinístico.
"""

from __future__ import annotations

from dataclasses import dataclass

# Limites do multiplicador de custo (mais estreito que o de produtividade).
MIN_COST_MULTIPLIER = 0.80
MAX_COST_MULTIPLIER = 1.25

# {fator: {opção: (efeito_relativo_no_custo, justificativa_curta)}}
COST_FACTOR_EFFECTS: dict[str, dict[str, tuple[float, str]]] = {
    "irrigacao": {
        "irrigado": (0.10, "Energia, manutenção e operação do sistema de irrigação."),
        "sequeiro": (0.0, ""),
    },
    "fungicida": {
        "completo": (0.0, ""),
        "parcial": (-0.04, "Menos aplicações de fungicida que o padrão."),
        "nenhum": (-0.08, "Sem programa de fungicida — economiza insumo/operação."),
    },
    "manejo_pragas": {
        "adequado": (0.0, ""),
        "parcial": (-0.02, "Menos inseticidas/monitoramento."),
        "deficiente": (-0.05, "Pouco controle de pragas — menor desembolso em insumos."),
    },
    "manejo_daninhas": {
        "adequado": (0.0, ""),
        "parcial": (-0.02, "Menos herbicidas/operações."),
        "deficiente": (-0.04, "Controle deficiente de daninhas — menos insumo."),
    },
    "acidez_corrigida": {
        "recente": (0.04, "Calagem aplicada na safra (calcário + operação)."),
        "antiga": (0.0, ""),
        "nao": (0.0, ""),
    },
    "plantio_direto": {
        "pd_consolidado": (-0.01, "Menos operações de preparo."),
        "pd_recente": (0.0, ""),
        "convencional": (0.03, "Mais operações/combustível no preparo do solo."),
    },
    "cultivar": {
        "moderna": (0.02, "Semente/tecnologia de maior valor (royalties)."),
        "intermediaria": (0.0, ""),
        "antiga": (-0.01, "Semente de menor custo."),
    },
    "tratamento_semente": {
        "sim": (0.0, ""),
        "nao": (-0.01, "Sem tratamento de sementes — pequena economia."),
    },
}


@dataclass(frozen=True)
class AppliedCostFactor:
    key: str
    option: str
    effect_pct: float
    rationale: str


@dataclass(frozen=True)
class CostAdjustmentResult:
    applied: list[AppliedCostFactor]
    multiplier: float
    raw_multiplier: float
    clamped: bool
    total_effect_pct: float


def compute_cost_adjustment(profile: dict[str, str]) -> CostAdjustmentResult:
    """Converte o perfil num multiplicador de custo transparente. Determinístico.

    Ignora fatores sem implicação de custo (entram só no ajuste de produtividade) e
    opções não mapeadas. Não levanta erro de validação — isso é papel do ajuste de
    produtividade, que valida o perfil inteiro.
    """
    applied: list[AppliedCostFactor] = []
    raw = 1.0
    for key, value in profile.items():
        effects = COST_FACTOR_EFFECTS.get(key)
        if effects is None or value not in effects:
            continue
        effect, rationale = effects[value]
        raw *= 1.0 + effect
        if effect != 0.0:
            applied.append(AppliedCostFactor(key, value, round(effect * 100, 1), rationale))
    multiplier = max(MIN_COST_MULTIPLIER, min(MAX_COST_MULTIPLIER, raw))
    applied.sort(key=lambda a: a.effect_pct)
    return CostAdjustmentResult(
        applied=applied,
        multiplier=round(multiplier, 4),
        raw_multiplier=round(raw, 4),
        clamped=abs(multiplier - raw) > 1e-9,
        total_effect_pct=round((multiplier - 1.0) * 100, 1),
    )
