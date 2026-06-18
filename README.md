# FADA — Farm AI Decision Agent

> **Agricultural Decision Intelligence System** — transforma dados públicos e da
> propriedade em **respostas acionáveis** para o agricultor: quanto vou colher,
> quanto vou gastar, quanto vou lucrar, qual o risco da safra.

FADA não é um preditor de produtividade isolado. É um sistema de **suporte à
decisão agrícola** que combina serviços de domínio determinísticos (agronomia e
finanças), modelos estatísticos/ML com **incerteza calibrada**, e uma camada de
linguagem natural (Claude) para orquestração e explicação.

## Princípios de engenharia

1. **Determinístico-first.** Cálculo agronômico e financeiro vive em código puro,
   testável e reprodutível — *não* dentro de um LLM. O LLM nunca inventa um número;
   ele chama uma ferramenta.
2. **Honestidade científica.** Toda saída numérica vem com incerteza (intervalo,
   cenários, e o N de dados que a sustenta). Resposta confiante e errada destrói
   confiança.
3. **Data flywheel.** O ativo defensável é o dado longitudinal de campo. O produto
   captura dado limpo do agricultor desde o MVP (inclusive "quanto você colheu?").
4. **Modular monolith.** Um único deploy, *bounded contexts* com fronteiras limpas
   (DDD). Extrai-se em serviço só quando a escala exigir — não antes.

## Estado atual

**MVP — Camada 1 (Inteligência Regional) funcionando ponta a ponta** com dados reais:
soja, microrregião Três Passos (Noroeste RS). Dado município + cultura + safra,
retorna produtividade estimada (sc/ha), intervalo, cenários, riscos climáticos,
janela de plantio e explicação em linguagem natural.

```bash
curl -X POST http://localhost:8000/api/v1/regional-intelligence \
  -H 'Content-Type: application/json' \
  -d '{"municipality":"Horizontina","uf":"RS","crop":"soja","season":"2026/27"}'
```

**Planting Date What-If** — simulação de data de plantio e otimização robusta (ZARC):

```bash
curl -X POST http://localhost:8000/api/v1/planting-window-optimization \
  -H 'Content-Type: application/json' \
  -d '{"municipality":"Horizontina","crop":"soja","season":"2026/27","risk_aversion":0.5}'
```

**Flywheel de dados + conversacional** — captura de ground truth (Farm/Field/
CropCycle/YieldObservation) e um assistente que roteia perguntas para os serviços
determinísticos (o LLM não gera números):

```bash
curl -X POST http://localhost:8000/api/v1/assistant \
  -H 'Content-Type: application/json' \
  -d '{"message":"Qual a melhor data para plantar soja em Horizontina?"}'
```

E um **frontend** (Next.js) em [`frontend/`](frontend/) consumindo todos os endpoints.

Veja:
- [`docs/MVP_REGIONAL_INTELLIGENCE.md`](docs/MVP_REGIONAL_INTELLIGENCE.md) — a fatia, com resultados reais
- [`docs/PLANTING_DATE_WHATIF.md`](docs/PLANTING_DATE_WHATIF.md) — What-If de data de plantio
- [`docs/FLYWHEEL_AND_ASSISTANT.md`](docs/FLYWHEEL_AND_ASSISTANT.md) — captura de ground truth + orchestrator
- [`docs/DIGITAL_TWIN_V1.md`](docs/DIGITAL_TWIN_V1.md) — timeline de eventos + Cost Engine
- [`docs/ADAPTIVE_INTELLIGENCE.md`](docs/ADAPTIVE_INTELLIGENCE.md) — personalização por fazenda (encolhimento)
- [`docs/CALIBRATION_AND_RELIABILITY.md`](docs/CALIBRATION_AND_RELIABILITY.md) — os intervalos são honestos?
- [`docs/FIELD_AND_INSIGHTS.md`](docs/FIELD_AND_INSIGHTS.md) — inteligência por talhão + Insight Engine
- [`docs/IN_SEASON_PRODUCT.md`](docs/IN_SEASON_PRODUCT.md) — quick capture, plano e orçamento
- [`docs/DECISION_SUPPORT.md`](docs/DECISION_SUPPORT.md) — atenção por talhão (sem score mágico)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — arquitetura e decisões técnicas
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — MVP / V1 / V2 / V3
- [`docs/DOMAIN_MODEL.md`](docs/DOMAIN_MODEL.md) — modelo de domínio e ubiquitous language
- [`docs/adr/`](docs/adr/) — Architecture Decision Records
- [`examples/`](examples/) — saídas reais do endpoint

## Rodando o backend (dev)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[ml,dev]"

# (opcional) reconstruir dataset e modelo a partir das fontes públicas:
python -m pipelines.build_dataset        # IBGE + Open-Meteo/NASA -> data/features
python -m pipelines.train                # compara Ridge/RF/XGBoost -> data/models (MLflow)
python -m pipelines.build_planting_grid  # grid de data de plantio (fenologia GDD)

pytest                              # 38 testes (domínio + serviço + API)
uvicorn app.main:app --reload
# http://localhost:8000/api/v1/health  ·  http://localhost:8000/docs
```

O modelo treinado (`data/models/*.json`) e o dataset (`data/features/*.csv`) já vêm
versionados — o endpoint funciona out-of-the-box após `pip install`.

## Stack

Backend: FastAPI · Pydantic v2 · SQLAlchemy · PostgreSQL + PostGIS · Redis ·
Claude (orquestração/explicação) · scikit-learn/XGBoost (V2+).
Frontend (a partir do MVP+): Next.js · React · Tailwind · shadcn/ui.
