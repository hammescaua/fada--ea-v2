"""Perfil Agronômico FADA — matriz padronizada de fatores que movem a produtividade.

Terceiro nível de personalização (ADR-0022): funciona **no dia 1**, sem histórico.
Captura, por um questionário padronizado, os fatores agronômicos do talhão e os
converte num **ajuste transparente** sobre a produtividade regional — fator a fator,
cada um com efeito (%), justificativa e fonte. Estilo "sem score mágico": o ajuste
é a soma auditável de efeitos nomeados, não uma caixa-preta.

Convenção de referência: o modelo regional reflete a **fazenda típica** do município
(manejo/solo médios). Por isso o nível "adequado/típico" tem efeito 0; desvios para
melhor/pior ajustam para cima/baixo. Efeitos são **estimativas agronômicas**
(Embrapa Soja / CQFS-RS-SC / literatura), conservadoras — não calibração local.

Puro e determinístico. ``math`` apenas.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Limites do multiplicador agregado: evita compor efeitos a valores absurdos.
MIN_MULTIPLIER = 0.50
MAX_MULTIPLIER = 1.25
SRC = "Embrapa Soja; CQFS-RS/SC; literatura agronômica"


@dataclass(frozen=True)
class FactorOption:
    effect: float       # efeito relativo (fração; ex.: -0.08 = -8%)
    label: str          # rótulo legível da opção escolhida


@dataclass(frozen=True)
class Factor:
    key: str
    question: str
    options: dict[str, FactorOption]
    rationale: str
    confidence: str     # "alta" | "média" | "baixa"


# --- Matriz de fatores (o "método padronizado" do FADA) --------------------
# Efeitos relativos à fazenda típica do município (nível típico = 0).
def _f(key, question, rationale, confidence, options) -> Factor:
    return Factor(key, question, {k: FactorOption(e, lab) for k, (e, lab) in options.items()},
                  rationale, confidence)


FACTORS: dict[str, Factor] = {
    f.key: f for f in [
        _f("textura_solo", "Textura do solo", "Solo mais argiloso retém mais água e "
           "ampara veranicos; arenoso sofre mais em estiagem (sequeiro).", "média",
           {"argiloso": (0.03, "Argiloso"), "medio": (0.0, "Médio"),
            "arenoso": (-0.07, "Arenoso")}),
        _f("profundidade_solo", "Profundidade efetiva do solo", "Solo profundo guarda "
           "mais água disponível para a fase reprodutiva.", "média",
           {"profundo": (0.02, "Profundo"), "medio": (0.0, "Médio"),
            "raso": (-0.06, "Raso")}),
        _f("drenagem", "Drenagem do talhão", "Drenagem ruim causa hipoxia e perdas em "
           "anos chuvosos.", "média",
           {"boa": (0.0, "Boa"), "imperfeita": (-0.04, "Imperfeita"),
            "ma": (-0.10, "Má")}),
        _f("fertilidade_p", "Fósforo (P) na análise de solo", "P é limitante frequente; "
           "classes baixas reduzem o teto produtivo (CQFS).", "alta",
           {"muito_alto": (0.02, "Muito alto"), "alto": (0.0, "Alto"),
            "medio": (-0.03, "Médio"), "baixo": (-0.09, "Baixo")}),
        _f("fertilidade_k", "Potássio (K) na análise de solo", "K afeta enchimento de "
           "grãos e tolerância a estresse.", "alta",
           {"muito_alto": (0.01, "Muito alto"), "alto": (0.0, "Alto"),
            "medio": (-0.02, "Médio"), "baixo": (-0.07, "Baixo")}),
        _f("acidez_corrigida", "Correção de acidez (calagem)", "Saturação por Al e pH "
           "baixo limitam raiz e nodulação; calagem em dia é base.", "alta",
           {"recente": (0.0, "Corrigida (recente)"), "antiga": (-0.03, "Antiga"),
            "nao": (-0.10, "Não corrigida")}),
        _f("materia_organica", "Matéria orgânica", "MO melhora água, CTC e biologia "
           "do solo.", "baixa",
           {"alta": (0.02, "Alta"), "media": (0.0, "Média"), "baixa": (-0.03, "Baixa")}),
        _f("cultivar", "Cultivar / potencial genético", "Cultivares modernas de alto "
           "potencial e sanidade superam materiais antigos.", "média",
           {"moderna": (0.04, "Moderna, alto potencial"),
            "intermediaria": (0.0, "Intermediária"), "antiga": (-0.08, "Antiga")}),
        _f("janela_plantio", "Data de plantio vs janela ZARC", "Plantio na janela ótima "
           "posiciona a fase reprodutiva no menor risco hídrico.", "alta",
           {"otima": (0.0, "Janela ótima"), "aceitavel": (-0.03, "Aceitável"),
            "fora": (-0.12, "Fora do ZARC")}),
        _f("populacao", "População de plantas", "Estande adequado define o teto; falhas "
           "reduzem, excesso acama.", "média",
           {"adequada": (0.0, "Adequada"), "baixa": (-0.05, "Baixa"),
            "alta_demais": (-0.02, "Alta demais")}),
        _f("inoculacao", "Inoculação (rizóbio)", "A FBN supre o N da soja; sem "
           "inoculação há limitação de nitrogênio.", "alta",
           {"sim": (0.0, "Sim"), "nao": (-0.08, "Não")}),
        _f("tratamento_semente", "Tratamento de sementes", "Protege o estande inicial "
           "contra pragas/doenças de solo.", "baixa",
           {"sim": (0.0, "Sim"), "nao": (-0.02, "Não")}),
        _f("fungicida", "Programa de fungicida (ferrugem)", "A ferrugem asiática pode "
           "cortar fortemente a produtividade sem controle adequado.", "alta",
           {"completo": (0.0, "Completo"), "parcial": (-0.08, "Parcial"),
            "nenhum": (-0.22, "Nenhum")}),
        _f("manejo_pragas", "Manejo de pragas (MIP)", "Percevejos/lagartas reduzem "
           "grãos e qualidade se mal manejados.", "média",
           {"adequado": (0.0, "Adequado"), "parcial": (-0.05, "Parcial"),
            "deficiente": (-0.15, "Deficiente")}),
        _f("manejo_daninhas", "Manejo de plantas daninhas", "Matocompetição (ex.: "
           "buva, capim-amargoso) rouba água, luz e nutrientes.", "média",
           {"adequado": (0.0, "Adequado"), "parcial": (-0.04, "Parcial"),
            "deficiente": (-0.12, "Deficiente")}),
        _f("rotacao", "Rotação de culturas / antecessor", "Rotação com milho/braquiária "
           "melhora solo e quebra ciclos; monocultura de soja piora.", "média",
           {"rotacao_boa": (0.03, "Rotação (milho/braquiária)"),
            "pousio": (0.0, "Pousio/cobertura"),
            "monocultura": (-0.05, "Soja sobre soja")}),
        _f("plantio_direto", "Sistema de plantio", "PD consolidado com palhada melhora "
           "água e estrutura; convencional expõe a erosão.", "baixa",
           {"pd_consolidado": (0.02, "PD consolidado"),
            "pd_recente": (0.0, "PD recente"), "convencional": (-0.03, "Convencional")}),
        _f("compactacao", "Compactação do solo", "Camada compactada limita raiz e "
           "infiltração, agravando veranicos.", "média",
           {"ausente": (0.0, "Ausente"), "presente": (-0.06, "Presente")}),
        _f("nematoides", "Pressão de nematoides", "Nematoides (ex.: cisto, galhas) "
           "reduzem absorção de água/nutrientes.", "média",
           {"baixa": (0.0, "Baixa"), "media": (-0.06, "Média"), "alta": (-0.15, "Alta")}),
        _f("irrigacao", "Irrigação", "Irrigação remove a principal limitação (água) do "
           "sequeiro, sobretudo em anos secos.", "média",
           {"sequeiro": (0.0, "Sequeiro"), "irrigado": (0.10, "Irrigado")}),
    ]
}


@dataclass(frozen=True)
class AppliedFactor:
    key: str
    question: str
    option_label: str
    effect_pct: float       # em %, já * 100 e arredondado
    rationale: str
    confidence: str


@dataclass(frozen=True)
class AdjustmentResult:
    applied: list[AppliedFactor]
    multiplier: float           # multiplicador agregado já limitado
    raw_multiplier: float       # antes do clamp (transparência)
    clamped: bool
    total_effect_pct: float     # (multiplier - 1) * 100
    n_factors: int


class UnknownFactor(ValueError):
    pass


def planting_window_class(within_zarc: bool, risk_level: int | None) -> str:
    """Mapeia a avaliação ZARC de uma data para o fator 'janela_plantio'.

    Dentro ao risco 20% (mais conservador) = ótima; dentro a 30/40% = aceitável;
    fora da janela indicada = fora.
    """
    if not within_zarc or risk_level is None:
        return "fora"
    if risk_level <= 20:
        return "otima"
    return "aceitavel"


def validate_profile(profile: dict[str, str]) -> None:
    """Garante que chaves e valores existem na matriz (entrada padronizada)."""
    for key, value in profile.items():
        factor = FACTORS.get(key)
        if factor is None:
            raise UnknownFactor(f"fator desconhecido: {key}")
        if value not in factor.options:
            raise UnknownFactor(f"opção '{value}' inválida para '{key}'")


def compute_adjustment(profile: dict[str, str]) -> AdjustmentResult:
    """Converte o perfil em ajuste multiplicativo transparente. Determinístico.

    Fatores ausentes no perfil são ignorados (assume-se o nível típico = 0): o
    produtor responde só o que sabe, sem penalização por omissão.
    """
    validate_profile(profile)
    applied: list[AppliedFactor] = []
    raw = 1.0
    for key, value in profile.items():
        factor = FACTORS[key]
        opt = factor.options[value]
        raw *= 1.0 + opt.effect
        if opt.effect != 0.0:
            applied.append(AppliedFactor(
                key=key, question=factor.question, option_label=opt.label,
                effect_pct=round(opt.effect * 100, 1), rationale=factor.rationale,
                confidence=factor.confidence,
            ))
    multiplier = max(MIN_MULTIPLIER, min(MAX_MULTIPLIER, raw))
    # Maior impacto primeiro (ajuda o produtor a priorizar).
    applied.sort(key=lambda a: a.effect_pct)
    return AdjustmentResult(
        applied=applied,
        multiplier=round(multiplier, 4),
        raw_multiplier=round(raw, 4),
        clamped=not math.isclose(multiplier, raw),
        total_effect_pct=round((multiplier - 1.0) * 100, 1),
        n_factors=len(applied),
    )
