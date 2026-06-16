# FADA — Arquitetura

> Documento vivo. Decisões pontuais são registradas como ADRs em `docs/adr/`.

## 1. Visão geral

FADA é um **modular monolith** organizado por *bounded contexts* (DDD). Um único
deploy FastAPI, com fronteiras internas explícitas que permitem extrair um módulo
em serviço independente **quando e se** a escala justificar.

```
┌─────────────────────────────────────────────────────────┐
│  FRONTEND  Next.js + React + Tailwind + shadcn/ui        │
│  Dashboard · Mapas (PostGIS→GeoJSON) · Timeline · What-If│
└───────────────────────────┬─────────────────────────────┘
                            │ REST/JSON (OpenAPI)
┌───────────────────────────┴─────────────────────────────┐
│  API LAYER  FastAPI + Pydantic v2 (async)                │
│  Auth · validação · DTOs · versionamento /api/v1         │
├──────────────────────────────────────────────────────────┤
│  DECISION ENGINE  (o "cérebro")                          │
│  ├─ LLM Orchestrator (Claude) → intent + tool-calling    │
│  ├─ Explanation/NL layer (Claude)                        │
│  └─ Research/RAG (EMBRAPA, boletins técnicos)            │
├──────────────────────────────────────────────────────────┤
│  DOMAIN SERVICES  (Python puro, determinístico, testável)│
│  units · climate · soil · crop · disease · input ·       │
│  machinery · cost(finance) · yield · market · whatif     │
├──────────────────────────────────────────────────────────┤
│  DATA PLATFORM                                           │
│  Ingestion/ETL (raw→curated→features) · cache+rate-limit │
│  Connectors: NASA POWER · Open-Meteo · INMET · CONAB ·   │
│  IBGE · SICAR/CAR · AgroBR                               │
├──────────────────────────────────────────────────────────┤
│  PERSISTENCE  PostgreSQL + PostGIS · Redis · Object store │
│  · MLflow (experimentos) · DVC (dados versionados)       │
└──────────────────────────────────────────────────────────┘
```

## 2. Camadas e responsabilidades

### API Layer (`app/api`)
Fina. Só HTTP: validação de entrada/saída (Pydantic), autenticação, versionamento
(`/api/v1`), tradução para chamadas de serviço. **Nenhuma regra de negócio aqui.**

### Decision Engine (`app/engine`)
A única camada onde LLM vive. Padrão **orquestrador + tool use**: o Claude
interpreta a intenção do agricultor, escolhe e chama *ferramentas determinísticas*
(os domain services), e depois **explica** o resultado em linguagem natural. O LLM
nunca produz números diretamente — ver ADR-0002.

### Domain Services (`app/domain`)
Coração científico. **Python puro, sem I/O, sem framework**, 100% testável e
reprodutível. Cada contexto é um pacote isolado:

| Contexto | Responsabilidade | Natureza |
|---|---|---|
| `units` | conversões (saca↔kg, kg/ha↔sc/ha, área, volume) | determinístico |
| `climate` | índices agroclimáticos (GDD, déficit hídrico, veranico, chuva em janela) | determinístico |
| `soil` | interpretação de análise de solo (regras CQFS-RS/SC, EMBRAPA) | determinístico |
| `crop` | culturas, cultivares, fenologia, exigências, ciclos | determinístico |
| `disease` | risco de pragas/doenças (ex.: ferrugem asiática) | modelo epidemiológico |
| `input` | defensivos, adubos, sementes, doses | determinístico |
| `machinery` | máquinas, consumo de diesel, custo operacional | determinístico |
| `cost` | custo, margem, ROI, breakeven, fluxo de caixa | determinístico |
| `yield` | estimativa de produtividade + cenários + incerteza | estatístico/ML |
| `market` | preço atual, futuros, basis, cenários de margem | dados + cenário |
| `whatif` | sensibilidade de decisões (data, cultivar, adubação, aplicações) | composição |

> **Correção arquitetural-chave:** a maioria dos "agentes" do conceito original
> **não são agentes de LLM** — são serviços de domínio determinísticos. Ver ADR-0002.

### Data Platform (`app/data`)
Ingestão e curadoria. Pipeline **raw → curated → features**. Conectores para fontes
externas com **cache (Redis)** e **respeito a rate-limit**. Separa "obter dado" de
"servir dado". Ingestão é agendada (cron+Python no início; Prefect/Dagster depois).

### Persistence (`app/infra`)
PostgreSQL + **PostGIS** (talhões, CAR, *point-in-grid* climático), Redis (cache),
object storage (raw). MLflow + DVC para reprodutibilidade de modelos (V2+).

## 3. Decisões técnicas-chave

| Tema | Escolha | Justificativa | ADR |
|---|---|---|---|
| Estrutura | Modular monolith (DDD) | Solo/time pequeno: baixo custo de coordenação | 0001 |
| LLM | Claude, só na orquestração/explicação/RAG | Determinismo numérico; sem alucinar valores | 0002 |
| Incerteza | Cenários + intervalos sempre | Honestidade científica = confiança | 0003 |
| Geoespacial | PostGIS | SQL espacial nativo p/ talhão/CAR/clima | — |
| ML inicial | Baseline estatístico → gradient boosting | Pouco dado: índices climáticos batem deep learning | 0003 |
| Unidades | Módulo `units` dedicado | Erro de unidade é a falha silenciosa nº1 em agro | — |

## 4. Modelos de ML — veredito

- **Prophet / LSTM:** ❌ no início. Volume de dado insuficiente; problema é regressão
  multivariada, não série univariada sazonal. Reavaliar na V2+.
- **RF / XGBoost / LightGBM / CatBoost:** ✅ família vencedora para dado tabular.
  CatBoost para muitas categóricas (cultivar, solo, município); LightGBM para escala.
- **Sempre** reportar incerteza (quantile boosting ou conformal prediction).
  Modelo sem intervalo não vai para produção.

## 5. Cross-cutting

- **LGPD / governança.** CAR, localização e dado econômico são sensíveis. Base legal,
  consentimento e isolamento por tenant desde o início.
- **Validação científica.** Backtest *walk-forward* por safra; métricas MAE/MAPE em
  sc/ha; *calibration* dos intervalos. Sem isso não é ciência, é opinião.
- **Observabilidade.** Logs estruturados, tracing das tool-calls do LLM, custo/request.

## 6. Estrutura de pastas (backend)

```
backend/app/
  main.py                 # bootstrap FastAPI
  core/config.py          # settings (pydantic-settings)
  api/v1/                 # rotas HTTP (finas)
  engine/                 # Decision Engine (LLM orquestração/explicação) — V2+
  domain/                 # serviços de domínio (puros, testáveis)
    units/  climate/  yield_estimation/  ...
  data/connectors/        # NASA POWER, Open-Meteo, CONAB, IBGE, ...
  infra/                  # db, cache, repositórios
  services/               # casos de uso (orquestra domínio + dados)
  tests/                  # unit + integração
```
