# Capítulo 7 — O backend por dentro (o cérebro, função por função)

Este é o capítulo mais longo, porque o backend é onde mora a inteligência. Vou primeiro
mostrar o **padrão** (que se repete em tudo) e depois passar por **cada
funcionalidade**, dizendo o que faz, quais arquivos a compõem e a ideia-chave.

## O padrão que se repete (entenda uma vez, entendeu todas)

Quase toda funcionalidade tem **4 arquivos** que conversam, um por camada:

```
1. routes/XXXX.py     (API)      → o endereço. Recebe o pedido, devolve a resposta.
2. schemas/XXXX.py    (formato)  → define os dados que entram/saem (Pydantic).
3. services/XXXX.py   (gerente)  → busca dados no banco e chama as contas.
4. domain/XXXX/...    (contas)   → a conta pura (sem banco, sem internet).
```

Exemplo com **custo**:
- `routes/cost.py` recebe "quero o custo da safra 5".
- `schemas/cost.py` define como é a resposta (total, por hectare, etc.).
- `services/cost.py` busca os eventos da safra 5 no banco.
- `domain/cost/engine.py` soma os custos e calcula custo/ha, custo/saca, ponto de
  equilíbrio.

Guardando esse padrão, vamos às funcionalidades. (Vou agrupar por assunto.)

---

## A. O "liga" e a configuração

- **`app/main.py`** — o **arranque** do backend. Cria a aplicação FastAPI, liga o
  **CORS** (uma permissão de segurança que deixa o frontend conversar com o backend —
  sem ela dá o famoso erro "não foi possível conectar"), prepara o banco e junta todos
  os endpoints. Também cria uma página simples na raiz `/` com links úteis.
- **`app/core/config.py`** — as **configurações**: endereço do banco, origens
  permitidas no CORS, qual modelo de LLM usar. Lê de "variáveis de ambiente" (ajustes
  que ficam fora do código, por segurança e flexibilidade).

---

## B. Fundações de domínio (peças que todos usam)

### Units — conversões (`domain/units/`)
A unidade comercial da soja é a **saca** (= 60 kg). Converter saca ↔ quilo e
produtividade kg/ha ↔ sacas/ha **parece bobo, mas erro de unidade é a falha número 1**
em software agrícola. Por isso isso ganhou um "contexto" próprio, testado, em vez de
números mágicos espalhados. (`measures.py`)

### Climate — índices de clima (`domain/climate/`)
Transforma dados crus de clima em **índices** que importam para a soja:
- **Déficit hídrico** no período reprodutivo (quanto faltou de água na fase crítica) —
  o fator nº 1 de quebra de safra no RS.
- **Veranico** (maior sequência de dias secos), **dias acima de 35 °C** (calor que
  prejudica), **chuva acumulada**.
- Também calcula a **evapotranspiração** (quanta água a planta "perde") por uma fórmula
  consagrada (Hargreaves). (`indices.py`)

### Crop — calendário da soja (`domain/crop/`)
Define as **fases da planta** (fenologia) e o **calendário** (quando é a janela de
plantio recomendada, quando é o período reprodutivo). Serve para saber **onde** medir o
estresse climático. (`calendar.py`)

### Features — os "ingredientes" do modelo (`domain/features/`)
"Feature" é cada **ingrediente** que entra no modelo de previsão. O FADA usa um conjunto
**enxuto e defensável** (4 índices climáticos + a tendência tecnológica do ano). Por que
poucos? Porque com pouco dado, muitos ingredientes fazem o modelo "decorar" ruído.
(`soybean.py`)

---

## C. A previsão de produtividade (o modelo principal)

### Yield estimation (`domain/yield_estimation/` + `services/regional_intelligence.py`)
É o coração do MVP. Responde: *"quanto vou colher e com qual risco?"*

- **`predictor.py`** carrega o **modelo treinado** (um arquivo JSON com os "pesos") e
  aplica a fórmula. Como a safra futura ainda não tem clima conhecido, ele usa a
  **climatologia** (o histórico de clima do município) para montar **3 cenários**:
  pessimista, normal e otimista. Tudo só com NumPy (rápido e leve).
