# Digital Twin V1 — timeline de eventos + Cost Engine

Transforma o FADA em um gêmeo digital que acumula conhecimento por safra. Sem
Disease/Soil/Market/RAG/Multi-agente/NDVI/CAR/Deep Learning. Princípio: **eventos >
estados** — orientado a eventos, não event sourcing (ADR-0011).

## Modelo

```
Farm ──< Field ──< CropCycle ──< AgriculturalEvent   (timeline operacional)
                       │           └ event_type, event_date, product, quantity, cost
                       ├ área, cultivar, datas canônicas, actual_yield_sc_ha
                       └< YieldObservation (captura granular: tickets de balança)

Product (catálogo de insumos, sem preços dinâmicos)
```

`CropCycle` é o registro-cabeçalho da safra; os eventos são a verdade operacional;
o **estado financeiro é derivado na leitura** pelo Cost Engine.

## Cost Engine (determinístico — ADR-0002/0011)

| Função | Saída |
|---|---|
| `calculate_total_cost` | soma dos custos dos eventos (R$) |
| `calculate_cost_per_hectare` | custo total ÷ área |
| `calculate_cost_per_bag` | custo total ÷ produção (real ou esperada) |
| `calculate_break_even_yield` | custo/ha ÷ preço da saca → sc/ha p/ empatar |
| `scenario_analysis` | lucro/margem por cenário (custo + preço + produtividade) |
| `count_applications` | nº de manejos (pulverizações/adubações) |

**Preço da saca é input do produtor** (preço spot), nunca previsão de mercado.
Pré-colheita, custo/saca e cenários usam a produtividade **esperada do modelo**;
pós-colheita, a **real** informada no CropCycle.

## Endpoints

```
PATCH /api/v1/crop-cycles/{id}              # atualiza datas/produtividade conforme a safra avança
GET   /api/v1/crop-cycles/{id}
POST  /api/v1/crop-cycles/{id}/events       GET .../events     # timeline
POST  /api/v1/products                      GET /api/v1/products
GET   /api/v1/crop-cycles/{id}/cost         # breakdown (total, /ha, /saca, nº aplicações)
POST  /api/v1/crop-cycles/{id}/financials   # break-even + cenários de lucro (preço input)
```

### Exemplo (100 ha, 5 eventos, preço R$125/sc)
- Custo total R$ 260.000 → **R$ 2.600/ha** · **R$ 50,73/saca** (produtividade esperada) · 4 aplicações
- Break-even: **20,8 sc/ha**
- Cenários: pessimista 36,8 sc/ha → lucro R$ 200k (43,5%); normal 51,2 → R$ 381k (59,4%); otimista 55,5 → R$ 434k

## Orchestrator (intenções de custo — ADR-0010)

`POST /api/v1/assistant` (com `crop_cycle_id` de contexto; `price_per_bag` p/ break-even):

| Pergunta | Intenção |
|---|---|
| "Quanto já investi nesta safra?" | cost_total |
| "Qual meu custo por hectare?" | cost_per_hectare |
| "Quantas aplicações fiz?" | applications_count |
| "Qual produtividade preciso para empatar?" | break_even |

O LLM continua proibido de gerar números — apenas roteia e verbaliza (ADR-0002).

## Limitações
- Sem migrações Alembic (`create_all`); evoluir o schema recria o SQLite de dev.
- `quantity`/`unit` dos eventos são descritivos (sem normalização dose/ha) — V2.
- Catálogo sem preços dinâmicos (estrutura apenas).
