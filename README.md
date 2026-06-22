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

## Estado atual — V1 utilizável

Produto completo de apoio à decisão na safra de soja (microrregião Três Passos,
Noroeste RS), com **frontend Next.js** e **backend FastAPI**:

| O produtor pergunta | Onde responde |
|---|---|
| Quanto vou colher? Qual o risco? | **Estimativa da Região** (produtividade + intervalo + cenários + riscos) |
| Qual a melhor data para plantar? | **Melhor Janela de Plantio** (otimização robusta dentro do ZARC) |
| Como está minha safra? | **Minha Lavoura** (resumo, plano×real, custos, atenção, timeline) |
| Estou no orçamento? Quanto falta investir? | **Plano & Orçamento** |
| Quanto vou lucrar? Quanto para empatar? | **Financeiro** (custo/ha, custo/saca, break-even, cenários) |
| Onde devo olhar primeiro? | **Decisões** (atenção por talhão, por alertas nomeados) |
| Minha fazenda produz acima da média? | **Personalização da Fazenda** (encolhimento bayesiano) |
| Os intervalos são confiáveis? | **Sobre o Modelo** (calibração) + selo de confiança |
| (em linguagem natural) | **Assistente** (roteia para os serviços; nunca inventa número) |

Captura de dados em poucos toques (**Registro rápido** + presets) alimenta o
*flywheel*; a personalização e a calibração melhoram a cada safra registrada.

**MVP — Camada 1 (Inteligência Regional) ponta a ponta** com dados reais. Dado
município + cultura + safra, retorna produtividade estimada (sc/ha), intervalo,
cenários, riscos climáticos, janela de plantio e explicação em linguagem natural.

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
- [`docs/V1_OVERVIEW.md`](docs/V1_OVERVIEW.md) — **visão geral da V1 concluída** (o que entrega + backlog V2+)
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

## Como rodar (dev)

Precisa de **dois terminais**: backend (porta 8000) e frontend (porta 3000).

### 1. Backend (FastAPI)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[ml,dev]"
pytest                              # 164 testes (domínio + serviço + API)
uvicorn app.main:app --reload --port 8000
# http://localhost:8000/api/v1/health  ·  http://localhost:8000/docs
```
O modelo treinado (`data/models/*.json`), o dataset (`data/features/*.csv`) e o
relatório de calibração já vêm versionados — funciona out-of-the-box. Banco padrão:
**SQLite** (`data/fada.db`); use `FADA_DATABASE_URL` para Postgres.

### 2. Frontend (Next.js)
```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local   # sem barra no fim, sem /api/v1
npm run dev          # http://localhost:3000
```
> **GitHub Codespaces / rede:** `localhost` é a SUA máquina. Se o frontend roda numa
> URL encaminhada, aponte `NEXT_PUBLIC_API_URL` para a URL **encaminhada da porta
> 8000** (https), deixe a porta 8000 **Public**, e reinicie `npm run dev`.
> CORS é configurável via `FADA_CORS_ORIGINS` (padrão `*` em dev).

### 3. Primeiro acesso
Abra `http://localhost:3000` → **Início**. Sem dados? Clique em **"Explorar com
fazenda de demonstração"** (popula histórico, plano, custos e insights) ou siga o
**onboarding** guiado (`/onboarding`): fazenda → talhão → safra → pronto. A seleção
**Fazenda · Safra** no topo persiste entre as páginas.

### (opcional) Reconstruir modelos a partir das fontes públicas
```bash
cd backend && source .venv/bin/activate
python -m pipelines.build_dataset         # IBGE + Open-Meteo/NASA -> data/features
python -m pipelines.train                 # compara Ridge/RF/XGBoost -> data/models (MLflow)
python -m pipelines.build_planting_grid   # grid de data de plantio (fenologia GDD)
python -m pipelines.backtest_calibration  # relatório de calibração
```

## Stack

Backend: FastAPI · Pydantic v2 · SQLAlchemy (SQLite/Postgres) ·
scikit-learn/XGBoost (offline) · Claude opcional (orquestração/explicação — nunca
gera número). Frontend: Next.js (App Router) · React · Tailwind · TanStack Query ·
Recharts.