- **`risk.py`** transforma os números em **riscos legíveis** ("déficit hídrico no
  enchimento é o principal risco; em anos ruins a queda chega a ~28%").
- **`services/regional_intelligence.py`** é o gerente: resolve o município pelo nome,
  chama o predictor, monta os cenários, riscos, a janela de plantio, e adiciona o bloco
  **"como chegamos nisso"** (quantos anos de dados, método, base do intervalo).
- **Endpoint:** `POST /api/v1/regional-intelligence`.

**Ideia-chave:** o modelo separa **tecnologia** (a produtividade sobe ao longo das
décadas por genética/manejo) de **clima** (a variação de cada ano). Assim ele não
confunde "ano de seca" com "fazenda ruim".

---

## D. "E se eu plantar em outra data?" (Planting What-If)

### Planting date (`domain/planting_date/` + `services/planting_date.py`)
Responde: *"qual a melhor data de plantio?"* e *"e se eu plantar 10 dias antes?"*

- **`phenology.py`** calcula, por **soma de calor** (graus-dia), quando cada fase da
  planta acontece se você plantar numa certa data. Plantar mais cedo (mais frio) atrasa
  o desenvolvimento de forma **não-linear** — e o FADA modela isso.
- **`simulation.py`** faz um **"backtest climatológico"**: re-joga a data escolhida
  contra **cada ano histórico** e vê a distribuição de resultados. A otimização não
  escolhe a maior média, e sim a melhor combinação de **alta produtividade + baixo
  risco** (um "equivalente-certeza" com aversão a risco).
- **Endpoints:** `POST /planting-date-simulation` e `POST /planting-window-optimization`.

**Ideia-chave honesta:** o sistema diz claramente que isso captura a dimensão de
**risco climático** da data, não o potencial intrínseco — por isso só recomenda datas
**dentro da janela oficial (ZARC)**.

---

## E. O Gêmeo Digital da fazenda (registro de dados)

### Farm (`domain/farm/` + `services/farm.py` + `infra/`)
São as **"coisas" da fazenda** que o produtor registra:
- **Farm** (fazenda), **Field** (talhão), **CropCycle** (uma safra completa de um talhão),
  **YieldObservation** (a colheita real informada). (`entities.py`)
- **AgriculturalEvent** (uma operação: plantio, pulverização, adubação…), com tipo,
  data, produto, custo. (`events.py`)
- **EventPreset** (uma "operação favorita" salva, para registrar rápido). (`preset.py`)
- **Endpoints:** criar/listar fazendas, talhões, safras, eventos, observações.

**Ideia-chave ("eventos > estados"):** a safra é uma **sequência de operações**. Em vez
de dezenas de tabelas rígidas, há **uma** tabela flexível de eventos, e o estado
(custo, nº de aplicações) é **calculado a partir dos eventos**. Isso é "orientado a
eventos", mas **sem** a complicação de "event sourcing".

### Captura rápida (`services/capture.py` + `routes/capture.py`)
O **registro em poucos toques**: aplicar uma operação (de um preset) a **vários
talhões de uma vez** (`POST /quick-log`). Reduz o atrito — o combustível do flywheel.

### Catálogo de produtos (`domain/catalog/`)
Um cadastro de **insumos** (produtos), para reaproveitar nomes. Sem preços dinâmicos —
só estrutura, por enquanto.

---

## F. O Cost Engine (o "contador")

### Cost (`domain/cost/engine.py` + `services/cost.py`)
Responde: *"quanto gastei, quanto custa por hectare, quanto para empatar, quanto vou
lucrar?"*
- Soma os custos dos eventos → **custo total**, **custo por hectare**, **custo por saca**.
- **Break-even**: a produtividade mínima para "empatar" (cobrir o custo), dado um preço.
- **Análise de cenários**: junta **custo** (dos eventos) + **preço** (informado por
  você) + **produtividade** (do modelo) → lucro e margem em cada cenário.
- **Endpoints:** `GET /crop-cycles/{id}/cost` e `POST /crop-cycles/{id}/financials`.

**Ideia-chave honesta:** o FADA **não prevê preço de mercado** (isso é quase impossível
de forma confiável). O **preço é informado por você**; o sistema só faz as contas.

---

## G. Planejamento e Orçamento (Plano × Realizado)

### Planning (`domain/planning/` + `services/planning.py`)
Responde: *"estou no orçamento? quanto falta investir? estou seguindo meu plano?"*
- **PlannedEvent** = uma operação **planejada** (espelho do evento real). (`entities.py`)
- **Plano × Realizado** = compara o planejado com o gasto real (variância, % consumido,
  quanto falta). (`budget.py`)
- **Agenda** = a lista de operações por status (concluída / atrasada / próxima),
  derivada dos planejados vs. realizados.
- **Projeção de custo** = "real + o que ainda falta no plano" (não uma extrapolação
  linear, que seria especulação).
- **Endpoints:** `.../planned-events`, `.../plan-vs-actual`, `.../agenda`,
  `.../cost-projection`.

**Ideia-chave:** o `PlannedEvent` **unifica três coisas** numa só (planejamento,
orçamento e agenda) — economia elegante de complexidade.

---

## H. Personalização por fazenda (Adaptive Intelligence)

### Adaptive (`domain/adaptive/` + `services/adaptive.py`)
Responde: *"minha fazenda produz acima ou abaixo da média da região?"* — e usa isso
para **ajustar** a previsão regional para a sua fazenda.
- A cada safra real informada, o FADA calcula o **resíduo** (quanto a fazenda fugiu da
  expectativa regional **do mesmo ano** — assim não confunde fazenda com clima).
- Com poucas safras, ele **quase não ajusta** (é cético); com muitas safras
  consistentes, ajusta mais. Isso é o **encolhimento bayesiano** (*shrinkage*): puxa o
  ajuste para perto de zero quando há pouca evidência. (`shrinkage.py`)
- **Garantia matemática provada e testada:** a personalização **nunca estreita** o
  intervalo de incerteza artificialmente (a incerteza do clima do ano é irredutível).
- **Endpoints:** `.../performance-profile` e `POST /personalized-intelligence`.

**Ideia-chave:** personalizar **move o centro** da previsão, mas **mantém a faixa de
incerteza** — porque ninguém sabe se o ano que vem será seco.

---

## I. Calibração (medir se as faixas são honestas)

### Calibration (`domain/calibration/` + `services/calibration.py`)
Responde: *"posso confiar nos intervalos do FADA?"*
- Mede a **cobertura** (de quantas vezes a faixa de 80% conteve a realidade) com uma
  **barra de erro** (intervalo de Wilson) — porque a própria medição tem incerteza.
- Mede a **nitidez** (largura das faixas — faixa larga demais é inútil) e desenha o
  **diagrama de confiabilidade** (esperado × observado).
- Tudo é calculado por um pipeline offline (Capítulo 8); o backend só **lê o relatório**.
- **Endpoint:** `GET /calibration`.

**Resultado real e honesto:** o intervalo de 80% conteve a produtividade em **~79%** das
safras → **calibrado**. (Descartou-se uma métrica famosa, o CRPS, por ser redundante —
um exemplo de "menos é mais".)

---

## J. Inteligência por Talhão e Insights

### Insights (`domain/insights/` + `services/insights.py`)
Responde: *"qual talhão produz melhor? qual é mais instável? onde o custo cresce?"*
- Resume cada talhão (produtividade, **estabilidade** medida sobre os resíduos
  ajustados ao clima, custo). (`summary.py`)
- Gera **insights** com **evidence gating**: só afirma algo se houver **dados
  suficientes** (N de safras) e tamanho de efeito. (`engine.py`)
- **Endpoints:** `.../field-analytics` e `.../insights`.

**Ideia-chave:** o sistema **prefere o silêncio à especulação** — não inventa insight de
dado ralo. (Por isso, "cultivar" e "personalização por talhão" foram **adiados**: ainda
não há dado suficiente para fazer isso de forma honesta.)

---

## K. Apoio à Decisão (onde olhar primeiro)

### Decisions (`domain/decisions/` + `services/decisions.py`)
Responde: *"qual talhão merece atenção?"*
- **NÃO** cria um "score único" mágico (que seria falsa precisão). Em vez disso, cada
  talhão dispara **alertas nomeados** ("custo 35% acima da mediana", "20% abaixo da
  meta", "orçamento estourado"), cada um com a evidência. (`model.py`, `engine.py`)
- O nível de atenção (alta/média/saudável) é a **severidade máxima** dos alertas — e dá
  para clicar e ver exatamente quais.
- Também faz **rankings** (uma dimensão por vez, sem misturar).
- **Endpoint:** `GET /farms/{id}/decisions`.

**Ideia-chave:** evita o "semáforo mágico". A cor sempre tem **explicação nomeada** atrás.

---

## L. O Assistente conversacional (Orchestrator)

### Engine (`engine/orchestrator.py` + `engine/explainer.py` + `services/assistant via routes`)
Responde perguntas em **linguagem natural**.
- O **orchestrator** entende a intenção da pergunta (por regras determinísticas, e
  opcionalmente pelo LLM) e **roteia** para o serviço certo (custo, decisão, plano…).
- O **explainer** transforma os números numa frase. Tem uma versão por **regra fixa**
  (sem LLM) e outra com **Claude** (se houver chave).
- **Regra de ferro:** o LLM **nunca** gera número. Tudo vem dos serviços.
- **Endpoint:** `POST /assistant`.

---

## M. Plataforma (robustez e "primeiro acesso")

- **`services/system.py`** + `routes/system.py` — o **status** do sistema (banco ok?
  modelo ok? quantos registros?). Endpoint `GET /system/status`.
- **`services/dashboard.py`** — junta atenção + orçamento + agenda + insights para a
  tela **Início**. Endpoint `GET /farms/{id}/dashboard`.
- **`services/demo.py`** — cria uma **fazenda de demonstração** (com histórico, plano,
  custos) para o sistema nunca parecer vazio. Endpoint `POST /demo/seed`.
- **`routes/export.py`** — **exporta** as operações em CSV (planilha). Endpoint
  `GET /farms/{id}/operations.csv`.

---

## Os testes (a rede de segurança)

A pasta `app/tests/` tem **164 testes** automáticos. Cada um confere uma pequena
verdade (ex.: "60 sacas = 3600 kg", "a personalização nunca estreita o intervalo",
"plantar mais quente acelera as fases"). Rodar `pytest` e ver tudo verde é a garantia
de que uma mudança não quebrou nada. Alguns testes são **property-based** (testam uma
regra com **milhares** de entradas aleatórias — ex.: a garantia do intervalo).

## Resumo do capítulo

O backend é um conjunto de funcionalidades, cada uma seguindo o padrão **API →
schema → serviço → domínio**. As contas finas vivem no **domínio** (puro e testado). O
LLM vive só no `engine`. Tudo é determinístico, honesto e coberto por 164 testes.

➡️ Próximo: **[Capítulo 8 — Dados e modelos](08-dados-e-modelos.md)** (de onde vêm os
números).
