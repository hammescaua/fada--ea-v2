# Capítulo 9 — O frontend por dentro (cada tela do aplicativo)

O frontend é o que o produtor **vê e usa**. Vou explicar as peças fundamentais e depois
passar por **cada tela**.

## As peças fundamentais (a "fundação" do app)

### `lib/api.ts` — o "telefone" para o backend
Este arquivo concentra **todas as chamadas** ao backend. Para cada endpoint do cérebro,
há aqui uma função (ex.: `api.getDecisions(farmId)`). Também define os **tipos** (o
formato exato de cada dado), o que dá segurança. Ele tem um detalhe esperto: **normaliza
o endereço** do backend (remove barra extra ou `/api/v1` colocado por engano) — foi a
correção de um bug real de configuração.

### `lib/context.tsx` — a memória "Fazenda · Safra"
Esta é uma sacada de produto importante. Antes, cada tela pedia para você **re-selecionar
a fazenda** e até **digitar números de ID** (péssimo para o usuário final). O `context`
é uma **memória global**: você escolhe **Fazenda · Safra uma vez** (na barra do topo) e
**todas as telas** passam a usar essa escolha. E ela é **salva no navegador**
(localStorage), então sobrevive a recarregar a página.

### `components/context-bar.tsx` — a barra de seleção no topo
A barra que aparece no alto de todas as telas, onde você escolhe a Fazenda e a Safra
**pelo nome** (não por número). Ela até **seleciona sozinha** a primeira opção, para o
app nunca ficar "vazio".

### `app/layout.tsx` — a moldura comum
A "moldura" que envolve todas as páginas: o **menu** lateral (no computador) ou o **menu
inferior** (no celular), a barra de contexto, e o espaço onde a página entra.

### `app/providers.tsx` — liga as fundações
Liga o **React Query** (que busca dados) e o **contexto global** para todas as telas.

### `components/nav.tsx` — o menu
O menu foi **reorganizado por tarefa** (não por arquitetura): 5 destinos principais
(Início, Planejar, Minha Lavoura, Financeiro, Assistente), um grupo "Ferramentas"
recolhível com o resto, e um rodapé discreto. No celular, vira um **menu inferior** com
os 5 principais.

### `components/states.tsx` e `error.tsx`/`global-error.tsx` — robustez
- `states.tsx` tem os blocos de **"carregando…"** e **"deu erro"** usados em toda tela.
- `error.tsx` e `global-error.tsx` são as **redes de segurança**: se uma tela quebrar
  por um erro inesperado, em vez de **tela branca**, aparece uma mensagem amigável com
  botão de "tentar de novo".

### `components/how-we-got-here.tsx` — "Como chegamos nisso"
Um bloco **expansível** reutilizável que mostra a **cadeia de raciocínio** por trás de
um número (quantos anos de dados, método, evidências). É a transparência feita
componente.

---

## As telas (cada pasta em `app/` = um endereço)

### `/` → Estimativa da Região (`app/page.tsx`)
Você escolhe município, cultura e safra; o FADA mostra a **produtividade esperada** (em
sacas/ha) com a **faixa de incerteza**, os **3 cenários**, os **riscos climáticos**, a
**janela de plantio** e uma **explicação em texto**. Em baixo, o "Como chegamos nisso".

### `/home` → Início (painel) (`app/home/page.tsx`)
A tela inicial. Responde "por onde começo?". Mostra, da fazenda selecionada: quanto já
gastou, quanto falta investir, talhões em alerta, operações atrasadas, próxima operação,
o que merece atenção e destaques. Tem o **selo de confiança** (Capítulo 3), o **registro
rápido** (com presets) e, se a fazenda estiver vazia, o botão **"Explorar com fazenda de
demonstração"** ou o caminho do **onboarding**.

