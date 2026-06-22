# Capítulo 13 — Como rodar e como estudar o projeto

Teoria é bom, mas **ver funcionando** consolida o entendimento. Aqui está como rodar o
FADA na sua máquina e um roteiro para estudar o código.

## Como rodar (passo a passo)

Você vai precisar de **dois terminais** abertos ao mesmo tempo: um para o backend, outro
para o frontend. (Um "terminal" é aquela tela preta de digitar comandos.)

### Pré-requisitos
- **Python 3.11+** instalado (para o backend).
- **Node.js** instalado (para o frontend).

### Terminal 1 — Backend
```bash
cd backend
python -m venv .venv            # cria um "ambiente isolado" do Python
source .venv/bin/activate       # ativa esse ambiente (no Windows: .venv\Scripts\activate)
pip install -e ".[ml,dev]"      # instala as dependências
pytest                          # (opcional) roda os 164 testes — deve dar tudo "passed"
uvicorn app.main:app --reload --port 8000
```
Deixe esse terminal aberto. O backend está no ar em `http://localhost:8000`.
- Teste no navegador: `http://localhost:8000/api/v1/health` → deve mostrar `{"status":"ok"}`.
- Documentação automática da API: `http://localhost:8000/docs`.

### Terminal 2 — Frontend
```bash
cd frontend
npm install                     # instala as dependências (demora um pouco na 1ª vez)
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev                     # sobe o frontend
```
Abra `http://localhost:3000` no navegador. 🎉

### Primeiro acesso
- Na tela **Início**, clique em **"Explorar com fazenda de demonstração"** — isso popula
  o sistema com dados de exemplo (histórico, plano, custos), e você pode navegar por
  tudo já preenchido.
- Ou siga o **onboarding** (`/onboarding`): criar fazenda → talhão → safra.

### ⚠️ Se der "não foi possível conectar à API"
Quase sempre é uma destas causas (detalhado no README):
1. O **backend não está rodando** (terminal 1). Suba-o.
2. O **endereço** no `.env.local` está errado. Deve ser **só** `http://localhost:8000`
   (sem barra no fim, sem `/api/v1`). Depois de mudar, **reinicie** o `npm run dev`.
3. Você está usando **GitHub Codespaces / máquina remota**: aí `localhost` é a SUA
   máquina, não o servidor. Use a **URL encaminhada da porta 8000** (https) e deixe a
   porta 8000 **Public**.

## Roteiro para estudar o código (na ordem)

Sugiro estudar "de fora para dentro", acompanhando uma funcionalidade:

1. **Escolha uma funcionalidade simples** — sugiro o **custo**.
2. **Comece pela tela**: `frontend/app/financeiro/page.tsx`. Veja o que ela mostra e que
   função do `lib/api.ts` ela chama (ex.: `api.getCropCycleCost`).
3. **Vá ao endpoint**: procure esse endereço em `backend/app/api/v1/routes/cost.py`.
4. **Suba para o serviço**: `backend/app/services/cost.py` — veja como ele busca dados.
5. **Chegue na conta**: `backend/app/domain/cost/engine.py` — a fórmula pura.
6. **Veja o teste**: `backend/app/tests/test_cost_engine.py` — confirma a fórmula.

Fazendo isso uma vez, você "pega o jeito" do padrão **tela → api → rota → serviço →
domínio → teste**, que se repete em tudo.

### Dicas de leitura
- Os arquivos têm **comentários no topo** explicando o propósito (em português).
- Os arquivos `__init__.py` (Python) e `index`-like definem o que cada pasta "exporta".
- A documentação técnica está em **`docs/`** (uma por funcionalidade) e as decisões em
  **`docs/adr/`**.
- A **documentação automática da API** (`http://localhost:8000/docs`) deixa você **testar
  cada endpoint** clicando — ótimo para ver as respostas de verdade.

## Onde está cada coisa (consulta rápida)

| Quero entender… | Vá para… |
|---|---|
| O que o sistema faz | Capítulos 1 e 9 deste guia |
| Como é organizado | Capítulos 4 e 6 |
| As contas / o cérebro | Capítulo 7 + `backend/app/domain/` |
| De onde vêm os números | Capítulo 8 + `backend/pipelines/` |
| As telas | Capítulo 9 + `frontend/app/` |
| Por que as decisões | Capítulo 11 + `docs/adr/` |
| Um termo difícil | Capítulo 12 (Glossário) |

## Palavra final

O FADA foi construído com uma ideia central: **honestidade acima de esperteza**. Cada
número tem origem rastreável, cada faixa de incerteza é medida, e o sistema prefere
dizer "não sei ainda" a inventar. É um alicerce sólido, científico e organizado — pronto
para crescer e melhorar a cada safra que o produtor registrar.

Bons estudos! 🌱

⬅️ Voltar ao **[Índice](00-INDICE.md)**.
