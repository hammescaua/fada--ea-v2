# ADR-0009 — Persistência de ground truth (fundação do flywheel)

**Status:** Aceito · **Data:** 2026-06-17

## Contexto
A prioridade estratégica do FADA é o **flywheel de dados**: capturar dado
longitudinal de campo para, no futuro, calibrar os modelos. Precisamos das entidades
fundacionais do Digital Twin sem introduzir complexidade prematura (solo, CAR,
manejo, gêmeo digital completo ficam fora).

## Decisão
1. **Bounded context `farm`** (domínio puro): agregado
   `Farm → Field → CropCycle → YieldObservation`.
2. **Season como Value Object** (rótulo + ano de colheita), não entidade — não tem
   identidade nem ciclo de vida próprios. Simplificação deliberada.
3. **SQLAlchemy 2.0 síncrono + SQLite por padrão**; Postgres em produção via
   `FADA_DATABASE_URL`. Endpoints já são síncronos; async seria cerimônia sem ganho.
4. **`create_all()` agora, Alembic depois** — migrações entram quando o schema
   estabilizar.
5. **Repositórios** mapeiam ORM ⇄ entidades de domínio: o domínio nunca importa
   SQLAlchemy.
6. **Captura ≠ treino.** `YieldObservation` é apenas persistida; nenhum pipeline de
   treino a consome nesta fase. É o ground truth que, acumulado por safras,
   calibrará os modelos.

## Justificativa
- Modelo mínimo que cobre Farm/Field/CropCycle/YieldObservation sem over-engineering.
- SQLite torna o sistema rodável e testável out-of-the-box (sem subir Postgres).
- Separar ORM de domínio preserva a pureza e a testabilidade do núcleo científico.

## Consequências
- (+) Flywheel iniciado com baixa complexidade; caminho claro para Postgres/Alembic.
- (+) `YieldObservation` guarda rendimento real, datas reais de plantio/colheita,
  cultivar, área e notas — exatamente o que falta para calibração por talhão (V2+).
- (−) Sem migrações versionadas ainda; mudanças de schema exigem cuidado até Alembic.
