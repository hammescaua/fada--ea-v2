# Capítulo 5 — As tecnologias usadas e por que cada uma

Aqui explico **cada ferramenta** do projeto, em linguagem simples, e **por que** foi
escolhida. Não precisa decorar — use como dicionário.

## Linguagens de programação

### Python (o backend)
**Python** é uma linguagem de programação famosa por ser **legível** (parece quase
inglês) e por ser a **rainha da ciência de dados e IA**. Quase todas as ferramentas de
modelos, estatística e dados são em Python. Como o coração do FADA é fazer **contas e
modelos**, Python é a escolha natural.

### TypeScript (o frontend)
**TypeScript** é uma versão "com segurança extra" do **JavaScript** (a linguagem dos
navegadores). O "Type" vem de **tipos**: você declara que algo é um número, um texto,
etc., e o computador **avisa antes** se você usar errado. Isso evita muitos erros. No
FADA, todo o frontend é em TypeScript.

> Você verá nos commits a frase "tsc --noEmit limpo". O `tsc` é o **verificador de
> tipos** do TypeScript. "Limpo" = ele não achou nenhum erro de tipo. É um selo de
> qualidade automático.

## Ferramentas do backend

### FastAPI (a "recepção" / API)
**FastAPI** é uma ferramenta em Python para **criar a API** (os tais endereços/endpoints).
Ela é rápida, moderna, e gera **automaticamente uma documentação** das rotas (você pode
abrir `http://localhost:8000/docs` no navegador e ver/testar todos os endpoints — muito
útil!). É ela que recebe os pedidos do frontend.

### Pydantic (o "conferente" de dados)
**Pydantic** confere se os dados que entram e saem estão **no formato certo**. Ex.: se o
frontend manda uma fazenda sem nome, o Pydantic barra e devolve "erro 422: faltou o
nome". Isso protege o sistema de dados bagunçados. (Os arquivos em `schemas/` são feitos
com Pydantic.)

### SQLAlchemy (o "tradutor" do banco de dados)
Falar com banco de dados "na unha" é chato e perigoso. **SQLAlchemy** é uma ferramenta
que deixa você trabalhar com **objetos do Python** (uma "Fazenda", um "Talhão") e ela
**traduz** isso para a linguagem do banco automaticamente. Isso se chama **ORM**
(*Object-Relational Mapping*, mapeamento objeto-relacional). (Os arquivos em `infra/`.)

### SQLite e PostgreSQL (os bancos de dados)
- **SQLite**: um banco **super simples**, que é só **um arquivo** (`data/fada.db`).
  Perfeito para desenvolver e testar — não precisa instalar nada.
- **PostgreSQL** (ou "Postgres"): um banco **robusto** para uso real em larga escala.
- O FADA usa SQLite por padrão e pode trocar para Postgres só mudando uma configuração.

### scikit-learn e XGBoost (o treino do modelo)
São **bibliotecas de aprendizado de máquina** (machine learning) em Python.
- **scikit-learn**: a "caixa de ferramentas" clássica de modelos. O FADA usa dela a
  **regressão linear** (o modelo escolhido).
- **XGBoost**: um modelo mais avançado. O FADA o testou para **comparar** — e o
  resultado mostrou que o simples (linear) é tão bom quanto, então ficou com o simples.
- ⚠️ Importante: essas ferramentas são usadas **só nos pipelines** (treino offline). O
  backend que responde ao usuário **não precisa delas** — ele só lê o resultado já
  treinado (um arquivo). Isso mantém o backend leve.

### NumPy, pandas (manipular números e tabelas)
- **NumPy**: faz contas com **muitos números de uma vez** (vetores) de forma rápida.
- **pandas**: trabalha com **tabelas** (como planilhas) em Python. Usado nos pipelines
  para organizar os dados antes de treinar.

### Claude / Anthropic (o LLM, opcional)
**Claude** é o LLM (modelo de linguagem, tipo ChatGPT) da empresa **Anthropic**. No
FADA, ele é **opcional** e fica só no Assistente, para entender perguntas e explicar.
Sem ele, o sistema usa explicações por regra fixa. **Nunca gera número.**

