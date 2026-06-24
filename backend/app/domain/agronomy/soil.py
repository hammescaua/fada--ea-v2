"""Interpretação de análise de solo → classes CQFS-RS/SC → fatores do perfil.

Reduz o atrito da coleta (ADR-0022): o produtor digita os valores do laudo e o
FADA classifica (baixo/médio/alto…) pelos critérios da CQFS-RS/SC (2016),
pré-preenchendo os fatores de fertilidade do Perfil Agronômico.

Honestidade (pilar do projeto): a classificação é **orientativa**, ancorada no
**nível crítico** (teor que separa resposta provável a adubação de suficiência) —
os valores estão em constantes auditáveis, com disclaimer para conferência
agronômica. Puro e determinístico.

Fontes: CQFS-RS/SC (2016) — Manual de Calagem e Adubação para RS e SC.
"""

from __future__ import annotations

from dataclasses import dataclass

# Teor crítico de P (Mehlich-1, mg/dm³) por classe de argila — CQFS-RS/SC 2016.
# Solos mais arenosos têm crítico mais alto (extração relativa maior).
def _p_critical(clay_pct: float | None) -> float:
    if clay_pct is None:
        return 6.0  # default: classe 3 (21–40% argila), a mais comum
    if clay_pct > 60:
        return 3.0
    if clay_pct > 40:
        return 4.0
    if clay_pct > 20:
        return 6.0
    return 9.0


# Teor crítico de K (Mehlich-1, mg/dm³) por faixa de CTC (cmolc/dm³) — CQFS.
def _k_critical(ctc: float | None) -> float:
    if ctc is None:
        return 60.0  # default: CTC média (7,6–15)
    if ctc <= 7.5:
        return 40.0
    if ctc <= 15.0:
        return 60.0
    return 80.0


def _class_vs_critical(value: float, critical: float) -> str:
    """Mapeia um teor em classe do perfil, ancorado no nível crítico (CL).

    < 0,5·CL → baixo · 0,5–1·CL → médio · 1–2·CL → alto · ≥2·CL → muito_alto.
    (Simplificação documentada das faixas CQFS, ancorada no CL canônico.)
    """
    if value < 0.5 * critical:
        return "baixo"
    if value < critical:
        return "medio"
    if value < 2.0 * critical:
        return "alto"
    return "muito_alto"


def classify_phosphorus(p_mehlich: float, clay_pct: float | None = None) -> str:
    return _class_vs_critical(p_mehlich, _p_critical(clay_pct))


def classify_potassium(k_mehlich: float, ctc: float | None = None) -> str:
    return _class_vs_critical(k_mehlich, _k_critical(ctc))


def classify_organic_matter(om_pct: float) -> str:
    # CQFS: Baixo ≤ 2,5% · Médio 2,6–5,0% · Alto > 5,0%.
    if om_pct <= 2.5:
        return "baixa"
    if om_pct <= 5.0:
        return "media"
    return "alta"


def classify_acidity(ph_water: float | None, al_saturation_pct: float | None) -> str | None:
    """Status de correção da acidez a partir de pH(H2O) e saturação por Al (m%).

    Tolerância da soja ~20% de m. Bem corrigido (recente) exige pH≥5,5 e m baixo;
    sinais de acidez levam a 'nao' (precisa calagem)."""
    if ph_water is None and al_saturation_pct is None:
        return None
    ph = ph_water if ph_water is not None else 5.5
    m = al_saturation_pct if al_saturation_pct is not None else 0.0
    if ph < 5.0 or m > 20.0:
        return "nao"
    if ph < 5.5 or m > 10.0:
        return "antiga"
    return "recente"


@dataclass(frozen=True)
class SoilAnalysis:
    p_mehlich: float | None = None       # mg/dm³
    k_mehlich: float | None = None       # mg/dm³
    clay_pct: float | None = None        # % (para classe de P)
    ctc: float | None = None             # cmolc/dm³ (para classe de K)
    ph_water: float | None = None
    al_saturation_pct: float | None = None   # m%
    organic_matter_pct: float | None = None  # %


def classify_soil_analysis(a: SoilAnalysis) -> tuple[dict[str, str], list[dict]]:
    """Retorna (fragmento_de_perfil, explicações). Só preenche o que os dados permitem."""
    profile: dict[str, str] = {}
    notes: list[dict] = []

    def add(factor: str, value: str, basis: str) -> None:
        profile[factor] = value
        notes.append({"factor": factor, "value": value, "basis": basis})

    if a.p_mehlich is not None:
        add("fertilidade_p", classify_phosphorus(a.p_mehlich, a.clay_pct),
            f"P {a.p_mehlich} mg/dm³ vs crítico {_p_critical(a.clay_pct)} "
            f"(argila {a.clay_pct if a.clay_pct is not None else 'n/d'}%)")
    if a.k_mehlich is not None:
        add("fertilidade_k", classify_potassium(a.k_mehlich, a.ctc),
            f"K {a.k_mehlich} mg/dm³ vs crítico {_k_critical(a.ctc)} "
            f"(CTC {a.ctc if a.ctc is not None else 'n/d'})")
    if a.organic_matter_pct is not None:
        add("materia_organica", classify_organic_matter(a.organic_matter_pct),
            f"MO {a.organic_matter_pct}%")
    acidity = classify_acidity(a.ph_water, a.al_saturation_pct)
    if acidity is not None:
        add("acidez_corrigida", acidity,
            f"pH {a.ph_water if a.ph_water is not None else 'n/d'}, "
            f"m {a.al_saturation_pct if a.al_saturation_pct is not None else 'n/d'}%")
    return profile, notes
