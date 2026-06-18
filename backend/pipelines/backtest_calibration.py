"""Backtest de calibração (offline) — mede a honestidade dos intervalos.

Leave-one-year-out sobre os 787 dados reais (IBGE × clima). Para cada ano-alvo:
- Regional: modelo treinado nos demais anos prevê cada município (OOF). O intervalo
  vem dos quantis dos resíduos OOF dos OUTROS anos (estilo conformal, sem vazar o ano).
- Personalizado: cada MUNICÍPIO é tratado como uma "fazenda" (proxy honesto enquanto
  não há dado de fazenda — ADR-0013). O bias do município é estimado nos demais anos e
  aplicado via o mesmo encolhimento do adaptive (reuso de domain.adaptive.personalize).

Produz data/models/calibration_report.json (regional + personalizado) e loga no MLflow.
NÃO altera nenhuma previsão. Uso: python -m pipelines.backtest_calibration
"""

from __future__ import annotations

import json

import mlflow
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from app.core.config import settings
from app.domain.adaptive import ShrinkagePrior, personalize, shrinkage_weight
from app.domain.calibration import build_report, personalized_halfwidth
from app.domain.features import SOYBEAN_FEATURE_NAMES
from app.domain.units import kg_per_ha_to_bags_per_ha

MODEL_FEATURES = [*SOYBEAN_FEATURE_NAMES, "harvest_year"]
# Níveis: canônicos (50/80/90/95) + curva de confiabilidade.
LEVELS = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
QUANTILE_TAUS = [0.1, 0.5, 0.9]


def _oof_predictions(df: pd.DataFrame) -> np.ndarray:
    """Predições leave-one-year-out (sc/ha) para cada linha."""
    X = df[MODEL_FEATURES].to_numpy(float)
    y = df["yield_kg_ha"].to_numpy(float)
    years = df["harvest_year"].to_numpy()
    oof = np.zeros(len(df))
    for t in np.unique(years):
        tr, te = years != t, years == t
        scaler = StandardScaler().fit(X[tr])
        model = Ridge(alpha=10.0).fit(scaler.transform(X[tr]), y[tr])
        oof[te] = model.predict(scaler.transform(X[te]))
    return np.array([kg_per_ha_to_bags_per_ha(v) for v in oof])


def _quantile(residuals: np.ndarray, level: float, side: str) -> float:
    p = (1 - level) / 2 * 100 if side == "lo" else (1 - (1 - level) / 2) * 100
    return float(np.percentile(residuals, p))


def backtest() -> dict:
    df = pd.read_csv(settings.data_dir / "features" / "soybean_tres_passos.csv").copy()
    df["actual_sc_ha"] = df["yield_kg_ha"].apply(kg_per_ha_to_bags_per_ha)
    df["oof_sc_ha"] = _oof_predictions(df)
    df["residual"] = df["actual_sc_ha"] - df["oof_sc_ha"]
    df["rel_residual"] = df["residual"] / df["oof_sc_ha"]
    years = df["harvest_year"].to_numpy()
    prior = ShrinkagePrior()

    actuals = df["actual_sc_ha"].tolist()
    reg_points = df["oof_sc_ha"].tolist()
    reg_levels: dict[float, tuple[list, list]] = {lv: ([], []) for lv in LEVELS}
    per_points: list[float] = []
    per_levels: dict[float, tuple[list, list]] = {lv: ([], []) for lv in LEVELS}
    reg_q: dict[float, list] = {t: [] for t in QUANTILE_TAUS}
    per_q: dict[float, list] = {t: [] for t in QUANTILE_TAUS}

    for idx, row in df.iterrows():
        t = row["harvest_year"]
        point = row["oof_sc_ha"]
        # Intervalos regionais: quantis dos resíduos OOF dos OUTROS anos (sem vazar t).
        res_other = df.loc[years != t, "residual"].to_numpy()
        for lv in LEVELS:
            reg_levels[lv][0].append(round(point + _quantile(res_other, lv, "lo"), 2))
            reg_levels[lv][1].append(round(point + _quantile(res_other, lv, "hi"), 2))
        for tau in QUANTILE_TAUS:
            reg_q[tau].append(round(point + float(np.percentile(res_other, tau * 100)), 2))

        # Personalizado: bias do município nos OUTROS anos -> encolhimento.
        mask = (df["municipality_code"] == row["municipality_code"]) & (years != t)
        muni_rel = df.loc[mask, "rel_residual"].to_numpy()
        n = len(muni_rel)
        obs_bias = float(muni_rel.mean()) if n else 0.0
        var_rel = float(muni_rel.var(ddof=1)) if n >= 2 else 0.0
        # IC80 regional para alimentar o personalize (mesma matemática do adaptive).
        reg_i80 = (reg_levels[0.8][0][-1], reg_levels[0.8][1][-1])
        pred = personalize(point, reg_i80, {}, n, obs_bias, var_rel, prior)
        per_points.append(pred.personalized_point_sc_ha)
        # Reaplica a meia-largura personalizada a cada nível (regional widening por SE_bias).
        _, se_bias = shrinkage_weight(n, var_rel, prior)
        ppoint = pred.personalized_point_sc_ha
        for lv in LEVELS:
            h_reg = (reg_levels[lv][1][-1] - reg_levels[lv][0][-1]) / 2
            h = personalized_halfwidth(h_reg, point, se_bias)
            per_levels[lv][0].append(round(ppoint - h, 2))
            per_levels[lv][1].append(round(ppoint + h, 2))
        for tau in QUANTILE_TAUS:
            h_reg = (reg_levels[0.8][1][-1] - reg_levels[0.8][0][-1]) / 2 or 1.0
            # quantil personalizado: desloca pelo bias (mantém forma)
            per_q[tau].append(round(ppoint + (reg_q[tau][-1] - point), 2))

    regional = build_report("Regional", actuals, reg_points, reg_levels, reg_q)
    personalized = build_report("Personalizado", actuals, per_points, per_levels, per_q)
    out = {
        "method": "leave-one-year-out",
        "ground_truth": "IBGE/PAM (municípios como proxy de fazenda no personalizado)",
        "note": "Calibração personalizada usa municípios como proxy enquanto não há dado de fazenda.",
        "regional": regional.to_dict(),
        "personalized": personalized.to_dict(),
    }
    path = settings.model_path.parent / "calibration_report.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    mlflow.set_tracking_uri(f"sqlite:///{settings.data_dir.parent / 'mlflow.db'}")
    mlflow.set_experiment("calibration_backtest")
    with mlflow.start_run(run_name="loyo"):
        for rep in (regional, personalized):
            tag = rep.label.lower()
            mlflow.log_metrics({
                f"{tag}_coverage_80": rep.coverage_80, f"{tag}_coverage_90": rep.coverage_90,
                f"{tag}_mae": rep.mae, f"{tag}_rmse": rep.rmse, f"{tag}_bias": rep.bias,
                f"{tag}_mean_width": rep.mean_width, f"{tag}_pinball_mean": rep.pinball["mean"],
            })

    print(regional.interpretation)
    print(personalized.interpretation)
    print(f"-> {path}")
    return out


if __name__ == "__main__":
    backtest()
