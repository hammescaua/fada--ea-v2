# Planting Date What-If

Análise de data de plantio sobre o MVP regional, **sem** introduzir solo, mercado,
doença ou gêmeo digital. Responde: *e se eu plantar antes/depois? qual data é mais
robusta? como o risco muda?*

## Hipótese científica

Mudar a data de plantio **desloca o período reprodutivo no calendário** (por tempo
térmico), alterando a **exposição climatológica** a déficit hídrico, veranico e calor.
O modelo de produtividade traduz essa mudança de exposição em mudança de risco/safra.
É uma ferramenta **comparativa** (deltas vs. data-base), não um oráculo absoluto —
ver ADR-0007.

## Pipeline

```
clima real por ano (Open-Meteo/NASA)
        │  fenologia GDD recoloca R1–R6 por data de plantio
        ▼
build_planting_grid  ──►  grid: município × data × ano × features  (15.300 linhas)
        │
        ▼
PlantingDateService ──►  /planting-date-simulation   (uma data)
                    └──►  /planting-window-optimization (Top 5 robusto, ZARC)
```

Grid pré-computado offline (pesado) → runtime leve (numpy + agregação).

## Fenologia (GDD, base 10 °C)

| Estágio | GDD desde o plantio |
|---|---|
| Emergência | 110 |
| R1 (início floração) | 720 |
| R6 (grão cheio) | 1500 |

Período crítico de estresse = R1→R6. Calibrado para reproduzir ~a janela de treino
na data-base (validação em ADR-0007).

## Backtest climatológico e cenários

Para cada data, rejogamos contra os 45 anos reais; a **distribuição** de
produtividade prevista dá: esperado (mediana), pessimista (P10), otimista (P90),
intervalo (resíduo do modelo), downside (P10) e estabilidade (IQR).

## Otimização robusta (ADR-0008)

`score(D) = mediana − λ·(mediana − P10)`, `λ` = aversão a risco (default 0.5),
restrita ao **ZARC**. Não escolhe a maior média — escolhe alta produtividade **e**
bom piso em anos ruins.

## Endpoints

`POST /api/v1/planting-date-simulation`
```json
{"municipality":"Horizontina","crop":"soja","season":"2026/27","planting_date":"2026-11-01"}
```

`POST /api/v1/planting-window-optimization`
```json
{"municipality":"Horizontina","crop":"soja","season":"2026/27","risk_aversion":0.5}
```

### Exemplo real (Horizontina, 2026/27)
- Reconciliação com endpoint regional: **52,4 vs 51,2 sc/ha** (Δ +1,2).
- Top robusto (ZARC): **30/11** (esperado 54,8 · piso 45,7 · score 50,3),
  25/11, 05/12. Datas que historicamente reduzem o déficit reprodutivo.

Saídas completas em [`examples/`](../examples).

## Limitações

- Captura **risco climático** da data, não potencial produtivo intrínseco
  (fotoperíodo/radiação) — por isso opera dentro do ZARC (`scope_note` na resposta).
- Resolução do grid: 5 dias (datas são encaixadas; precisão fina é ruído climático).
- Efeito absoluto de data não calibrado por dado de campo (V1+).

## Reproduzir

```bash
python -m pipelines.build_planting_grid    # grid de features (MLflow)
python -m pipelines.example_planting        # exemplos + validação/reconciliação (MLflow)
pytest app/tests/test_phenology.py app/tests/test_planting_simulation.py
```
