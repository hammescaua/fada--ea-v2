# Capítulo 10 — Uma ação de ponta a ponta (vendo tudo funcionar junto)

Agora juntamos tudo. Vou seguir **dois exemplos** reais, passo a passo, do clique até a
resposta na tela. Se você entender estes dois, entendeu como o sistema inteiro funciona.

---

## Exemplo 1 — "Quanto vou colher em Horizontina?"

Você abre a tela **Estimativa da Região**, escolhe Horizontina e a safra 2026/27, e
clica em "Calcular". Veja o caminho completo:

```
1. FRONTEND (app/page.tsx)
   Você clica. O React Query chama: api.regionalIntelligence({município, safra…})
   → isso é um pedido HTTP do tipo POST para o endereço /api/v1/regional-intelligence

2. INTERNET → chega ao BACKEND

3. API (routes/regional_intelligence.py)
   Recebe o pedido. O Pydantic (schemas/regional_intelligence.py) confere que veio
   município, cultura e safra. Se faltar algo, devolve "erro 422".

4. SERVIÇO (services/regional_intelligence.py)
   - resolve "Horizontina" → o município no modelo
   - chama o DOMÍNIO para prever

5. DOMÍNIO (domain/yield_estimation/predictor.py)
   - carrega o modelo treinado (o JSON)
   - como a safra é futura, monta 3 cenários usando a climatologia
   - calcula: ponto = 51,2 sacas/ha; intervalo = [39,6 ; 62,0]
   - domain/yield_estimation/risk.py monta os riscos legíveis

6. SERVIÇO (de volta)
   - junta cenários, riscos, janela de plantio, "como chegamos nisso"
   - monta a resposta em JSON

7. API → devolve o JSON para o frontend (status 200 = sucesso)

8. FRONTEND
   - o React Query recebe o JSON
   - a tela mostra: "51,2 sc/ha", a faixa [40–62], o gráfico de cenários,
     os cards de risco, e o bloco "Como chegamos nisso"
```

**Repare:** nenhum LLM participou. Tudo foi conta determinística. Rodar de novo dá
**exatamente** o mesmo resultado.

---

## Exemplo 2 — "Registrar uma pulverização e perguntar quanto já gastei"

Este exemplo mostra o **flywheel** em ação: registrar dado → o sistema responder com base
nele.

### Parte A — registrar a operação (na tela Início)

```
1. FRONTEND (app/home/page.tsx)
   No "Registro rápido", você escolhe um preset "Fungicida padrão", a data, e confirma.
   → api.quickLog({crop_cycle_ids:[safra atual], event_date, preset_id})
   → POST /api/v1/quick-log

2. API (routes/capture.py) recebe; Pydantic confere.

3. SERVIÇO (services/capture.py)
   - busca o preset (Fungicida padrão = R$220/ha)
   - busca a área do talhão (ex.: 90 ha)
   - como o custo do preset é "por hectare", calcula: 220 × 90 = R$ 19.800
   - cria o EVENTO no banco

4. INFRA (infra/repositories.py + models.py)
   - grava o evento na tabela do banco de dados (SQLite)

5. Resposta → o frontend atualiza o painel
```

Agora o dado **está guardado**. O sistema "sabe" dessa operação.

### Parte B — perguntar ao Assistente

```
1. FRONTEND (app/assistant/page.tsx)
   Você digita "Quanto já gastei nesta safra?"
   → api.assistant({message, crop_cycle_id: safra atual, farm_id: fazenda})
   → POST /api/v1/assistant
   (o crop_cycle_id e o farm_id vêm do CONTEXTO global — você não digita nada disso)

2. API → ENGINE (engine/orchestrator.py)
   - o orchestrator entende a intenção: "custo total"
   - vê que precisa da safra (crop_cycle_id) → e ela veio no contexto ✓
   - chama o SERVIÇO de custo

3. SERVIÇO (services/cost.py) + DOMÍNIO (domain/cost/engine.py)
   - busca todos os eventos da safra no banco
   - soma os custos → total

4. ENGINE devolve a frase montada com o número calculado:
   "Você já investiu R$ 19.800,00 nesta safra (1 aplicação)."

5. FRONTEND mostra a resposta no chat.
```

**Repare de novo:** o LLM (se estivesse ativo) só **entenderia a pergunta** e
**escreveria a frase**. O número (R$ 19.800) veio da **soma determinística** dos eventos,
não do LLM. Essa é a regra de ferro do projeto.

---

## O que estes exemplos ensinam

1. O caminho é sempre o mesmo: **Frontend → API → Serviço → Domínio/Infra → resposta**.
2. As **contas** vivem no domínio (puras, testadas). O LLM só conversa.
3. O **contexto global** é o que faz tudo fluir sem você digitar IDs.
4. Cada dado registrado **alimenta** as respostas futuras — o flywheel.

➡️ Próximo: **[Capítulo 11 — Princípios e porquês](11-principios-e-porques.md)**.
