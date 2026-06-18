# FADA — Modelo de Domínio

## Ubiquitous language (PT-BR ↔ código)

| Termo de domínio | Conceito no código | Notas |
|---|---|---|
| Saca | `Bag` / unidade de massa | Soja e milho: **60 kg**. Café: 60 kg (outro contexto). |
| Produtividade | `Yield` em `sc/ha` ou `kg/ha` | Sempre carregar a unidade explicitamente. |
| Talhão | `Plot` | Subdivisão de manejo de uma `Farm`. Geometria PostGIS. |
| Fazenda / Propriedade | `Farm` | Pode ter múltiplos talhões; vínculo com CAR. |
| Safra | `Season` | Ex.: `2026/27`. Define janela temporal de análise. |
| Cultura | `Crop` | soja, milho, trigo... |
| Cultivar / Híbrido | `Cultivar` | Ciclo, exigências, resistências. |
| Janela de plantio | `PlantingWindow` | Intervalo agronômico recomendado. |
| GDD | `growing_degree_days` | Soma térmica acima da temp. base da cultura. |
| Déficit hídrico | `water_deficit` | Demanda evapotranspirativa não atendida pela chuva. |
| Veranico | `dry_spell` | Sequência de dias sem chuva significativa. |
| Cenário | `Scenario` | pessimista / normal / otimista. |
| Margem | `margin` | Receita − custo total. |
| Basis | `basis` | Diferença preço local − referência (B3/CBOT). |

## Bounded contexts

```
                    ┌──────────────────┐
                    │  Decision Engine  │  (LLM: orquestra + explica)
                    └────────┬─────────┘
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                     ▼
┌──────────────┐    ┌──────────────┐      ┌──────────────┐
│  Climate     │    │  Yield       │      │  Cost /      │
│  (índices)   │───▶│  Estimation  │◀────│  Finance     │
└──────────────┘    └──────────────┘      └──────────────┘
        ▲                    ▲                     ▲
┌──────────────┐    ┌──────────────┐      ┌──────────────┐
│  Soil        │    │  Crop /      │      │  Market      │
│              │    │  Cultivar    │      │              │
└──────────────┘    └──────────────┘      └──────────────┘
        ▲                    ▲
┌──────────────┐    ┌──────────────┐
│  Units       │ (kernel compartilhado — sem dependências)
└──────────────┘    │  Disease     │
                    └──────────────┘
```

`units` é **shared kernel**: sem dependências, usado por todos. Erro de unidade é a
falha silenciosa mais comum em software agrícola — por isso é um contexto próprio,
não constantes espalhadas.

## Agregados principais (V1+)

- **Farm** (raiz) → `Plot[]`, `CarRegistry`, `Address(geom)`, `SeasonHistory[]`.
- **Plot** → `Geometry`, `SoilAnalysis[]`, `ManagementRecord[]`, `HarvestRecord[]`.
- **Season** → `Crop`, `Cultivar`, `PlantingDate`, `Costs`, `Yield`.

## Invariantes / regras (exemplos)

- Toda `Yield` carrega unidade; conversão sc/ha↔kg/ha passa **sempre** por `units`.
- Toda estimativa de produtividade expõe `point_estimate` **e** `interval` + `scenarios`.
- `Crop.base_temperature` é obrigatória para cálculo de GDD (soja ≈ 10 °C; milho ≈ 10 °C).
- `HarvestRecord` (colheita real informada pelo produtor) é o *ground truth* do flywheel
  e nunca é sobrescrito por estimativa.
