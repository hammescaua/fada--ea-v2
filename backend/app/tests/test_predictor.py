"""Testa a inferência e a construção de cenários com um artefato controlado."""

from app.domain.yield_estimation import RegionalYieldModel


def _artifact() -> dict:
    feats = [
        "water_deficit_reproductive_mm",
        "dry_spell_longest_reproductive_days",
        "hot_days_reproductive",
        "precip_total_season_mm",
        "harvest_year",
    ]
    return {
        "feature_names": feats,
        "standardization": {"mean": [0, 0, 0, 0, 0], "scale": [1, 1, 1, 1, 1]},
        "coefficients": [-10.0, -1.0, -1.0, 0.5, 1.0],
        "intercept": 2000.0,
        "residual_scha_quantiles": {"p5": -15, "p10": -10, "p50": 0, "p90": 10, "p95": 15},
        "climatology": {
            "by_municipality": {
                "999": {
                    "name": "Teste",
                    "n_years": 30,
                    "yield_kg_ha": {"p10": 1200, "p50": 2000, "p90": 3200},
                    "features": {
                        "water_deficit_reproductive_mm": {"p10": 0, "p50": 50, "p90": 200},
                        "dry_spell_longest_reproductive_days": {"p10": 0, "p50": 5, "p90": 15},
                        "hot_days_reproductive": {"p10": 0, "p50": 2, "p90": 10},
                        "precip_total_season_mm": {"p10": 600, "p50": 900, "p90": 1400},
                    },
                }
            },
            "regional": {},
        },
    }


def test_predict_linear():
    m = RegionalYieldModel(_artifact())
    fv = {
        "water_deficit_reproductive_mm": 50,
        "dry_spell_longest_reproductive_days": 5,
        "hot_days_reproductive": 2,
        "precip_total_season_mm": 900,
        "harvest_year": 2027,
    }
    # 2000 -500 -5 -2 +450 +2027
    assert m.predict_kg_ha(fv) == 3970.0


def test_scenarios_ordered():
    m = RegionalYieldModel(_artifact())
    est = m.estimate(999, 2027)
    by = {s.name: s.yield_sc_ha for s in est.scenarios}
    assert by["pessimista"] < by["normal"] < by["otimista"]
    # intervalo de confiança em torno do normal
    assert est.interval_sc_ha[0] < est.point_sc_ha < est.interval_sc_ha[1]


def test_unknown_municipality_raises():
    m = RegionalYieldModel(_artifact())
    try:
        m.estimate(123, 2027)
        raise AssertionError("deveria ter levantado KeyError")
    except KeyError:
        pass
