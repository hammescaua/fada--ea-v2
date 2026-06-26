"""Leitura em linguagem natural da estimativa personalizada do talhão (puro)."""

from __future__ import annotations


def _n(v: float) -> str:
    return f"{v:.0f}" if abs(v - round(v)) < 0.05 else f"{v:.1f}"


def narrate_estimate(estimate: dict) -> str:
    """Uma frase clara sobre a previsão do talhão e o que mais a limita."""
    point = estimate["personalized"]["point_sc_ha"]
    eff = estimate["adjustment"]["total_effect_pct"]
    direction = "acima" if eff >= 0 else "abaixo"
    text = (
        f"Seu talhão tende a render cerca de {_n(point)} sc/ha — "
        f"{_n(abs(eff))}% {direction} da média da região."
    )
    note = estimate.get("water_sensitivity_note")
    if note:
        text += f" {note}"
    recs = estimate.get("recommendations") or []
    if recs and recs[0].get("gain_sc_ha", 0) > 0:
        top = recs[0]
        text += (
            f" O que mais vale corrigir é {top['question'].lower()} "
            f"(de {top['current_label'].lower()} para {top['target_label'].lower()}), "
            f"valendo cerca de +{_n(top['gain_sc_ha'])} sc/ha."
        )
    return text
