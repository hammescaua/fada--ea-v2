# MVP — Inteligência Regional (Camada 1)

Primeira fatia vertical do FADA, ponta a ponta, com **dados reais**. Responde, a
partir de **município + cultura + safra**, à pergunta central do agricultor: *quanto
vou colher, com qual risco e quando plantar?*

## Pipeline

```
IBGE/PAM (rendimento)  ┐
Open-Meteo / ERA5      ├─►  build_dataset  ─►  features (787 linhas)  ─►  train  ─►  model.json
NASA POWER (fallback)  ┘     (domínio puro)        data/features/          (CV)     data/models/
                                                                                       │
município+cultura+safra ──► RegionalIntelligenceService ──► /api/v1/regional-intelligence
                            (estimativa + cenários + riscos + janela + explicação)
```

Camadas de dados (DVC): `data/raw` (cache HTTP, gitignored) → `data/intermediate` →
`data/features` (versionado) → `data/models` (versionado).

## Dados

- **Ground truth:** IBGE/PAM tabela 1612 — rendimento municipal de soja (kg/ha),
  1980–2024, 20 municípios da microrregião **Três Passos** (Noroeste RS). 787 obs.
- **Clima:** Open-Meteo (reanálise ERA5, 1940+) como primária; **NASA POWER** (1981+)
  como fallback automático quando a primária falha (rate-limit). Ambos intercambiáveis.

## Features (ADR-0004)

| Feature | Papel |
|---|---|
| Déficit hídrico reprodutivo (Hargreaves ET0 − chuva, 21/dez–28/fev) | estresse hídrico — **primário** |
| Maior veranico reprodutivo | distribuição do estresse |
| Dias > 35 °C reprodutivo | estresse térmico |
| Precipitação total da safra | contexto hídrico |
| Ano de colheita | tendência tecnológica (ADR-0005) |

## Modelo (ADR-0003, ADR-0006)

Validação **leave-one-year-out** (prever um ano climático não observado):

| Modelo | MAE (sc/ha) | RMSE (sc/ha) |
|---|---|---|
| Ridge (produção) | 6.96 | 8.85 |
| Random Forest | 7.35 | 9.60 |
| XGBoost | 6.86 | 8.79 |

Erros indistinguíveis → ship do **Ridge linear** (interpretável). Coeficientes
agronomicamente corretos: déficit reprodutivo domina e é negativo; ano é positivo.

## Cenários e incerteza

Como a safra 2026/27 é **futura** (sem clima observado), os cenários vêm da
**climatologia histórica** do município:

- **Pessimista** = features de estresse no P90 adverso (ex.: déficit alto).
- **Normal** = mediana (P50).
- **Otimista** = P10 favorável.
- **Intervalo de confiança** = normal ± quantis de resíduo out-of-fold.

A assimetria observada (otimista sobe pouco, pessimista cai muito) é correta: soja
satura na água suficiente e tem cauda longa de perda por seca.

## Endpoint

`POST /api/v1/regional-intelligence`

```json
{ "municipality": "Horizontina", "uf": "RS", "crop": "soja", "season": "2026/27" }
```

Retorna: produtividade estimada (sc/ha), intervalo, 3 cenários, riscos climáticos
quantificados, janela de plantio (ZARC) e explicação em linguagem natural. Exemplos
reais em [`examples/`](../examples).

### Exemplo (Horizontina, 2026/27)
- Normal: **51,2 sc/ha** · IC [39,6; 62,0]
- Pessimista 36,8 · Otimista 55,5 sc/ha
- Risco principal: déficit hídrico reprodutivo (**alto**, ~−28% em ano adverso)

## Reproduzir

```bash
cd backend && pip install -e ".[ml,dev]"
python -m pipelines.build_dataset   # ingestão + features (cacheado em data/raw)
python -m pipelines.train           # comparação de modelos + artefato (MLflow)
python -m pipelines.example         # gera examples/
pytest
```

`params.yaml` + `dvc.yaml` definem o grafo reproduzível (`dvc repro`).

## Limitações (honestidade-first)

- Estimativa **regional**, não por talhão — não usa solo/manejo/cultivar (Camadas 2–4).
- Cobre só a microrregião Três Passos e **soja**. Expansão = ADR-0005/roadmap.
- Extrapolar a tendência tecnológica muitos anos à frente é arriscado; monitorar.
- A climatologia de cenários pode subestimar caudas extremas (ex.: secas-recorde).