### `/onboarding` → Primeiros passos (`app/onboarding/page.tsx`)
Um **assistente em 4 passos** para quem está começando: criar fazenda → talhão → safra →
pronto. **Sem digitar nenhum número de ID.** Ao final, já deixa tudo selecionado no
contexto.

### `/safra` → Minha Lavoura (`app/safra/page.tsx`)
A **tela-hub** da safra. Numa página só: resumo da safra, **Plano & Orçamento**,
**Custos**, **Atenção do talhão**, e a **linha do tempo** das operações + formulário para
registrar evento. Tudo dirigido pelo contexto (sem re-selecionar).

### `/planejamento` → Plano & Orçamento (`app/planejamento/page.tsx`)
Compara **planejado × realizado**: quanto gastou de quanto planejou, quanto falta,
aplicações feitas vs. planejadas, e a **agenda** (operações concluídas/atrasadas/
próximas). Tem formulários para planejar operações e para registro rápido.

### `/financeiro` → Financeiro (`app/financeiro/page.tsx`)
Os custos em detalhe: total, por hectare, por saca, gráfico de **custo por categoria**,
e — informando o **preço da saca** — o **ponto de equilíbrio** e os **cenários de lucro**
(gráfico).

### `/decisoes` → Onde Olhar Primeiro (`app/decisoes/page.tsx`)
O "heatmap" honesto: cada talhão como um card colorido por **nível de atenção**, com a
**lista de alertas nomeados** que ele disparou. Cada alerta tem um "Ver dados" que mostra
a evidência. Mais os **rankings** por dimensão.

### `/insights` → Análise dos Talhões (`app/insights/page.tsx`)
Compara os talhões (produtividade, estabilidade, custo) e lista **insights** com nível de
confiança e "Ver dados".

### `/adaptive` → Personalização da Fazenda (`app/adaptive/page.tsx`)
Mostra a **cascata**: previsão regional → ajuste da sua fazenda (após o encolhimento) →
previsão personalizada, com a **confiança** visível e a **evolução dos resíduos** em
gráfico.

### `/calibration` → Sobre o Modelo (`app/calibration/page.tsx`)
A prova de honestidade: o **diagrama de confiabilidade** (esperado × observado), a
cobertura, e a comparação regional × personalizado. É a página técnica por trás do "selo
de confiança".

### `/assistant` → Assistente (`app/assistant/page.tsx`)
O chat. Você pergunta em português; ele usa o **contexto** (fazenda/safra) para responder
perguntas de custo, orçamento, decisão e personalização — sempre com números vindos do
backend.

### `/farms` → Captura de Dados (`app/farms/page.tsx`)
O fluxo de cadastro guiado (fazenda → talhão → safra → registrar colheita).

### `/planting/simulate` e `/planting/optimize`
Simular uma data de plantio específica e otimizar a janela (top 5 datas).

### `/system` → Sistema (`app/system/page.tsx`)
O **status técnico**: backend, banco, modelo, versão, contagem de registros. Útil para
diagnosticar problemas.

---

## Os componentes de apoio (`components/`)

- `ui/` — os blocos visuais básicos (botão, card, campo, seletor, etc.).
- `*-charts.tsx` — os **gráficos** específicos (cenários, financeiro, calibração,
  insights, adaptativo), feitos com Recharts.
- `stat.tsx`, `page-header.tsx`, `municipality-select.tsx` — pedacinhos reutilizáveis.
- `confidence-badge.tsx` — o selo de confiança.

## Resumo do capítulo

- O frontend tem uma **fundação** (`api.ts` = telefone, `context` = memória global,
  `nav` = menu, error boundaries = rede de segurança).
- Cada pasta em `app/` é uma **tela**, organizada **por tarefa do produtor**.
- O **contexto global** elimina re-seleção e digitação de IDs; a **transparência**
  ("Como chegamos nisso", "Ver dados") está espalhada nas telas.

➡️ Próximo: **[Capítulo 10 — Uma ação de ponta a ponta](10-ponta-a-ponta.md)**.
