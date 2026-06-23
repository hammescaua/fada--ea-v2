# FADA V2 — Visão, Análise Crítica e Plano de Evolução

> Documento estratégico (CTO/produto) para a próxima versão do FADA.
> Mantém os princípios da V1 — **determinismo auditável, incerteza honesta, data flywheel,
> monólito modular, baixa fricção** — e responde a uma pergunta só:
> **o que de fato faz o agricultor do Noroeste do RS voltar a usar a ferramenta?**

---

## 0. Princípio que governa tudo na V2

A V1 provou uma tese: dá para construir um sistema de decisão agrícola **acurado e
honesto** (intervalos calibrados, nada de número inventado por LLM). Mas a V1 é, hoje,
uma **excelente demonstração com dados reais** — não um produto que um agricultor usa
toda semana na safra.

**A V2 não é "mais features". É a transição de _demo_ para _uso real_.** Todo item abaixo
é avaliado por um único critério: *isto faz um produtor real capturar dado e tomar uma
decisão melhor?* Se não, é descartado — por mais "tecnológico" que seja.

---

## 1. Diagnóstico honesto da V1

| Dimensão | Estado | Veredito para a V2 |
|---|---|---|
| Modelo regional (Ridge, MAE 6,96, calibrado) | Forte e on-principle | **Manter**, evoluir o método (ver §4) |
| Personalização (shrinkage bayesiano) | Forte, mas **nunca testada em fazenda real** | **Validar com dado real** é prioridade |
| Incerteza calibrada | Diferencial científico real | **Manter e levar para o nível de fazenda** |
| Plantio / custo / decisão | Bons, determinísticos | Manter; conectar a dados ao vivo |
| Dados climáticos | **Só reanálise histórica** (passado) | **Lacuna crítica:** falta previsão/tempo real |
| Monitoramento na safra | Plano × real manual | **Lacuna:** falta sensoriamento sem esforço |
| Interface | Web Next.js, mobile-first | Boa, mas **não é onde o agricultor está** |
| Flywheel | Estruturado, **mas vazio** (0 fazendas reais) | **A V2 só vale se o flywheel girar** |
| Cultura/região | Só soja, Três Passos | Expandir **com cautela** (revalidar) |

**Conclusão do diagnóstico:** a V1 tem o *cérebro* certo. Falta o *corpo* — sentidos
(dados ao vivo), pele (chegar onde o produtor está) e memória (dado real de fazenda).

---

## 2. A aposta central da V2 (se for escolher UMA coisa)

> **Fazer o flywheel girar de verdade**: 3 a 5 fazendas-piloto reais no Noroeste do RS
> capturando dado com **fricção quase zero**, alimentadas por **inteligência que chega
> sozinha** (alertas e monitoramento), durante uma safra completa.

Tudo na V2 serve a isso. Sem fazenda real, a personalização e a calibração-em-nível-de-
fazenda (a maior limitação científica declarada no relatório) **nunca saem do papel**.

---

## 3. Iniciativas priorizadas (cada uma passou pelo crivo "questione antes de implementar")

Notação: ✅ implementar na V2 · 🟡 adiar/condicional · ❌ descartar.

### ✅ 3.1 Previsão do tempo e alertas acionáveis (a maior lacuna)
- **Necessidade do agricultor:** "vai gear? tem janela pra pulverizar? vem veranico?"
- **O quê:** integrar **previsão** (Open-Meteo Forecast, INMET) ao lado da reanálise; gerar
  **alertas nomeados e auditáveis** (geada em N dias, janela de pulverização, risco de
  chuva na colheita), no mesmo estilo "sem score mágico" da V1.
- **Crítica/risco:** previsão erra — então **comunicar com probabilidade/confiança**, nunca
  como certeza. Coerente com o princípio de incerteza.
- **Veredito:** núcleo da V2. Transforma o FADA de retrospectivo em **proativo**.

### ✅ 3.2 Sensoriamento por satélite (NDVI) — inteligência sem esforço do produtor
- **Necessidade:** "como está minha lavoura agora, sem eu medir nada?"
- **O quê:** índices de vigor (NDVI/EVI) do **Sentinel-2** (gratuito via Copernicus/Sentinel
  Hub/Earth Engine) por talhão, com série temporal e detecção de anomalia.
- **Por que é forte:** valor altíssimo, **zero fricção** (o produtor não digita nada), e
  alimenta o flywheel com dado espacial real.
- **Crítica:** nuvem atrapalha; resolução 10 m não vê detalhe fino. Tratar como **indicador
  de atenção** ("olhe o talhão X"), não diagnóstico.
- **Veredito:** alto impacto, baixo atrito. Entra.

### ✅ 3.3 Chegar onde o produtor está: WhatsApp + PWA offline-first
- **Necessidade:** conectividade rural é ruim; o produtor vive no WhatsApp, não num app web.
- **O quê:** (a) **PWA offline-first** (captura sem sinal, sincroniza depois); (b) **bot de
  WhatsApp** para captura por **voz/foto/texto** ("plantei o talhão da sede hoje") e para
  **receber alertas**.
