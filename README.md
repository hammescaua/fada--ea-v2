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

**MVP em construção — Camada 1 (Inteligência Regional), soja, Horizontina + Noroeste RS.**

Veja:
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — arquitetura e decisões técnicas
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — MVP / V1 / V2 / V3
- [`docs/DOMAIN_MODEL.md`](docs/DOMAIN_MODEL.md) — modelo de domínio e ubiquitous language
- [`docs/adr/`](docs/adr/) — Architecture Decision Records

## Rodando o backend (dev)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                      # roda os testes de domínio
uvicorn app.main:app --reload
# http://localhost:8000/api/v1/health  ·  http://localhost:8000/docs
```

## Stack

Backend: FastAPI · Pydantic v2 · SQLAlchemy · PostgreSQL + PostGIS · Redis ·
Claude (orquestração/explicação) · scikit-learn/XGBoost (V2+).
Frontend (a partir do MVP+): Next.js · React · Tailwind · shadcn/ui.
