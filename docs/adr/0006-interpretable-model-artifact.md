# ADR-0006 — Artefato de modelo interpretável (JSON) em produção

**Status:** Aceito · **Data:** 2026-06-17

## Contexto
A comparação leave-one-year-out deu erros **estatisticamente indistinguíveis** entre
os três candidatos (MAE em sc/ha):

| Modelo | MAE | RMSE |
|---|---|---|
| Ridge (linear) | 6.96 | 8.85 |
| Random Forest | 7.35 | 9.60 |
| XGBoost | 6.86 | 8.79 |

XGBoost vence por 0,1 sc/ha — diferença sem significância prática.

## Decisão
O **modelo de produção é o Ridge linear**, serializado como **JSON inspecionável**
(coeficientes + padronização + quantis de resíduo + climatologia para cenários).

## Justificativa
- Com sinal predominantemente linear e ganho nulo das árvores, o linear é tão bom e
  **muito mais defensável, auditável e barato** (inferência só com numpy, sem
  sklearn/xgboost no runtime).
- JSON > pickle: reprodutível, versionável, sem risco de desserialização, legível por
  humanos. O agricultor pode, em princípio, rastrear cada coeficiente.
- A comparação completa fica registrada no **MLflow**; a decisão é baseada em
  evidência, não preferência.

## Consequências
- (+) Runtime da API leve e seguro; artefato pequeno e commitável.
- (+) Transparência total dos drivers de cada estimativa.
- (−) Se, com mais dados (V2), as árvores passarem a vencer com folga, revisar este
  ADR e empacotar o modelo via joblib + serviço de inferência dedicado.
