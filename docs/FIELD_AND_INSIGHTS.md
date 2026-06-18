# Field Intelligence + Insight Engine

Primeiro passo da transição do FADA de "plataforma científica" para **Farm Operating
System**: valor ao produtor a partir do dado que ele já registra. Determinístico,
auditável, com *evidence gating*. Sem cultivar, sem shrinkage por talhão, sem LLM
gerando número (ADR-0014).

## Field Intelligence (descritivo, computado na leitura)

Para cada talhão, agrega suas safras em um sumário:
- produtividade média e **bias vs. região** (resíduo ajustado ao clima);
- **estabilidade** = desvio dos resíduos relativos (não da produtividade bruta — senão
  confunde clima com instabilidade);
- custo/ha médio e **tendência de custo**;
- última safra e nº de safras.

`GET /api/v1/farms/{id}/field-analytics` → sumários + rankings (sem persistir perfil).

## Insight Engine (regras + estatística, com gating)

`GET /api/v1/farms/{id}/insights`. Cada insight declara **N** e **tamanho de efeito**.

| Insight | Gate | Exemplo |
|---|---|---|
| Melhor / pior talhão (produtividade) | ≥2 safras, ≥2 talhões | "Talhão Norte rende +7,2% vs. média da fazenda" |
| Mais / menos estável | ≥3 safras + gap 1,3× | "Talhão Leste é o menos estável (desvio 16%)" |
| Tendência de custo | ≥3 safras + |Δ|>10% | "Custo crescendo há 4 safras (+80%)" |
| Anomalia de produtividade | ≥4 safras, z>2, variância>0 | "Safra 2024 muito abaixo da norma (z=−21)" |
| Fazenda vs. região | ≥3 registros | "A fazenda rende 1,5% abaixo da região" |

Confiança: **alta** (n≥5), **moderada** (3–4), **exploratória** (<3). Insights de
padrão climático (ENSO) e ranking de cultivar foram **descartados** (inferência fraca /
confundimento).

## Por que estes objetos, e não outros
- **Cultivar:** confundido com ano/talhão/manejo em dado observacional → adiado (V3).
- **Bias-correction por talhão:** 1 obs/talhão/ano → encolhimento dá ~zero por anos →
  adiado; quando entrar, hierárquico de 3 níveis (talhão→fazenda→região).
- **Estabilidade ajustada ao clima:** reusa os resíduos do Adaptive Intelligence.

## Exemplo
`examples/insights_demo.json` (fazenda sintética com 3 talhões × 7 safras):
melhor (Norte), pior (Sul), menos estável (Leste), custo crescente e anomalia —
todos com N e efeito.

## Reproduzir
```bash
python -m pipelines.example_insights
pytest app/tests/test_insights.py app/tests/test_insights_endpoints.py
```

## Limitações
- Insights só surgem com dado suficiente (gating) — intencional.
- Sem causalidade de cultivar/manejo; sem time-decay; sem personalização por talhão.
