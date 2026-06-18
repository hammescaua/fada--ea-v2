"""Treino do baseline regional de produtividade de soja.

Compara Ridge, Random Forest e XGBoost sob **validação temporal honesta**
(leave-one-year-out): cada ano é previsto por um modelo treinado nos demais anos —
exatamente o caso de uso (generalizar para um ano climático não visto). Sem CV
aleatório, que vazaria o futuro no passado.

O vencedor é serializado como artefato JSON inspecionável (ADR-0006). Métricas e
parâmetros são logados no MLflow.

Uso:  python -m pipelines.train
"""

from __future__ import annotations

import json
from datetime import datetime

import mlflow
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from app.core.config import settings
from app.domain.features import SOYBEAN_FEATURE_NAMES
from app.domain.units import kg_per_ha_to_bags_per_ha

MODEL_FEATURES = [*SOYBEAN_FEATURE_NAMES, "harvest_year"]
TARGET = "yield_kg_ha"
PERCENTILES = [10, 25, 50, 75, 90]


def _candidates() -> dict[str, Pipeline]:
    return {
        "ridge": Pipeline([("sc", StandardScaler()), ("m", Ridge(alpha=10.0))]),
        "random_forest": Pipeline(
            [("m", RandomForestRegressor(n_estimators=300, min_samples_leaf=5, random_state=0))]
        ),
        "xgboost": Pipeline(
            [(
                "m",
                XGBRegressor(
                    n_estimators=300,
                    max_depth=3,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=0,
                ),
            )]
        ),
    }


def _cv_oof(model: Pipeline, X: np.ndarray, y: np.ndarray, groups: np.ndarray) -> np.ndarray:
    """Predições out-of-fold por leave-one-year-out."""
    oof = np.zeros_like(y, dtype=float)
    logo = LeaveOneGroupOut()
    for tr, te in logo.split(X, y, groups):
        m = model
        m.fit(X[tr], y[tr])
        oof[te] = m.predict(X[te])
    return oof


def _metrics_scha(y: np.ndarray, yhat: np.ndarray) -> dict[str, float]:
    """Erros reportados na unidade do agricultor (sc/ha)."""
    y_s = np.array([kg_per_ha_to_bags_per_ha(v) for v in y])
    yhat_s = np.array([kg_per_ha_to_bags_per_ha(v) for v in yhat])
    return {
        "mae_scha": float(mean_absolute_error(y_s, yhat_s)),
        "rmse_scha": float(np.sqrt(mean_squared_error(y_s, yhat_s))),
    }


def _climatology(df: pd.DataFrame) -> dict:
    """Percentis das features climáticas por município e regional (para cenários)."""
    feats = SOYBEAN_FEATURE_NAMES

    def pct(sub: pd.DataFrame) -> dict:
        return {
            f: {f"p{p}": float(np.percentile(sub[f], p)) for p in PERCENTILES} for f in feats
        }

    by_mun = {}
    for code, sub in df.groupby("municipality_code"):
        by_mun[str(int(code))] = {
            "name": sub["municipality_name"].iloc[0],
            "n_years": int(len(sub)),
            "yield_kg_ha": {f"p{p}": float(np.percentile(sub[TARGET], p)) for p in PERCENTILES},
            "features": pct(sub),
        }
    return {"by_municipality": by_mun, "regional": pct(df)}


def train() -> dict:
    df = pd.read_csv(settings.data_dir / "features" / "soybean_tres_passos.csv")
    X = df[MODEL_FEATURES].to_numpy(dtype=float)
    y = df[TARGET].to_numpy(dtype=float)
    groups = df["harvest_year"].to_numpy()

    mlflow.set_tracking_uri(f"sqlite:///{settings.data_dir.parent / 'mlflow.db'}")
    mlflow.set_experiment("soybean_regional_baseline")

    results = {}
    for name, model in _candidates().items():
        with mlflow.start_run(run_name=name):
            oof = _cv_oof(model, X, y, groups)
            m = _metrics_scha(y, oof)
            mlflow.log_params({"model": name, "cv": "leave-one-year-out", "n": len(df)})
            mlflow.log_metrics(m)
            results[name] = m
            print(f"{name:14s}  MAE={m['mae_scha']:.2f} sc/ha  RMSE={m['rmse_scha']:.2f} sc/ha")

    # Vencedor por MAE (menor erro). Em empate, prefere-se o mais simples (ridge).
    winner = min(results, key=lambda k: (results[k]["mae_scha"], k != "ridge"))
    print(f"\nVencedor: {winner}")

    artifact = _build_artifact(df, X, y, groups, winner, results)
    settings.model_path.parent.mkdir(parents=True, exist_ok=True)
    settings.model_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2))
    print(f"Artefato -> {settings.model_path}")
    return artifact


def _build_artifact(df, X, y, groups, winner, results) -> dict:
    """Serializa o modelo linear (interpretável) + climatologia para cenários.

    Mesmo quando um modelo de árvore vence no CV, o artefato de produção é o linear:
    com este n e sinal predominantemente linear, é tão bom quanto e muito mais
    defensável/auditável (ADR-0006). A comparação fica registrada no MLflow.
    """
    scaler = StandardScaler().fit(X)
    ridge = Ridge(alpha=10.0).fit(scaler.transform(X), y)

    # Resíduos out-of-fold do ridge -> intervalo de predição honesto.
    oof = _cv_oof(_candidates()["ridge"], X, y, groups)
    residuals_scha = np.array(
        [kg_per_ha_to_bags_per_ha(a) - kg_per_ha_to_bags_per_ha(b) for a, b in zip(y, oof)]
    )

    return {
        "model_type": "ridge_linear",
        "target": "yield_kg_ha",
        "crop": "soja",
        "region": "microrregiao_tres_passos_rs",
        "feature_names": MODEL_FEATURES,
        "standardization": {
            "mean": scaler.mean_.tolist(),
            "scale": scaler.scale_.tolist(),
        },
        "coefficients": ridge.coef_.tolist(),
        "intercept": float(ridge.intercept_),
        "residual_scha_quantiles": {
            f"p{p}": float(np.percentile(residuals_scha, p)) for p in [5, 10, 50, 90, 95]
        },
        "climatology": _climatology(df),
        "metadata": {
            "trained_at": datetime.utcnow().isoformat() + "Z",
            "n_rows": int(len(df)),
            "n_municipalities": int(df["municipality_code"].nunique()),
            "harvest_years": [int(df["harvest_year"].min()), int(df["harvest_year"].max())],
            "cv": "leave-one-year-out",
            "cv_metrics_scha": results,
            "production_model": "ridge_linear",
            "cv_winner": winner,
            "ground_truth": "IBGE/PAM tabela 1612",
            "weather_sources": ["open-meteo-era5", "nasa-power"],
        },
    }


if __name__ == "__main__":
    train()