- **Tecnologia nova com propósito:** LLM para **extrair dado estruturado** de mensagem livre
  (voz→texto→evento). O LLM **estrutura entrada**, não gera número — princípio preservado.
- **Crítica:** WhatsApp Business API tem custo/burocracia; começar com um número simples.
- **Veredito:** é o que destrava adoção real. Entra (PWA primeiro, WhatsApp logo após).

### ✅ 3.4 Validar a personalização e a calibração **em fazenda real**
- **Necessidade:** honestidade científica — a V1 só calibrou com município como proxy.
- **O quê:** com os pilotos, medir cobertura dos intervalos **no nível de fazenda**; fechar
  a limitação central do relatório.
- **Veredito:** é o experimento que dá à V2 valor científico novo (não só de engenharia).

### ✅ 3.5 Contas + LGPD (pré-requisito de uso real)
- **Necessidade:** dado de fazenda é sensível; uso real exige login e privacidade.
- **O quê:** autenticação, multi-tenant, consentimento e política de dados (LGPD).
- **Veredito:** chato, porém **inegociável** para sair do modo demo.

### 🟡 3.6 Preço e comercialização ("quando vender?")
- **Necessidade:** margem não é só produzir, é vender bem.
- **O quê:** série de preços (CEPEA), break-even já existente + cenários de venda.
- **Crítica:** prever preço é traiçoeiro — **não** prometer previsão de preço; oferecer
  **cenários e contexto**, não um "vai subir/cair".
- **Veredito:** adiar para V2.1; entra como **decisão sob cenários**, nunca como palpite.

### 🟡 3.7 Triagem de pragas/doenças por foto
- **Necessidade:** "que mancha é essa na folha?"
- **O quê:** visão computacional para **triagem** (sugerir possibilidades + encaminhar a
  agrônomo), nunca diagnóstico fechado.
- **Crítica:** risco de erro e de responsabilidade agronômica; exige cautela e disclaimer.
- **Veredito:** V2.2, e sempre como **triagem assistiva**, não laudo.

### 🟡 3.8 Expansão multi-cultura (milho, trigo) e mais municípios
- **Crítica:** a arquitetura já é parametrizável, mas **cada cultura/região precisa
  revalidação temporal** antes de comunicar número. Sem isso, viraria falsa precisão.
- **Veredito:** expandir **uma cultura por vez, com backtest próprio**. Milho safrinha é o
  candidato natural depois da soja.

### ❌ 3.9 O que descartar (premature/contra-princípio)
- **Hardware/IoT proprietário:** capital-intensivo, fora da alavanca de software. (Se o
  produtor já tem sensor, integra-se; não se constrói.)
- **Microsserviços agora:** complexidade distribuída sem necessidade de escala. Monólito
  modular ainda é o certo.
- **Deep learning para o número de produtividade:** dados e interpretabilidade não
  justificam. (DL entra só em visão/satélite, onde faz sentido.)
- **"Score único de prioridade" / prescrição agronômica fechada:** continua proibido —
  destrói confiança e assume responsabilidade indevida.
- **Multiagente pelo hype:** ver §5.

---

## 4. Evolução do método estatístico (simplificar **e** melhorar ao mesmo tempo)

Hoje a V1 tem **três peças separadas**: Ridge regional + correção de viés por shrinkage +
intervalos conformais. Funciona, mas são três mecanismos.

**Proposta V2 — modelo hierárquico bayesiano (partial pooling):**
- Um **único modelo** em que fazenda "empresta força" da região (pooling parcial) → a
  personalização e o encolhimento passam a ser **nativos**, não um pós-processamento.
- Incerteza **distribucional nativa** (posterior preditiva) → intervalos calibrados saem
  do próprio modelo; a calibração empírica vira **verificação**, não construção.
- **Mantém interpretabilidade** (coeficientes com sentido agronômico) e o princípio
  determinístico (treino offline, artefato versionado).

Isto é **menos peças e mais poder** — o tipo de mudança que vale a pena (não complexidade
pelo hype). Tecnologias: PyMC/NumPyro (bayesiano) ou abordagem de efeitos mistos.

> ⚠️ Crivo: só adotar se, no backtest, **igualar ou superar** a calibração atual (IC80 ≈
> 79%). Caso contrário, mantém-se a stack da V1. Honestidade > elegância.

---

## 5. A pergunta "agentes / LLM": resposta crítica

O relatório e o briefing flertam com "multiagente". **Posição honesta:** não adicionar
agentes pelo marketing. Mas existe um uso de **camada agêntica que respeita os princípios**:

**Adotar (✅): orquestração agêntica determinística-first.**
- Um **agente orquestrador** que **planeja chamadas de ferramentas** determinísticas
  (estimar, otimizar plantio, custo, NDVI) e **explica** — exatamente como a V1, porém
  agora **proativo**: roda **monitores** que disparam quando algo muda (geada chegando,
  NDVI caindo, veranico previsto) e **avisa o produtor** no WhatsApp.
- **Extração estruturada** de entrada livre (voz/foto/texto) por LLM.
- **RAG agronômico** (Embrapa/ZARC) para o assistente **explicar com fonte citada** — sem
  gerar número.

