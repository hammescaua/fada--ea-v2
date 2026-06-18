# Flywheel de dados, Digital Twin (fundação) e Orchestrator

Evolução do FADA de inteligência para **produto**, com foco na prioridade
estratégica: iniciar a captura de dado proprietário que tornará o sistema melhor a
cada safra. Sem solo, mercado, doença, CAR, RAG ou multi-agente (fora de escopo).

## 1. Fundação do Digital Twin + flywheel (ADR-0009)

Agregado mínimo (bounded context `farm`):

```
Farm ──< Field ──< CropCycle ──< YieldObservation
 │         │           │              └ ground truth (rendimento real, datas, cultivar)
 │         │           └ cultura + Season (VO) + data de plantio
 │         └ área, geolocalização opcional
 └ município
```

`Season` é Value Object (`"2026/27"` → harvest_year 2027), não entidade.

**Persistência:** SQLAlchemy 2.0 síncrono, SQLite por padrão (Postgres via
`FADA_DATABASE_URL`). Repositórios isolam o domínio do ORM.

**Captura ≠ treino:** `YieldObservation` só é persistida. Nenhum pipeline a consome
ainda. Acumulada por safras, será o ground truth para calibração por talhão (V2+).

### Endpoints
```
POST /api/v1/farms                          GET /api/v1/farms
POST /api/v1/farms/{id}/fields              GET /api/v1/farms/{id}/fields
POST /api/v1/fields/{id}/crop-cycles
POST /api/v1/yield-observations             GET /api/v1/yield-observations
```

`YieldObservation` guarda: `actual_yield_sc_ha`, `actual_planting_date`,
`actual_harvest_date`, `cultivar`, `area_ha`, `notes`, `created_at`.

## 2. Orchestrator conversacional (ADR-0010)

`POST /api/v1/assistant` — interpreta a pergunta, roteia para um serviço
determinístico e verbaliza o resultado. **O LLM não gera números** (ADR-0002);
roteamento determinístico é o padrão, Claude é opcional.

Exemplos validados (município de contexto opcional):

| Pergunta | Intenção | Serviço |
|---|---|---|
| "Qual a melhor data para plantar soja em Horizontina?" | optimization | planting-window-optimization |
| "Vale plantar em 20 de outubro?" | simulation | planting-date-simulation |
| "Quais os riscos?" | regional | regional-intelligence |
| "Quanto eu colheria se plantasse em novembro?" | simulation | planting-date-simulation |

## 3. Frontend

Next.js + TypeScript + Tailwind + React Query + Recharts (`frontend/`). Páginas:
Regional Intelligence, Planting Simulation, Planting Optimization, **Ground Truth
Capture** e Assistant. Veja `frontend/README.md`.

## Limitações
- Sem migrações versionadas (Alembic) — `create_all()` até o schema estabilizar.
- Roteamento conversacional por regras; perguntas fora do escopo pedem reformulação.
- Ground truth ainda não calibra modelos (decisão deliberada desta fase).
