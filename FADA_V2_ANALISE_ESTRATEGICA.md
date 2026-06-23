# FADA V2 — Análise Estratégica Aprofundada

> **Companheiro crítico** do `FADA_V2_VISAO_E_PLANO.md`. Aquele documento continua válido nos
> princípios; **este o revisa em três pontos onde a estratégia muda de fato**:
> 1. o gargalo da V1 não é *canal*, é **valor no dia 1 sem depender de dado de fazenda**;
> 2. **dados públicos oficiais** (via `agrobr.dev`) deixam de ser "ingestão" e viram **o produto**;
> 3. **WhatsApp sai** do escopo (decisão do dono) — e isso é libertador, não limitante.
>
> Escrito na pele de **dois leitores**: o **agricultor** do Noroeste do RS (o usuário) e o
> **CTO/founder** (quem decide o que construir). Tudo é julgado por: *isto faz um produtor real
> tomar uma decisão melhor — e podemos construir sem esperar anos de dado próprio?*

---

## 0. Leitura honesta do que a V1 já é (do código, não do marketing)

Li o repositório inteiro. O que existe de verdade:

- **Domínio determinístico forte e testado** (26 arquivos de teste): features agroclimáticas
  em janelas fenológicas, custo/margem/break-even, otimização de plantio robusta (ZARC caseiro
  via GDD), encolhimento bayesiano Normal-Normal para personalização, e **calibração empírica
  honesta** (cobertura IC80 verificada por leave-one-year-out).
- **Modelo regional**: Ridge de **5 features** (déficit hídrico reprodutivo, veranico, dias
  quentes, chuva total, tendência de ano) treinado em **787 linhas** — ~10 municípios da
  microrregião Três Passos, soja, 1980–2024. MAE ~7 sc/ha, intervalos calibrados.
- **Orquestrador conversacional**: hoje é um **roteador por regex** (não um LLM) que mapeia ~20
  intenções para serviços determinísticos. O LLM é opcional e só explica.
- **Flywheel estruturado mas vazio**: entidades Fazenda/Talhão/Safra/Colheita existem, captura
  rápida existe, **0 fazendas reais**.

**Diagnóstico de uma frase:** a V1 é um *motor de decisão honesto e bem-arquitetado*, alimentado
por **um filete de dado público** (clima de reanálise + IBGE), preso a **uma cultura e uma
microrregião**, e **sem nenhum agricultor dentro**.

A pergunta certa para a V2 não é "como faço o agricultor capturar dado?" (isso é consequência).
É: **"como o FADA fica obviamente útil para esse agricultor na primeira semana, antes de ele
digitar qualquer coisa?"** A resposta a essa pergunta é o que destrava o flywheel — não o
contrário.

---

## 1. Na pele do agricultor — a jornada real e onde o FADA falha hoje

O produtor de soja de sequeiro de Três Passos, ao longo de uma safra, faz na prática estas
perguntas — em ordem de urgência sentida:

| Momento | A pergunta real dele | O FADA V1 responde? | O que falta |
|---|---|---|---|
| Pré-safra (set) | "Quanto vale a saca? Fecho preço agora ou espero?" | ❌ | **Preço (CEPEA) + futuros (B3) + basis** — hoje inexistente |
| Pré-safra | "Compro insumo agora? Quanto custou ano passado?" | parcial (custo manual) | **Custo de produção CONAB + preço de diesel/fertilizante** |
| Plantio (out–dez) | "Qual a janela ZARC do meu solo/ciclo? Tô dentro?" | parcial (ZARC **caseiro** por GDD) | **ZARC oficial** por município/solo/ciclo (MAPA) |
| Plantio | "Vai chover na semana que vem pra eu plantar?" | ❌ (só passado) | **Previsão** (Open-Meteo Forecast / INMET) |
| Vegetativo | "Como tá meu talhão sem eu ir lá?" | ❌ | **NDVI Sentinel-2** por talhão |
| Reprodutivo (jan–fev) | "Vem veranico? Risco de ferrugem?" | parcial (risco climático histórico) | **Alerta proativo de veranico/geada + ferrugem** |
| Sempre | "Que produto uso pra essa praga? Qual a carência?" | ❌ | **Agrofit (defensivos oficiais)** + RAG agronômico |
| Pós-colheita | "Produzi acima da média? Valeu o custo?" | ✅ (este é o ponto forte) | manter |

