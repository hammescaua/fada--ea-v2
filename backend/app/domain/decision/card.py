"""Cartão de Decisão — o contrato único de toda recomendação do FADA (§4 do guia).

Materializa o "Decision Agent": clima, manejo, plantio e atenção por talhão se
apresentam no **mesmo formato** — decisão, recomendação, **efeito sempre com
incerteza** (sc/ha e/ou R$/ha), *porquê* auditável, confiança, horizonte e
disclaimer. Regras de honestidade herdadas da V1 (ADR-0003/0016): efeito nunca é
número seco; previsão/preço nunca como certeza; o cartão aponta o trade-off, não
prescreve laudo.

Funções puras e determinísticas — construtores que mapeam as fontes já existentes
(alertas de clima, recomendações econômicas, flags de atenção) para o cartão.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Origem do cartão (para agrupar/ordenar na UI).
SOURCE_CLIMA = "clima"
SOURCE_MANEJO = "manejo"
SOURCE_HISTORICO = "historico"

# Ordem de exibição: o proativo/urgente primeiro.
_SOURCE_RANK = {SOURCE_CLIMA: 0, SOURCE_MANEJO: 1, SOURCE_HISTORICO: 2}
_CONFIDENCE_MAP = {"alta": "alta", "média": "moderada", "media": "moderada", "baixa": "baixa"}


@dataclass(frozen=True)
class Evidence:
    label: str
    detail: str


@dataclass(frozen=True)
class DecisionEffect:
    basis: str                                  # "vs. manter o manejo atual"
    yield_sc_ha: tuple[float, float, float] | None = None   # [low, ponto, high]
    profit_brl_ha: tuple[float, float, float] | None = None # [low, ponto, high]


@dataclass(frozen=True)
class DecisionCard:
    id: str
    source: str
    decision: str           # a pergunta do produtor
    recommendation: str
    confidence: str         # "alta" | "moderada" | "baixa"
    horizon: str
    disclaimer: str
    n_data: int = 0
    effect: DecisionEffect | None = None
    why: list[Evidence] = field(default_factory=list)
    severity: str = "info"  # "alerta" | "atenção" | "info" (ordenação secundária)


_SEVERITY_RANK = {"alerta": 0, "atenção": 1, "info": 2}


def sort_cards(cards: list[DecisionCard]) -> list[DecisionCard]:
    """Ordena por origem (clima→manejo→histórico) e severidade. Determinístico."""
    return sorted(
        cards,
        key=lambda c: (_SOURCE_RANK.get(c.source, 9), _SEVERITY_RANK.get(c.severity, 9)),
    )


def _conf(value: str) -> str:
    return _CONFIDENCE_MAP.get(value, "moderada")


# -- construtores a partir das fontes existentes ----------------------------

# Pergunta do produtor por tipo de alerta de clima.
_CLIMA_DECISION = {
    "geada": "Preciso proteger a lavoura do frio nesses dias?",
    "veranico": "Vem estiagem — devo ajustar manejo/irrigação?",
    "chuva_intensa": "Chuva forte à vista — adio pulverização/colheita?",
    "janela_pulverizacao": "Tenho janela para pulverizar essa semana?",
}


def from_weather_alert(alert: dict) -> DecisionCard:
    """Mapeia um alerta de clima (services/weather) para um Cartão de Decisão."""
    code = alert["code"]
    why = [
        Evidence(label=str(k), detail=str(v))
        for k, v in (alert.get("evidence") or {}).items()
    ]
    return DecisionCard(
        id=f"clima_{code}",
        source=SOURCE_CLIMA,
        decision=_CLIMA_DECISION.get(code, alert["title"]),
        recommendation=alert["title"] + " — " + alert["detail"],
        confidence=_conf(alert.get("confidence", "moderada")),
        horizon=f"{alert['starts_on']} a {alert['ends_on']}",
        disclaimer="Previsão do tempo erra; comunicada com probabilidade/confiança.",
        effect=None,  # alerta de clima não tem efeito numérico direto em sc/ha
        why=why,
        severity=alert.get("severity", "info"),
    )


# Bandas de incerteza do efeito por confiança do fator (fração do ponto).
_EFFECT_BAND = {"alta": 0.20, "moderada": 0.35, "baixa": 0.50}


def from_economic_recommendation(rec: dict) -> DecisionCard:
    """Mapeia uma recomendação econômica (ganho líquido R$/ha) para um cartão.

    O efeito vem **sempre com intervalo**: o ponto é o valor estimado e a banda
    reflete a (in)certeza agronômica do fator.
    """
    conf = _conf(rec.get("confidence", "moderada"))
    band = _EFFECT_BAND[conf]
    gain_sc = rec["gain_sc_ha"]
    net = rec["net_gain_rs_ha"]
    yield_gain_rs = rec["yield_gain_rs_ha"]
    # banda do líquido proporcional ao ganho bruto (o custo é mais determinístico)
    half = abs(yield_gain_rs) * band
    return DecisionCard(
        id=f"manejo_{rec['key']}",
        source=SOURCE_MANEJO,
        decision=f"{rec['question']}: vale agir essa safra?",
        recommendation=f"{rec['current_label']} → {rec['target_label']}",
        confidence=conf,
        horizon="safra",
        disclaimer="Estimativa agronômica (efeito médio), não calibrada ao seu "
                   "talhão; confirme com seu agrônomo.",
        effect=DecisionEffect(
            basis="vs. manter o manejo atual",
            yield_sc_ha=(round(gain_sc * (1 - band), 1), gain_sc, round(gain_sc * (1 + band), 1)),
            profit_brl_ha=(round(net - half, 2), net, round(net + half, 2)),
        ),
        why=[Evidence(label="Por que pesa", detail=rec["rationale"])],
        severity="atenção" if net > 0 else "info",
    )


# Pergunta do produtor por flag histórica de atenção.
_FLAG_DECISION = {
    "custo_ha_alto": "Meu custo/ha está acima do esperado — onde cortar?",
    "abaixo_da_meta": "Produtividade abaixo da meta — o que revisar?",
    "orcamento_estourado": "Orçamento estourado — revejo o plano?",
    "orcamento_quase_esgotado": "Orçamento quase no limite — priorizo gastos?",
    "abaixo_da_regiao": "Talhão abaixo da média regional — investigar?",
    "instavel": "Produtividade instável nesse talhão — por quê?",
}


def from_attention_flag(field_name: str, flag: dict) -> DecisionCard:
    """Mapeia uma flag histórica de atenção (services/decisions) para um cartão."""
    code = flag["code"]
    why = [
        Evidence(label=str(k), detail=str(v))
        for k, v in (flag.get("evidence") or {}).items()
    ]
    return DecisionCard(
        id=f"historico_{code}_{field_name}",
        source=SOURCE_HISTORICO,
        decision=_FLAG_DECISION.get(code, flag["title"]),
        recommendation=f"{field_name}: {flag['detail']}",
        confidence=_conf(flag.get("confidence", "moderada")),
        horizon="histórico",
        disclaimer="Baseado em histórico e contabilidade da safra, não em condição "
                   "viva do talhão.",
        effect=None,
        why=why,
        severity=flag.get("severity", "info"),
    )