**Não adotar (❌):** "vários agentes de IA" gerando números/recomendações de forma opaca.
Continua valendo: **o LLM coordena e comunica; o domínio determinístico decide os números.**

Resumo: a V2 é **mais agêntica em comportamento** (proativa, multimodal) sem trair o
determinismo. "Agente" = quem **planeja e age com ferramentas**, não quem **inventa o
número**.

---

## 6. Arquitetura V2 (evolução, não revolução)

```
[ Canais ]      WhatsApp bot  ·  PWA offline-first  ·  Web (Next.js)
                         │
[ Orquestração ]  Agente (tool-calling) + Monitores proativos (scheduler)
                         │
[ Serviços ]   regional · plantio · custo · decisão · NDVI · clima/alertas · preço
                         │
[ Domínio ]    determinístico e puro (agronomia · estatística · finanças)   ← intacto
                         │
[ Ingestão ]   IBGE · NASA/Open-Meteo (hist+forecast) · Sentinel-2 · INMET · CEPEA
                         │
[ Dados ]      PostgreSQL + PostGIS (espacial) · TimescaleDB (séries) · object storage
```

Mudanças-chave:
- **Banco:** migrar de SQLite para **Postgres + PostGIS** (dado espacial de talhão/satélite)
  e séries temporais. Continua um deploy só.
- **Scheduler/jobs:** para monitores proativos (alertas, refresh de NDVI) e re-treino.
- **MLOps leve:** monitorar **drift** e **calibração ao longo do tempo** conforme o flywheel
  cresce (a calibração pode degradar; precisa vigilância).
- **Mantém o monólito modular** — extrai-se serviço só quando a escala exigir.

Tecnologias novas (com propósito, não por moda): Postgres/PostGIS, TimescaleDB, um
job-runner (ex.: APScheduler/Celery), Sentinel Hub/Earth Engine, WhatsApp Cloud API,
PyMC/NumPyro (modelo hierárquico), camada RAG (vetor) só para conhecimento, não para números.

---

## 7. O que remover / otimizar

- **Consolidar telas:** a V1 acumulou muitas páginas; a V2 deve ir para o fluxo
  **orientado a tarefa** (a "tela única" que a V1 começou) — menos navegação, mais decisão.
- **Unificar o método estatístico** (§4): três peças → um modelo hierárquico.
- **Aposentar dados/telas de demonstração** quando houver fazenda real.
- **Reduzir fricção de captura ao limite**: voz e foto no lugar de formulários.

---

## 8. Métricas de sucesso (centradas no agricultor, não em vaidade técnica)

1. **Nº de fazendas reais ativas** numa safra (meta inicial: 3–5 pilotos).
2. **Dado de verdade-terreno capturado por fazenda** (colheita registrada / safra).
3. **Retenção ao longo da safra** (o produtor volta?).
4. **Decisões efetivamente tomadas** com base num alerta/recomendação.
5. **Calibração no nível de fazenda** (fecha a limitação científica da V1).
6. **Tempo para registrar um evento** (meta: < 20 s por voz/foto).

Repare: nenhuma métrica é "acurácia do modelo" isolada. Acurácia sem adoção é nada.

---

## 9. Faseamento sugerido

**V2.0 — Fundação para uso real (destravar adoção)**
- Previsão + alertas (§3.1) · NDVI Sentinel-2 (§3.2) · PWA offline + captura por voz/foto
  (§3.3) · contas + LGPD (§3.5) · Postgres/PostGIS · recrutar 3–5 pilotos.

**V2.1 — Inteligência mais profunda**
- Modelo hierárquico bayesiano (§4) · monitores proativos + WhatsApp (§3.3/§5) ·
  validação de calibração em fazenda (§3.4) · preço/comercialização sob cenários (§3.6).

**V2.2 — Expansão**
- Milho/trigo com backtest próprio (§3.8) · RAG agronômico com citação · triagem de
  pragas por foto (§3.7) · MLOps de drift/calibração.

---

## 10. Riscos e como não trair os princípios

| Risco | Mitigação |
|---|---|
| Virar "app de features" sem adoção | Tudo medido por adoção/flywheel (§8) |
| LLM/agentes gerando número | Regra dura mantida: domínio decide número; LLM coordena/explica |
| Previsão/preço vendidos como certeza | Sempre com probabilidade/cenário e disclaimer |
| Expansão sem revalidar | Uma cultura/região por vez, com backtest temporal |
| Dado real → privacidade | LGPD desde o V2.0, consentimento explícito |
| Calibração degradando no tempo | Monitoramento de drift/calibração (MLOps leve) |

---

## 11. Primeiro passo concreto

1. Criar o repositório `fada--ea-v2` a partir do `v1` (passos no chat).
2. Colocar este documento como `docs/VISAO_V2.md`.
3. Abrir issues para as iniciativas V2.0 (§3.1, §3.2, §3.3, §3.5) e o spike do modelo
   hierárquico (§4).
4. Em paralelo (o mais importante): **mapear 3–5 produtores reais** dispostos a pilotar —
   porque é o produtor, e não o código, que define a V2.