**Conclusão na pele do usuário:** o FADA hoje brilha **depois** da colheita (análise) e é fraco
**antes e durante** (decisão ao vivo) — que é exatamente quando o agricultor mais sente dor e
mais voltaria ao app. A V2 precisa empurrar o valor **para a frente da safra**.

E o ponto crítico: **quase tudo que falta na tabela acima é dado público oficial** — não exige
um único agricultor cadastrado. É construível já.

---

## 2. A virada estratégica: dados públicos oficiais **são** o produto (agrobr.dev)

A V1 trata dado público como "ingestão" para treinar um modelo. A V2 deve tratá-lo como **a
camada de valor entregue ao agricultor no dia 1**. O `agrobr.dev` (pacote Python, ~40 fontes
oficiais em DataFrames limpos, com *fallback* automático entre fontes) torna isso viável para
um founder solo — em vez de escrever e manter 15 conectores frágeis (como o stub atual da CONAB,
que hoje retorna vazio), você consome uma API unificada.

### 2.1 Mapa: fonte oficial → o que destrava no FADA

| Fonte (via agrobr) | Vira no FADA | Depende de dado de fazenda? | Prioridade |
|---|---|---|---|
| **CEPEA/ESALQ** (preços soja/milho) | "Quanto vale a saca hoje" + margem ao vivo no Financeiro | Não | 🟢 P0 |
| **B3 Futuros Agro** | Cenários de venda (sem *prever* preço) | Não | 🟡 P1 |
| **CONAB** (custo de produção, progresso de safra) | Benchmark de custo/ha regional + "como vai a safra no RS" | Não | 🟢 P0 |
| **ZARC** (janela oficial por município/solo/ciclo) | **Substitui o ZARC caseiro** por GDD pela fonte oficial | Não | 🟢 P0 |
| **INMET / NASA POWER** (estações, previsão) | Previsão + alertas (veranico/geada) | Não | 🟢 P0 |
| **IBGE/SIDRA PAM + LSPA** | Já usado (treino) — **expandir** para todo o RS/BR | Não | 🟢 P0 |
| **Agrofit/MAPA** (defensivos registrados) | "Que produto/dose/carência" com fonte oficial (via RAG) | Não | 🟡 P1 |
| **EMBRAPA Solos** (PronaSolos, SiBCS) | Tipo de solo do talhão → ciclo ZARC correto, AWC | Não | 🟡 P1 |
| **SICAR** (CAR, geometria do imóvel) | Importar o talhão **desenhando zero** (geometria pronta) | Não (só o CAR do produtor) | 🟡 P1 |
| **MapBiomas** (uso do solo anual) | Histórico de uso/rotação do talhão sem o produtor digitar | Não | 🔵 P2 |
| **INPE Queimadas / DETER** | Alerta de foco de calor próximo ao talhão | Não | 🔵 P2 |
| **BCB/SICOR** (crédito rural), **ANP** (diesel) | Contexto de custo/financiamento | Não | 🔵 P2 |

**Repare na coluna do meio:** quase nada depende de dado de fazenda. Essa é a tese central da
revisão — **o FADA pode ficar 5× mais útil sem recrutar um único piloto**, e *aí* o piloto vira
fácil porque o produto já entrega valor.

### 2.2 Princípio de engenharia para a integração

- `agrobr` entra como **dependência opcional de um connector** (`app/data/connectors/agrobr.py`),
  atrás da mesma interface `HttpDataSource`/connector que já existe — **não** vaza para o domínio.
- **Cache + versionamento (DVC já está no repo):** preço/clima mudam; reanálise/PAM não. Cachear
  agressivamente e **datar** toda resposta ("preço CEPEA de 2026-06-20"). Honestidade de dado =
  honestidade de número.
- **Degradação graciosa** (já é padrão do código): fonte fora do ar → o FADA diz o que **não**
  sabe, nunca inventa. O agrobr já faz *fallback* (ex.: CEPEA→Notícias Agrícolas) — alinhado.

> ⚠️ **Devida diligência antes de adotar:** validar licença de cada fonte que o agrobr expõe
> (várias são CC-BY, mas há CC-BY-NC e ODbL), a estabilidade de versão do pacote, e *fixar
> versão*. O agrobr é um **acelerador de ingestão**, não uma fonte de verdade — a fonte de
> verdade continua sendo o órgão oficial citado.

