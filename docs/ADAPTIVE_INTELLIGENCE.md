# Adaptive Farm Intelligence

Personaliza progressivamente a predição por fazenda como **correção** sobre o modelo
regional — nunca substituição. `Prediction = Regional + BiasCorrection`, com
encolhimento hierárquico e incerteza preservada (ADR-0012). Sem treino, sem deep
learning, sem retreinar o regional.

## Método (em uma figura)

```
safras reais da fazenda ─┐
                         │  fitted = modelo regional sob o CLIMA REAL do ano
                         ▼  (isola fazenda de clima)
      resíduo r = (actual − fitted)/fitted  ──►  FarmPerformanceProfile (memória)
                                                      │ n, bias observado, variância
                                                      ▼
  w = n/(n+k),  k = s²/τ²   ──►  shrunk_bias = w·bias   (encolhe p/ regional)
                                                      │
  personalized = regional × (1 + shrunk_bias)         │
  intervalo = √(reg² + (point·SE_bias)²)  (nunca estreita)
```

## Regra de confiança
`w = n/(n+k)` com `k = s²/τ²`. Depende de **quantidade E consistência** das safras.
Defaults: n=1 → ~11% de confiança; n=10 (consistente) → ~70%; n=20 → ~86%. Fazenda
ruidosa é encolhida mais (menos confiança para o mesmo n).

## Incerteza-first
`halfwidth_pers = √(halfwidth_reg² + (point_reg·SE_bias)²)`. A incerteza climática do
ano é **irredutível**: personalizar move o centro, quase não estreita a banda — e
nunca abaixo da regional. Com `n=0`, a previsão é puramente regional.

## Endpoints

```
POST /api/v1/farms/{id}/performance-profile/recompute   # recomputa a memória
GET  /api/v1/farms/{id}/performance-profile             # perfil + evolução dos resíduos
POST /api/v1/personalized-intelligence                  # {farm_id, season}
```

`/personalized-intelligence` retorna: `regional_prediction`, `farm_adjustment`
(observed vs applied, n_cycles), `personalized_prediction` (ponto, intervalo,
cenários), `confidence_score`, `adaptation_level`, `explanation`.

### Exemplo (fazenda demo +12%, Horizontina, 2026/27 — sintético)
- Bias observado **+12,1%** recuperado de 10 safras (inclusive 2022, ano de seca,
  graças ao clima-condicionamento).
- Regional **51,2** → Personalizado **56,0 sc/ha** (ajuste **+9,3%** após encolhimento,
  confiança **77%**, adaptação **alta**).
- Intervalo personalizado **≥** regional (não estreita). Ver `examples/adaptive_farm_demo.json`.

## Orchestrator (ADR-0010)
Perguntas adaptativas (com `farm_id` de contexto): "Minha fazenda produz acima da
média?", "Quanto o FADA já aprendeu?", "Quão confiável é essa personalização?",
"Diferença entre regional e personalizada?". O LLM nunca gera número.

## Limitações
- Apenas `FarmPerformanceProfile` (Field/Cultivar = evolução).
- Prior fixo (Empirical Bayes quando houver população de fazendas).
- Sem time-decay (não-estacionariedade) e sem desconfundir cultivar — futuro.
