# Capítulo 4 — A arquitetura geral (a planta da casa)

"Arquitetura" de software é como a **planta de uma casa**: mostra os cômodos (partes do
sistema) e como eles se ligam (corredores, portas). Vamos ver a planta do FADA.

## A visão de cima (o desenho)

```
┌───────────────────────────────────────────────┐
│  VOCÊ (produtor), no navegador                 │
└───────────────────────┬───────────────────────┘
                        │ clica, digita
                        ▼
┌───────────────────────────────────────────────┐
│  FRONTEND  (pasta frontend/)                   │
│  As telas: Início, Lavoura, Financeiro…        │
│  Tecnologia: Next.js + React + Tailwind        │
└───────────────────────┬───────────────────────┘
                        │ pede dados pela internet (JSON)
                        ▼   pelos endereços /api/v1/...
┌───────────────────────────────────────────────┐
│  BACKEND  (pasta backend/)                     │
│                                                │
│   1. API  ────────────► recebe o pedido        │
│   2. Serviços ────────► organizam o trabalho   │
│   3. Domínio ─────────► fazem as CONTAS         │
│   4. Infra (banco) ───► guardam/buscam dados   │
│                                                │
│  Tecnologia: Python + FastAPI                  │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│  BANCO DE DADOS  (arquivo data/fada.db)        │
│  Guarda fazendas, talhões, safras, custos      │
└───────────────────────────────────────────────┘

   À parte, "offline" (rodado só de vez em quando):
┌───────────────────────────────────────────────┐
│  PIPELINES  (pasta backend/pipelines/)         │
│  Baixam dados públicos e TREINAM o modelo,     │
│  gerando arquivos em data/models e data/features│
└───────────────────────────────────────────────┘
```

## As 4 camadas do backend (a parte mais importante de entender)

O "cérebro" (backend) é organizado em **camadas**, como uma cebola. Cada camada tem um
papel, e uma camada só conversa com a vizinha. Isso mantém tudo organizado.

### Camada 1 — API (a recepção)
É a "porta de entrada". Recebe o pedido de fora, confere se os dados vieram certos, e
encaminha para o serviço apropriado. **Não faz conta nenhuma.** É só recepção e
tradução. (Arquivos em `backend/app/api/v1/routes/`.)

### Camada 2 — Serviços (os gerentes)
Cada **serviço** organiza um trabalho. Ex.: o "serviço de custo" busca os eventos da
safra no banco, chama as contas de custo, e monta a resposta. O serviço **coordena**,
mas as contas finas ele delega para a camada de baixo. (Arquivos em
`backend/app/services/`.)

### Camada 3 — Domínio (os especialistas / onde vivem as contas)
É o **coração científico**. Aqui ficam as **contas puras**: a fórmula de custo, a
fórmula de previsão, a estatística de calibração. Essa camada é **"pura"** — ela não
conhece banco de dados, nem internet, nem telas. Recebe números, devolve números. Por
isso é fácil de **testar** e tem **garantia** de estar certa. (Arquivos em
`backend/app/domain/`.)

> Essa separação é a regra de ouro da organização: **as contas nunca dependem de banco
> ou de internet**. Isso permite testá-las isoladamente e confiar nelas.

### Camada 4 — Infraestrutura (o almoxarifado)
Cuida do "mundo de fora": o **banco de dados** (guardar e buscar) e os **conectores**
que baixam dados públicos da internet. (Arquivos em `backend/app/infra/` e
`backend/app/data/connectors/`.)

E tem mais uma peça especial:

### Engine (o motor conversacional)
A pasta `backend/app/engine/` é a **única** onde o LLM (Claude) aparece — para entender
perguntas e explicar resultados. Lembre: ele nunca gera número.

## "Modular monolith" — uma decisão importante de arquitetura

Você vai ver o termo **"modular monolith"** (monólito modular). Traduzindo:

- **Monólito** = o backend é **um único programa** que roda junto (não está quebrado em
  vários mini-programas espalhados).
- **Modular** = mas, **por dentro**, ele é bem dividido em módulos com fronteiras
  claras (as tais camadas e os "contextos" de domínio).

**Por que essa escolha?** Existe uma moda chamada "microsserviços", onde se quebra o
sistema em dezenas de mini-programas separados. Isso traz uma complexidade enorme
(comunicação pela rede, falhas, monitoramento). Para um time pequeno ou uma pessoa,
isso é "matar formiga com bazuca". O monólito modular dá **organização sem a dor da
complicação distribuída** — e, se um dia precisar, dá para extrair um módulo em serviço
separado, porque as fronteiras já estão limpas. (Documentado em ADR-0001.)

## "DDD" e "bounded contexts" — organizando por assunto

**DDD** = *Domain-Driven Design* ("desenho guiado pelo domínio"). É uma forma de
organizar o código **por assunto do negócio**, não por tecnicalidade. No FADA, o
domínio é dividido em **contextos** (em inglês, *bounded contexts*), cada um cuidando de
um assunto:

| Contexto (pasta em `domain/`) | Assunto |
|---|---|
| `units` | conversões (saca ↔ quilo) |
| `climate` | índices de clima (chuva, calor, déficit de água) |
| `crop` | calendário e fenologia da soja (fases da planta) |
| `features` | preparar os "ingredientes" do modelo |
| `yield_estimation` | a previsão de produtividade + cenários |
| `planting_date` | o "e se eu plantar em outra data?" |
| `farm` | fazenda, talhão, safra, eventos, presets |
| `cost` | custos, lucro, ponto de equilíbrio |
| `planning` | plano da safra, orçamento, agenda |
| `catalog` | catálogo de produtos (insumos) |
| `adaptive` | personalização por fazenda |
| `calibration` | medir se os intervalos são honestos |
| `insights` | comparar talhões + insights |
| `decisions` | atenção/prioridade por talhão |

Cada contexto é uma "caixinha" coesa. Isso facilita achar as coisas e mexer numa parte
sem quebrar as outras.

## O caminho de um pedido (resumido)

Quando você clica em algo que precisa de dados, o caminho é sempre parecido:

```
Frontend (clique) → API (recebe) → Serviço (coordena) →
Domínio (faz a conta) e/ou Infra (busca no banco) →
Serviço (monta resposta) → API (devolve JSON) → Frontend (mostra na tela)
```

No **Capítulo 10**, vou seguir esse caminho com dois exemplos concretos, passo a passo.

## Resumo do capítulo

- O FADA tem **frontend** (telas), **backend** (cérebro), **banco** (memória) e
  **pipelines** (treino do modelo, offline).
- O backend tem **4 camadas**: API (recepção) → Serviços (gerência) → Domínio (contas
  puras) → Infra (banco/internet). O LLM vive só no `engine`.
- É um **monólito modular** (um programa, bem dividido) com **DDD** (organizado por
  assunto, em "contextos").

➡️ Próximo: **[Capítulo 5 — Tecnologias usadas](05-tecnologias-usadas.md)**.
