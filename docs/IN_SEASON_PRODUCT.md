# Produto na safra — Quick Capture, Plano e Orçamento

Virada de "plataforma científica" para **ferramenta usada na safra**. Foco: reduzir o
atrito de captura (o flywheel) e dar visão de plano x realizado. Sem OCR, sem CropPlan
separado, sem Budget Engine, sem contexto Operations (ADR-0015).

## Quick Capture (atrito mínimo)

- **`EventPreset`** — "operação favorita" que pré-preenche um evento (tipo, produto,
  dose, custo padrão; custo pode ser por hectare).
- **`POST /api/v1/quick-log`** — registra a mesma operação em **1..N talhões** numa
  chamada; com preset, o custo é resolvido por talhão (por ha × área).

```
POST /event-presets        GET /event-presets
POST /quick-log  { crop_cycle_ids:[..], event_date, preset_id }  -> N eventos
```

## Plano da safra (no CropCycle, sem agregado separado)

O plano vive no `CropCycle` (`target_yield_sc_ha`, `expected_price_per_bag`) +
**`PlannedEvent`** (operações planejadas). Uma só entidade nova, que também alimenta a
agenda.

```
POST /crop-cycles/{id}/planned-events     GET  /crop-cycles/{id}/planned-events
```

## Orçamento: Plano x Realizado (extensão do Cost Engine)

`GET /crop-cycles/{id}/plan-vs-actual` → planejado vs realizado: custo total e /ha,
variância, **quanto falta investir**, nº de aplicações, lucro esperado (a preço
informado) e uma interpretação determinística.

Exemplo: *"Gastou R$ 152.000 de R$ 160.000 (95%) — dentro do planejado. Faltam
R$ 8.000. Aplicações: 2 de 3."*

## Agenda (vista derivada de PlannedEvent)

`GET /crop-cycles/{id}/agenda` → operações planejadas com status (**concluída /
atrasada / próxima**) por reconciliação de contagem por tipo (honesto, sem matching
frágil) + resumo.

## Assistente (determinístico)

`POST /assistant` com `crop_cycle_id`: "Estou gastando acima do planejado?" ·
"Quanto ainda falta investir?" · "Estou seguindo meu plano?". O LLM nunca gera número.

## Sequência de uso (o plano é opcional)

```
Criar safra → [Criar plano] → registrar operações (quick-log) →
acompanhar plano x real → registrar colheita → insights → (personalização automática)
```

## Limitações
- Sem import CSV/Excel nem OCR (entrada manual, mitigada por presets/quick-log).
- Agenda por contagem de tipo (não vincula evento real ↔ planejado individualmente).
- Tank mix multi-produto, lembretes/push: adiados.