---

## 3. Diferenciação competitiva — onde o FADA ganha (e onde não brigar)

Os incumbentes (Aegro, Strider, Climate FieldView, Solinftec, aplicativos de cooperativa) são
fortes em **gestão operacional** (caderno de campo, máquinas, estoque, folha) e/ou exigem
**hardware/assinatura cara**. Eles são fracos exatamente onde o FADA é desenhado para ser forte:

| Eixo | Incumbentes | **Cunha do FADA** |
|---|---|---|
| Promessa de número | "Produtividade" sem dizer o erro | **Incerteza calibrada e auditável** (já é o diferencial científico) |
| Dado | Proprietário, preso à plataforma | **Síntese honesta de dado público oficial** — útil sem lock-in |
| Custo de entrada | Assinatura + às vezes hardware | **Útil no dia 1, de graça, sem sensor** |
| Foco | Operação (o que já aconteceu) | **Decisão sob incerteza** (o que fazer agora) |
| LLM | Chatbot que às vezes "alucina" número | **LLM coordena/explica; domínio decide o número** |

**A frase de posicionamento da V2:** *"O painel honesto da sua safra a partir de todo o dado
público oficial do agro brasileiro — com o erro sempre na mesa."* Não competir em caderno de
campo nem em telemetria de máquina. Competir em **inteligência de decisão confiável e
transparente** — o nicho que ninguém ocupa com honestidade.

---

## 4. Revisão crítica do plano anterior (o que muda e por quê)

### 4.1 ❌ WhatsApp — **fora do escopo** (decisão do dono)
O plano anterior tinha WhatsApp como ✅ núcleo (§3.3). **Removido.** Justificativa que *sustenta*
a decisão (não só acata):
- WhatsApp Business/Cloud API traz **custo, burocracia de aprovação e dependência de plataforma
  de terceiros** — atrito alto para um founder solo, e fora do controle.
- O valor que o WhatsApp prometia (chegar onde o produtor está, captura por voz/foto, alertas) é
  **majoritariamente entregue pelo PWA**: push notification nativo (alertas), câmera/microfone do
  device (voz/foto), e *offline-first*. Sem intermediário, sem custo por mensagem.
- **Canal da V2 = PWA instalável (offline-first) + Web.** É suficiente, é gratuito, e mantém
  todo o relacionamento dentro do produto.

> Se um dia houver demanda real e validada de notificação fora do app, o canal natural é
> **e-mail/Telegram bot** (gratuitos, sem aprovação), não WhatsApp. Mas **não agora**.

### 4.2 🔁 ZARC caseiro → ZARC oficial
A V1 implementa uma janela de plantio via **GDD próprio** (`build_planting_grid`). É elegante,
mas é **fonte caseira competindo com a fonte oficial**. Para o agricultor, "o que diz o ZARC do
MAPA" tem peso legal/de seguro que o GDD caseiro não tem. **Usar o ZARC oficial (agrobr) como
verdade** e manter o GDD apenas como *interpolador* para datas fora da grade oficial. Mais
honesto e mais útil (casa com crédito/seguro do produtor).

### 4.3 🔁 Método estatístico — **sequência antes de elegância**
O plano anterior propõe modelo **hierárquico bayesiano** (§4) para unificar Ridge + shrinkage +
conformal. Concordo com o destino, **discordo da ordem**. Com **10 municípios e 787 linhas**, o
ganho de um hierárquico é pequeno e o risco de complexidade é alto. A jogada de maior alavancagem,
**barata e imediata**, é:

1. **Expandir a base de treino via IBGE** de 10 municípios para **todo o RS (e depois Sul/BR)** —
   o agrobr/SIDRA já entrega isso. Centenas de municípios × 40 anos = dataset 1–2 ordens de
   grandeza maior, **de graça, sem fazenda**.
2. *Aí sim* o **hierárquico (município dentro de microrregião dentro de estado)** passa a valer a
   pena — é o caso de uso natural de *partial pooling*, e a personalização por fazenda entra como
   o nível mais baixo da mesma hierarquia quando os pilotos chegarem.