### pytest e ruff (qualidade do backend)
- **pytest**: ferramenta que roda os **testes automáticos**. O FADA tem **164 testes**
  que conferem se as contas estão certas. Rodar `pytest` e ver "164 passed" é a garantia
  de que nada quebrou.
- **ruff**: confere o **estilo e a limpeza** do código (sem variáveis sobrando, imports
  organizados, etc.). "ruff limpo" = código arrumado.

## Ferramentas do frontend

### Next.js + React (a estrutura das telas)
- **React** é a biblioteca mais popular do mundo para construir **interfaces** (telas)
  na web, montando-as como "blocos" reutilizáveis chamados **componentes** (ex.: um
  botão, um card, um gráfico).
- **Next.js** é um "framework" (estrutura completa) construído em cima do React. Ele
  organiza as **páginas** (cada pasta em `frontend/app/` vira um endereço no navegador),
  cuida da navegação e do empacotamento. No FADA usamos o "App Router" do Next.

### Tailwind CSS (a aparência)
**CSS** é a linguagem que define **cores, tamanhos, espaçamentos** — a aparência.
**Tailwind** é uma forma de escrever CSS direto no componente com "atalhos" curtos (ex.:
`px-4` = espaçamento horizontal). Deixa o visual consistente e rápido de montar.

### shadcn/ui (componentes prontos com bom gosto)
Um conjunto de componentes visuais (botões, cartões, campos) com um **estilo
profissional**. No FADA, os componentes em `frontend/components/ui/` seguem esse estilo.

### TanStack React Query (buscar dados do backend)
Quando o frontend pede dados ao backend, há um monte de detalhes chatos: mostrar
"carregando…", lidar com erro, guardar o resultado para não pedir de novo à toa.
**React Query** cuida de tudo isso automaticamente. É por isso que, no FADA, uma falha
em **uma** tela não derruba as outras — cada pedido é gerenciado de forma isolada.

### Recharts (os gráficos)
**Recharts** desenha os **gráficos** (barras de cenários, diagrama de calibração, etc.)
de forma bonita e responsiva (se adapta ao tamanho da tela).

## Ferramentas de dados e reprodutibilidade (pipelines)

### DVC e MLflow
- **DVC** (*Data Version Control*): ajuda a **versionar dados e pipelines** (saber qual
  dado gerou qual modelo). Define a "receita" de como reconstruir tudo (`dvc.yaml`).
- **MLflow**: registra os **experimentos de treino** (qual modelo deu qual erro). É como
  um caderno de laboratório automático.

## Ferramentas gerais

### Git e GitHub
- **Git** é o sistema que guarda o **histórico** de todas as mudanças do código (cada
  "commit" é uma foto do projeto num momento). Permite voltar atrás e trabalhar em
  equipe.
- **GitHub** é o site onde esse histórico fica guardado na nuvem.

### Docker / docker-compose
**Docker** "empacota" um programa com tudo que ele precisa, para rodar igual em qualquer
máquina. O `docker-compose.yml` descreve como subir o banco, o cache e o backend juntos.
(No FADA, é opcional — dá para rodar tudo sem Docker.)

## Resumo do capítulo

- **Backend**: Python + **FastAPI** (API) + **Pydantic** (confere dados) + **SQLAlchemy**
  (banco) + **scikit-learn/XGBoost** (treino, offline) + **pytest/ruff** (qualidade).
- **Frontend**: **TypeScript** + **Next.js/React** (telas) + **Tailwind/shadcn** (visual)
  + **React Query** (buscar dados) + **Recharts** (gráficos).
- **Dados**: **DVC/MLflow** (reprodutibilidade). **Geral**: **Git/GitHub** (histórico),
  **Docker** (empacotar, opcional).

➡️ Próximo: **[Capítulo 6 — Estrutura de pastas](06-estrutura-de-pastas.md)**.
