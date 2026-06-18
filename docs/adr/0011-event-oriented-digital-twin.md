# ADR-0011 — Digital Twin orientado a eventos (não event sourcing) + Cost Engine

**Status:** Aceito · **Data:** 2026-06-17

## Contexto
A safra é, na essência, uma **sequência de operações** (plantio, adubação,
pulverizações, colheita). Custo, nº de aplicações e investimento são *derivados*
dessas operações. Queremos um Digital Twin que acumule conhecimento por safra, sem
"dezenas de tabelas rígidas".

## Decisão
1. **Orientado a eventos, NÃO event sourcing.** Uma única entidade flexível
   `AgriculturalEvent` (filha do agregado `CropCycle`), com `event_type` + payload
   (produto, quantidade, unidade, custo). O **estado derivado** (custo total,
   custo/ha, nº de aplicações) é **calculado na leitura** pelo Cost Engine. Evitamos
   a maquinaria de event store/projeções/replay — complexidade prematura.
2. **CropCycle é o registro-cabeçalho da safra.** Datas canônicas
   (`actual_planting_date`, `harvest_date`) e `actual_yield_sc_ha` vivem nele.
   Eventos `PLANTING`/`HARVEST` capturam apenas custo/insumos dessas operações —
   sem digitar produtividade em dois lugares. `YieldObservation` permanece para
   captura **granular** (tickets de balança).
3. **`Product` opcional nos eventos.** `product_id` (FK) e/ou `product_name` livre —
   não forçar o catálogo preserva baixo atrito de captura (o flywheel).
4. **Cost Engine determinístico** (`calculate_total_cost`, `cost_per_hectare`,
   `cost_per_bag`, `break_even_yield`, `scenario_analysis`). Nenhum LLM (ADR-0002).
5. **Preço da saca é input do produtor**, não previsão. `break_even` e
   `scenario_analysis` recebem o preço spot; `scenario_analysis` integra
   **custo (eventos) + preço (input) + produtividade (modelo)** → lucro/margem.

## Trade-offs
- (+) Flexível: novos tipos de operação não exigem novas tabelas.
- (+) A timeline é a fonte da verdade; o financeiro é sempre coerente com ela.
- (+) Custo/decisão 100% determinístico e testável.
- (−) Sem o histórico de auditoria imutável do event sourcing (não necessário agora).
- (−) Estado derivado recalculado a cada leitura (barato nesta escala; cacheável depois).
- (−) `create_all()` sem Alembic: evoluir o schema do `CropCycle` exige recriar o
  banco de dev (SQLite, não versionado).

## Bounded contexts
- `farm`: `CropCycle` (raiz) + `AgriculturalEvent` + `EventType`; `YieldObservation`.
- `catalog`: `Product`, `ProductCategory`.
- `cost`: Cost Engine (funções puras + value objects).
- `engine`: orchestrator com intenções de custo (chama o Cost Engine).