3. **Crivo mantido:** só promover o hierárquico se, no backtest, **igualar ou superar** a
   calibração atual (IC80 ≈ 79%). Honestidade > elegância.

> Ou seja: **expandir o dado primeiro melhora o modelo atual de imediato**; o bayesiano colhe
> esse dado depois. Inverter a ordem é resolver o problema difícil antes do fácil.

### 4.4 ✅ Mantém-se do plano anterior
Previsão + alertas, NDVI Sentinel-2, PWA offline-first, contas+LGPD, Postgres/PostGIS,
orquestração agêntica determinística-first, RAG com citação, validação de calibração em fazenda.

---

## 5. LLM e camada agêntica — onde aplicar (com princípio intacto)

Regra dura preservada: **o LLM coordena e comunica; o domínio determinístico decide o número.**
Dentro disso, há quatro usos de alto valor — dois já cabíveis na V2.0:

1. **Orquestrador por tool-calling (substitui o regex).** O roteador atual é ~200 linhas de regex
   frágil para ~20 intenções. Um LLM com *tool-calling* sobre os serviços existentes (estimar,
   otimizar, custo, NDVI, preço) entende linguagem livre muito melhor e **continua chamando as
   mesmas ferramentas determinísticas**. Risco: latência/custo → manter o roteador determinístico
   como *fallback* offline (já existe). **Alta alavancagem, baixo risco. Entra na V2.0.**

2. **RAG agronômico com citação obrigatória.** Conhecimento (não número): Agrofit (defensivos,
   dose, carência), bulas, ZARC, boletins Embrapa, Consórcio Antiferrugem. O assistente passa a
   responder "que produto para ferrugem, qual carência" **citando a fonte oficial** — nunca
   inventando. Casa perfeitamente com o princípio e é dor real do produtor. **V2.1.**

3. **Extração estruturada de entrada livre (voz/foto/texto).** "Apliquei fungicida no talhão da
   sede hoje" → evento estruturado. LLM **estrutura a entrada, não gera número**. Reduz fricção
   de captura a quase zero — alimenta o flywheel. **V2.1.**

4. **Briefing de safra gerado (LLM-as-writer, grounded).** Um resumo semanal em linguagem natural
   construído **exclusivamente sobre números já computados** pelo domínio (preço, NDVI, alerta de
   veranico, orçamento). O LLM redige; os números vêm prontos e citados. **V2.2.**

❌ **Continua proibido:** múltiplos "agentes de IA" gerando recomendação/número de forma opaca,
e qualquer prescrição agronômica fechada (vira responsabilidade indevida e destrói confiança).

---

## 6. Seja realista sobre os dados — o que o FADA **pode** e **não pode** dizer

Honestidade científica é o ativo da marca; então vale explicitar os limites na própria UI:

- **O modelo regional NÃO prevê a sua safra específica** — prevê o **rendimento médio municipal**
  esperado, com intervalo. É um *prior* regional honesto, não uma adivinhação do seu talhão.
- **Para a safra futura (2026/27) não há clima observado** — os cenários vêm da **climatologia
  histórica** (percentis). Com previsão (V2.0), parte disso vira observação conforme a safra anda.
- **NDVI a 10 m é indicador de atenção, não diagnóstico** — "olhe o talhão X", não "o talhão X
  tem doença Y". Nuvem atrapalha; comunicar lacunas.
- **Preço não se prevê** — mostrar preço **atual** (CEPEA) e **cenários** de futuros (B3), nunca
  "vai subir/cair".
- **Datar tudo.** Todo número público carrega a data da fonte. Um preço de duas semanas atrás
  apresentado como "hoje" é uma mentira silenciosa.

Esses limites não são fraqueza — **expostos com clareza, são a diferenciação**. É o que nenhum
concorrente faz.

---

## 7. Arquitetura V2 (revisada — sem WhatsApp, com agrobr)

