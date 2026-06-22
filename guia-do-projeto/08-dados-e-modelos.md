# Capítulo 8 — Os dados e os modelos (de onde vêm os números)

Tudo que o FADA "sabe" sobre a região vem de **dados reais e públicos**, processados por
"receitas" chamadas **pipelines**. Este capítulo explica essa base científica.

## De onde vêm os dados (as fontes públicas)

O FADA usa **conectores** (em `backend/app/data/connectors/`) que baixam dados de
serviços públicos:

| Fonte | O que fornece | Arquivo |
|---|---|---|
| **IBGE** (PAM) | produtividade histórica de soja por município (desde 1974) | `ibge.py` |
| **NASA POWER** | clima diário por ponto (satélite), desde 1981 | `nasa_power.py` |
| **Open-Meteo** | clima diário (reanálise), desde 1940 | `open_meteo.py` |
| **CONAB** | séries de safra (suplementar, "best-effort") | `conab.py` |

- **`base.py`** é o conector "base" que todos usam: faz a chamada à internet, guarda o
  resultado em **cache** (para não baixar de novo toda hora) e **tenta de novo** se a
  internet falhar (com espera crescente).

**Por que duas fontes de clima (NASA + Open-Meteo)?** Robustez. Se uma falhar (ex.:
limite de requisições), o FADA usa a outra automaticamente. Foi exatamente isso que
permitiu reunir os 20 municípios sem furos.

## O "ground truth" (a verdade-terreno)

Para treinar um modelo de previsão, você precisa de **exemplos reais**: "neste ano, com
este clima, colheu-se tanto". Esse "tanto" real é o **ground truth** (verdade-terreno).
No FADA, ele vem do **IBGE** — produtividade municipal real de soja, ano a ano.

> Um dado real marcante: em **2022**, Horizontina colheu **1380 kg/ha** (≈ 23 sacas) —
> uma quebra brutal por causa da seca de La Niña. Em **2024**, **3300 kg/ha** (55 sacas).
> Essa diferença enorme é o "sinal" que o modelo aprende: clima ruim → colheita menor.

## Os pipelines (as receitas de preparo, rodadas "offline")

"Offline" significa: **não** rodam quando o usuário usa o app. Rodam de vez em quando,
quando se quer reconstruir os dados/modelos. Ficam em `backend/pipelines/`.

### 1. `build_dataset.py` — montar a tabela de treino
Para cada município da microrregião e cada ano: baixa o clima, calcula os índices
(déficit hídrico, veranico…), pega a produtividade real do IBGE, e monta **uma linha**
da tabela. Resultado: **787 linhas reais** salvas em
`data/features/soybean_tres_passos.csv`. (`region.py` define a região: microrregião
Três Passos, Noroeste RS.)

### 2. `train.py` — treinar e comparar modelos
Pega a tabela e **treina** três modelos (regressão linear, floresta aleatória, XGBoost),
comparando-os de forma **justa** (um teste chamado "deixe um ano de fora" — leave-one-
year-out — que simula prever um ano que o modelo nunca viu). Resultado: os três deram
quase o mesmo erro (~7 sacas/ha de erro médio), então escolheu-se o **linear**. O modelo
final é salvo como um **JSON inspecionável** em `data/models/soybean_regional_baseline.json`.
Os experimentos ficam registrados no **MLflow**.

### 3. `build_planting_grid.py` — preparar o "e se" de data de plantio
Pré-calcula, para várias datas de plantio × cada ano, os índices climáticos na janela
**recolocada** pela fenologia. Isso deixa a simulação de data **rápida** no app (o
trabalho pesado já foi feito antes).

### 4. `backtest_calibration.py` — medir a honestidade dos intervalos
Faz o "teste de volta no tempo" para verificar se as faixas de incerteza são honestas
(Capítulo 3). Gera o relatório `data/models/calibration_report.json`, que o app lê.

### Os `example_*.py`
Geram **exemplos reais** de saída (salvos em `examples/`), úteis para documentação e
para entender o que cada parte produz.

## O modelo treinado (o que tem dentro do JSON)

O modelo final **não** é uma caixa-preta misteriosa — é um arquivo JSON legível com:
- os **pesos** (quanto cada ingrediente pesa na conta),
- como **padronizar** os ingredientes,
- os **quantis dos resíduos** (que definem a largura do intervalo),
- a **climatologia** de cada município (para montar os cenários),
- e **metadados** (quantas linhas, quando foi treinado, qual o erro).

Os **pesos** confirmam a agronomia, e isso é lindo: o **déficit hídrico reprodutivo** é
o fator de maior peso e **negativo** (mais seca → menos colheita), e a **tendência do
ano** é positiva (a produtividade sobe com a tecnologia ao longo do tempo).

## Reprodutibilidade (ciência de verdade)

Um princípio científico é: **outra pessoa deve conseguir reproduzir seus resultados**. O
FADA cuida disso:
- **`params.yaml`** guarda os parâmetros (a região, os limiares, etc.).
- **`dvc.yaml`** descreve a "receita" completa (qual pipeline gera qual arquivo).
- **MLflow** registra cada experimento de treino.
- E o mais importante: o **modelo treinado, a tabela de dados e o relatório de
  calibração já vêm versionados** no projeto. Por isso o app **funciona out-of-the-box**
  (assim que você instala) — não precisa rodar os pipelines para usar.

## Resumo do capítulo

- Os dados vêm de **fontes públicas reais** (IBGE, NASA, Open-Meteo) via **conectores**
  com cache e fallback.
- A **verdade-terreno** (produtividade real do IBGE) treina o modelo.
- Os **pipelines** (offline) montam a tabela, treinam, comparam, e medem a calibração.
- O **modelo** é um JSON legível e auditável; os pesos confirmam a agronomia.
- Tudo é **reprodutível**, e o resultado já vem pronto no projeto.

➡️ Próximo: **[Capítulo 9 — O frontend por dentro](09-frontend-por-dentro.md)** (cada
tela).
