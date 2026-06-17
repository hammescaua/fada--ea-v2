# Calibração e Confiabilidade

Esta camada **mede**, não altera. Responde: *"os intervalos que o FADA comunica são
honestos?"*. Transforma o FADA de um sistema preciso em um sistema **calibrado**
(ADR-0013).

## Princípio
Hierarquia de avaliação probabilística: **calibração primeiro, sharpness depois,
precisão por último**. Um IC80 só é honesto se contém a realidade ~80% das vezes.

## Backtest (offline, leave-one-year-out)

`pipelines/backtest_calibration.py` roda LOYO sobre os 787 dados reais:
- **Regional**: modelo treinado nos demais anos; intervalo dos quantis de resíduo OOF
  dos outros anos (estilo conformal, sem vazar o ano-alvo).
- **Personalizado**: cada **município como proxy de fazenda** — bias estimado nos
  demais anos e aplicado pelo mesmo encolhimento do adaptive.

Produz `data/models/calibration_report.json` e loga no MLflow. Não muda previsões.

## Métricas (só as que sobreviveram à crítica)

| Métrica | Papel |
|---|---|
| **Cobertura 50/80/90/95 + IC de Wilson** | calibração; 80% é o IC comunicado (headline). Wilson dá a incerteza da própria métrica. |
| **Reliability diagram** | forma da (má-)calibração: esperado × observado por nível. |
| **Sharpness** (mean/median/relative width) | utilidade; intervalo largo demais é inútil. |
| **Pinball loss** (P10/P50/P90) | *proper scoring rule* p/ "o personalizado é melhor?". |
| **MAE / RMSE / Bias** | acurácia do ponto e direção do erro. |
| ~~CRPS~~ | **descartado**: redundante com pinball+cobertura (ADR-0013). |

Over/underconfidence só é declarado quando o **IC de Wilson exclui o nominal** (não se
confunde ruído amostral com má-calibração).

## Garantia fundamental (provada e testada)
`largura(personalizado) ≥ largura(regional)` para todo n —
`√(reg² + (ponto·SE_bias)²) ≥ reg`. Property-based testing com 25 mil entradas
aleatórias. A incerteza **nunca** diminui artificialmente.

## Resultados
- **Regional**: IC80 = **79%** [76–82] → calibrado; reliability quase diagonal.
- **Personalizado**: IC80 = **81%** (calibrado), **MAE 6,65 vs 6,96**, **pinball 2,18 vs
  2,25**, largura 22,5 vs 22,4 — melhora a acurácia sem estreitar nem descalibrar.

## Endpoint e assistente
- `GET /api/v1/calibration` → relatório (regional + personalizado).
- Assistente (determinístico): "os intervalos estão calibrados?", "quão confiável é o
  modelo?", "erra para cima ou para baixo?", "o personalizado é realmente melhor?".

## Reproduzir
```bash
python -m pipelines.backtest_calibration   # gera o relatório + MLflow
pytest app/tests/test_calibration_metrics.py app/tests/test_width_guarantee.py
```

## Limitações
- Calibração personalizada por proxy (municípios) até haver dado de fazenda real.
- Quantis OOF assumem estacionariedade; monitorar a cobertura ao longo das safras
  (mudança climática pode alargar a incerteza verdadeira).
