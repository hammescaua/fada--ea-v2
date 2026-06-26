"""Leitura da safra em linguagem natural (determinística, fundamentada)."""

from __future__ import annotations

from app.domain.narrative import narrate_brief


def _brief(**over) -> dict:
    base = {
        "municipality": "Horizontina", "season": "2026/27",
        "yield": {
            "expected_sc_ha": 37.1, "interval_sc_ha": [25.0, 49.0],
            "scenarios": [
                {"name": "pessimista", "yield_sc_ha": 25.5},
                {"name": "normal", "yield_sc_ha": 37.1},
                {"name": "otimista", "yield_sc_ha": 42.1},
            ],
            "risks": [], "n_years": 40,
            "personalized": True,
            "adjustment": {"total_effect_pct": -27.5, "factors": [
                {"question": "Programa de fungicida (ferrugem)"},
                {"question": "Textura do solo"},
            ]},
        },
        "planting": {
            "zarc": {"windows_by_risk": {"20": [{"start": "10-01", "end": "01-31"}]}},
            "best_date": {"planting_date": "30/11/2026"},
        },
        "price": {"price_per_bag": 133.5, "source": "CEPEA/ESALQ"},
        "cost": {"cot_per_ha": 5830.0, "safra": "2025/26"},
        "margin": {
            "cost_per_ha_cot": 5830.0,
            "break_even_yield_sc_ha": {"coe": 32.2, "cot": 40.2, "ct": 45.9},
            "expected": {"profit_per_ha": -411.0, "margin_pct": -8.3},
        },
        "recommendations": [{
            "question": "Programa de fungicida (ferrugem)", "current_label": "Nenhum",
            "target_label": "Completo", "net_gain_rs_ha": 890.0,
        }],
    }
    base.update(over)
    return base


def test_narrative_is_grounded_and_plain():
    paras = narrate_brief(_brief())
    text = " ".join(paras)
    assert len(paras) >= 3
    assert "37" in text and "Horizontina" in text          # produtividade
    assert "veranico" in text.lower()                       # risco do ano
    assert "ponto de equilíbrio" in text.lower()            # economia
    assert "fungicida" in text.lower()                      # ação de maior retorno
    assert "10-01" in text                                  # janela ZARC
    assert "probabilística" in text.lower()                 # ressalva honesta


def test_narrative_handles_missing_margin():
    paras = narrate_brief(_brief(margin=None, price=None))
    text = " ".join(paras).lower()
    assert "falta preço" in text


def test_narrative_regional_when_not_personalized():
    b = _brief()
    b["yield"]["personalized"] = False
    b["yield"]["adjustment"] = None
    paras = narrate_brief(b)
    assert paras  # não quebra sem personalização