```
[ Canais ]      PWA instalável (offline-first, push, câmera/voz)  ·  Web (Next.js)
                         │
[ Orquestração ]  Agente tool-calling (LLM) + Monitores proativos (scheduler)
                  └── fallback: roteador determinístico (já existe)
                         │
[ Serviços ]   regional · plantio(ZARC oficial) · custo · decisão · NDVI ·
               clima/alertas · preço/margem · RAG agronômico
                         │
[ Domínio ]    determinístico e puro (agronomia · estatística · finanças)   ← intacto
                         │
[ Ingestão ]   agrobr.dev (CEPEA·CONAB·ZARC·INMET·B3·Agrofit·SICAR·EMBRAPA Solos·
               MapBiomas·IBGE…) + Open-Meteo(hist+forecast) + Sentinel-2
                         │
[ Dados ]      PostgreSQL + PostGIS (talhão/satélite) · cache datado · DVC (artefatos)
```

Mudanças-chave: **Postgres+PostGIS** (espacial), **scheduler** (alertas/NDVI), **camada agrobr**
atrás de connectors, **MLOps leve** (drift/calibração no tempo). Continua **um deploy só** —
monólito modular. Nada de microsserviços.

---

## 8. Roadmap V2 revisado (sequenciado por *valor sem fazenda* → *valor com fazenda*)

**V2.0 — "Útil no dia 1" (zero dependência de piloto)**
> Tese: tornar o FADA obviamente valioso para qualquer produtor de soja do RS, antes de qualquer
> cadastro. É o que torna o recrutamento de pilotos fácil.
- Integração **agrobr**: CEPEA (preço/margem ao vivo), CONAB (custo benchmark), **ZARC oficial**.
- **Previsão + alertas** (Open-Meteo Forecast/INMET): veranico, geada, janela de pulverização.
- **Expandir base de treino IBGE** para todo o RS → re-treino e re-calibração do modelo atual.
- **Orquestrador tool-calling** (LLM) com fallback determinístico.
- **PWA offline-first** + push. Contas + **LGPD**. **Postgres/PostGIS**.

**V2.1 — "Inteligência sem esforço + primeiros pilotos"**
- **NDVI Sentinel-2** por talhão (import de geometria via **SICAR**; solo via **EMBRAPA**).
- **RAG agronômico** (Agrofit/Embrapa) com citação · **extração estruturada** voz/foto.
- Recrutar **3–5 pilotos** (agora com produto que já entrega valor) · validar calibração em
  fazenda · **monitores proativos**.

**V2.2 — "Profundidade e escala"**
- **Modelo hierárquico bayesiano** (município→microrregião→estado→fazenda), *se* bater a
  calibração atual.
- **Milho safrinha** com backtest próprio · **briefing de safra** gerado · B3 (cenários de venda)
  · risco de **ferrugem** (Consórcio Antiferrugem) · MLOps de drift.

---

## 9. Métricas de sucesso (revisadas)

Mantêm-se as do plano anterior (fazendas ativas, ground-truth capturado, retenção, decisões
tomadas, calibração em fazenda, tempo de registro) **e acrescenta-se uma métrica de "dia 1"**,
porque a V2.0 entrega valor antes de qualquer piloto:

7. **Valor sem cadastro:** nº de consultas úteis (preço, ZARC, alerta, estimativa) por visitante
   **antes** de criar fazenda. Se for alto, o produto "vende sozinho" e o flywheel destrava.

---

## 10. Primeiro passo concreto (spikes desta semana)

1. **Spike agrobr (1–2 dias):** instalar, validar licenças/versão, e provar 3 chamadas —
   **CEPEA soja**, **ZARC** (Três Passos/soja), **CONAB custo RS**. Critério: DataFrame limpo e
   datável, atrás de um connector novo, sem tocar no domínio.
2. **Spike expansão IBGE (1 dia):** puxar PAM de **todos os municípios do RS** e medir o ganho de
   MAE/calibração do modelo atual re-treinado. Critério: ≥ base atual em calibração.
3. **Spike previsão (1 dia):** Open-Meteo Forecast → primeiro **alerta de veranico** nomeado e
   auditável, com probabilidade. Critério: alerta honesto, nunca como certeza.
4. **Abrir issues** para V2.0 (§8) e marcar **WhatsApp como descartado** no plano anterior.
5. Em paralelo: **mapear 2–3 produtores** para a V2.1 — mas sem bloquear a V2.0 neles.

---

### Resumo de uma frase

> **A V1 construiu o cérebro honesto; a V2.0 dá a ele os sentidos do dado público oficial
> (agrobr) para ser útil no dia 1 — e é esse valor imediato, não um canal de mensagem, que
> finalmente faz o flywheel girar.**
