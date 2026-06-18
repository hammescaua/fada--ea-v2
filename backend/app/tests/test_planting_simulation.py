"""Testa a agregação do backtest e a otimização robusta (domínio puro)."""

from app.domain.planting_date import optimize_planting_window, simulate_planting_date
from app.domain.yield_estimation import RegionalYieldModel


def _model() -> RegionalYieldModel:
    return RegionalYieldModel({
        "feature_names": [
            "water_deficit_reproductive_mm",
            "dry_spell_longest_reproductive_days",
            "hot_days_reproductive",
            "precip_total_season_mm",
            "harvest_year",
        ],
        "standardization": {"mean": [0, 0, 0, 0, 0], "scale": [1, 1, 1, 1, 1]},
        "coefficients": [-10.0, 0.0, 0.0, 0.0, 0.0],
        "intercept": 3000.0,
        "residual_scha_quantiles": {"p10": -8, "p50": 0, "p90": 8},
        "climatology": {"by_municipality": {}, "regional": {}},
    })


def _years(deficits: list[float]) -> list[dict]:
    return [
        {
            "water_deficit_reproductive_mm": d,
            "dry_spell_longest_reproductive_days": 5,
            "hot_days_reproductive": 2,
            "precip_total_season_mm": 800,
        }
        for d in deficits
    ]


def test_scenarios_ordered_and_score():
    m = _model()
    # déficit variando -> produtividade variando; mediana=déficit 50
    o = simulate_planting_date(m, _years([0, 25, 50, 75, 100]), 2027, "11-05", True)
    assert o.pessimista_sc_ha <= o.normal_sc_ha <= o.otimista_sc_ha
    # equivalente-certeza = mediana - 0.5*(mediana - P10) < mediana
    assert o.risk_score < o.normal_sc_ha


def test_optimization_prefers_robust_date_and_respects_zarc():
    m = _model()
    grid = {
        # data A: alta média mas grande downside (anos ruins severos)
        "11-05": _years([0, 0, 0, 200, 200]),
        # data B: média um pouco menor, porém estável (baixo downside)
        "11-10": _years([40, 45, 50, 55, 60]),
        # data fora do ZARC deve ser ignorada mesmo com bom score
        "01-05": _years([0, 0, 0, 0, 0]),
    }
    zarc = {"11-05": True, "11-10": True, "01-05": False}
    ranked = optimize_planting_window(m, grid, 2027, zarc, risk_aversion=0.5, top_n=5)
    dates = [o.planting_date for o in ranked]
    assert "01-05" not in dates  # ZARC exclui
    assert ranked[0].planting_date == "11-10"  # robustez vence
