# Capítulo 6 — A estrutura de pastas (o mapa do projeto)

Aqui está o **mapa** de onde fica cada coisa. Não precisa decorar — volte aqui quando se
perder.

## Visão geral (a raiz do projeto)

```
fada--ea-v1/
├── backend/          ← o "cérebro" (Python/FastAPI)
├── frontend/         ← as telas (Next.js/React)
├── data/             ← os dados e modelos treinados
├── docs/             ← documentação técnica + decisões (ADRs)
├── guia-do-projeto/  ← ESTE guia que você está lendo
├── examples/         ← exemplos de respostas reais (JSON)
├── docker-compose.yml ← receita para subir tudo com Docker (opcional)
├── dvc.yaml          ← receita de como reconstruir os dados/modelo
├── params.yaml       ← parâmetros dos pipelines (números de configuração)
└── README.md         ← apresentação + "como rodar"
```

## Dentro de `backend/`

```
backend/
├── app/              ← o código do backend
│   ├── main.py       ← o "liga" do backend (cria a aplicação)
│   ├── core/         ← configurações gerais (config.py)
│   ├── api/          ← a "recepção": os endpoints (endereços)
│   │   └── v1/routes/  ← um arquivo por assunto (farms.py, cost.py…)
│   ├── schemas/      ← os "formulários" (que dados entram e saem)
│   ├── services/     ← os "gerentes" (coordenam o trabalho)
│   ├── domain/       ← o coração: as CONTAS puras (por assunto)
│   ├── engine/       ← o motor conversacional (o LLM mora aqui)
│   ├── infra/        ← banco de dados (guardar/buscar)
│   ├── data/         ← conectores que baixam dados públicos
│   └── tests/        ← os 164 testes automáticos
├── pipelines/        ← scripts "offline" que TREINAM o modelo
├── pyproject.toml    ← lista de dependências do Python
└── .env.example      ← exemplo de configurações de ambiente
```

### O que é cada subpasta de `backend/app/` (a mais importante)

| Pasta | Em uma frase | Analogia (restaurante) |
|---|---|---|
| `api/v1/routes/` | os **endereços** que o frontend chama | o cardápio/garçom |
| `schemas/` | define **quais dados** entram e saem (formato) | os formulários de pedido |
| `services/` | **coordenam** cada tarefa | os gerentes/chefes de cozinha |
| `domain/` | fazem as **contas puras** (o coração) | os cozinheiros especialistas |
| `engine/` | conversa/explica (o **LLM**) | o garçom que explica o prato |
| `infra/` | fala com o **banco de dados** | o almoxarifado |
| `data/connectors/` | baixam **dados públicos** da internet | os fornecedores externos |
| `core/` | **configurações** gerais | o manual de regras da casa |
| `tests/` | **testes** que conferem tudo | o controle de qualidade |

### Dentro de `backend/app/domain/` (o coração, por assunto)

Cada pasta é um "contexto" (assunto). Em geral, cada uma tem:
- um arquivo de **entidades/modelo** (as "coisas": uma Fazenda, um Evento) e/ou
- um arquivo de **engine/cálculo** (as contas daquele assunto).

```
domain/
├── units/          ← conversões (saca ↔ quilo)
├── climate/        ← índices de clima (chuva, calor, déficit de água)
├── crop/           ← calendário/fases da soja
├── features/       ← prepara os "ingredientes" do modelo
├── yield_estimation/ ← a previsão de produtividade
├── planting_date/  ← "e se eu plantar noutra data?"
├── farm/           ← fazenda, talhão, safra, eventos, presets
├── cost/           ← custos, lucro, ponto de equilíbrio
├── planning/       ← plano da safra, orçamento, agenda
├── catalog/        ← catálogo de produtos (insumos)
├── adaptive/       ← personalização por fazenda
├── calibration/    ← mede se os intervalos são honestos
├── insights/       ← compara talhões + insights
└── decisions/      ← atenção/prioridade por talhão
```

## Dentro de `frontend/`

```
frontend/
├── app/              ← as PÁGINAS (cada pasta = um endereço no navegador)
│   ├── page.tsx      ← a página inicial "/" (Estimativa da Região)
│   ├── home/         ← "/home" (o painel inicial)
│   ├── safra/        ← "/safra" (Minha Lavoura)
│   ├── financeiro/   ← "/financeiro"
│   ├── planejamento/ ← "/planejamento" (Plano & Orçamento)
│   ├── decisoes/     ← "/decisoes"
│   ├── insights/     ← "/insights" (Análise dos Talhões)
│   ├── adaptive/     ← "/adaptive" (Personalização)
│   ├── calibration/  ← "/calibration" (Sobre o Modelo)
│   ├── assistant/    ← "/assistant"
│   ├── farms/        ← "/farms" (Captura de Dados)
│   ├── onboarding/   ← "/onboarding" (primeiros passos)
│   ├── system/       ← "/system" (status técnico)
│   ├── planting/     ← simular e otimizar data de plantio
│   ├── layout.tsx    ← a "moldura" comum a todas as páginas (menu, contexto)
│   ├── providers.tsx ← liga o React Query e o contexto global
│   ├── error.tsx / global-error.tsx ← telas de erro (evitam tela branca)
├── components/       ← "blocos" reutilizáveis (botões, cards, gráficos)
│   └── ui/           ← componentes visuais básicos (estilo shadcn)
├── lib/              ← código auxiliar
│   ├── api.ts        ← o "telefone" para o backend (todas as chamadas)
│   ├── context.tsx   ← a memória "Fazenda · Safra" entre páginas
│   ├── events.ts     ← nomes/cores dos tipos de operação
│   └── utils.ts      ← funções utilitárias (formatar dinheiro etc.)
├── package.json      ← lista de dependências do frontend
└── .env.local.example ← exemplo de configuração (endereço do backend)
```

> **Regra do Next.js que vale ouro:** no Next, **cada pasta dentro de `app/` com um
> arquivo `page.tsx` vira um endereço** no navegador. Ex.: `app/financeiro/page.tsx` →
> `http://localhost:3000/financeiro`. É assim que as telas viram URLs.

## Dentro de `data/`

```
data/
├── features/   ← as tabelas de dados prontas para o modelo (CSV)
│   ├── soybean_tres_passos.csv          ← clima + produtividade por município/ano
│   └── soybean_planting_grid_tres_passos.csv ← dados por data de plantio
├── models/     ← os resultados do treino (JSON)
│   ├── soybean_regional_baseline.json   ← o MODELO treinado
│   └── calibration_report.json          ← o relatório de calibração
├── raw/        ← dados crus baixados (cache; não versionado)
├── intermediate/ ← dados intermediários
└── fada.db     ← o banco de dados (SQLite) do dia a dia
```

## Dentro de `docs/`

Documentação técnica (uma para cada grande funcionalidade) e a pasta `adr/` com os
**ADRs** — *Architecture Decision Records*, ou "Registros de Decisão de Arquitetura".
Cada ADR é um documento curto que explica **uma decisão importante e o porquê** (ex.:
"por que não usamos deep learning"). São 17 ADRs. O Capítulo 11 resume os principais.

## Resumo do capítulo

- **`backend/`** = cérebro; dentro, `app/` tem as camadas (api, services, domain, infra).
- **`frontend/`** = telas; cada pasta em `app/` com `page.tsx` é um endereço.
- **`data/`** = dados e modelos treinados. **`docs/`** = documentação + decisões (ADRs).
- **`guia-do-projeto/`** = este guia.

➡️ Próximo: **[Capítulo 7 — O backend por dentro](07-backend-por-dentro.md)** (passamos
por cada funcionalidade do cérebro).
