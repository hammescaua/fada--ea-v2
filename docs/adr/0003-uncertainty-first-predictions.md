# ADR-0003 — Predições com incerteza calibrada; baseline antes de deep learning

**Status:** Aceito · **Data:** 2026-06-16

## Contexto
O agricultor "quer respostas", não gráficos. A tentação é entregar um número único
e confiante de produtividade. Além disso, há disponibilidade limitada de dado de
verdade-terreno (rendimento por talhão), tornando modelos de alta capacidade
(LSTM/deep learning) inadequados no início.

## Decisão
1. **Toda saída numérica expõe incerteza:** `point_estimate` + `interval` +
   `scenarios` (pessimista/normal/otimista) + o **N de dados** que a sustenta.
2. **Baseline estatístico antes de ML pesado.** Começar com regressão sobre índices
   agroclimáticos (interpretável, defensável). Subir para gradient boosting
   (XGBoost/LightGBM/CatBoost) quando o volume de dado justificar, mantendo o
   baseline como *sanity check*. LSTM/Prophet só na V2+ se o dado justificar.
3. **Protocolo de validação:** backtest *walk-forward* por safra; métricas MAE/MAPE
   em sc/ha; verificação de *calibration* dos intervalos.

## Justificativa
- Uma resposta confiante e errada destrói a confiança do agricultor — e é
  cientificamente desonesta.
- Com pouco dado, índices climáticos em janelas fenológicas superam redes neurais.
- Interpretabilidade é requisito de adoção no agronegócio, não luxo.

## Consequências
- (+) Confiança e honestidade científica como diferencial de produto.
- (+) Caminho incremental de modelagem (baseline → boosting → deep).
- (−) Exige disciplina de UX para comunicar incerteza sem confundir o usuário.
