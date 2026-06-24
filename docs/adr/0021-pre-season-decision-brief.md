# ADR-0021 — Brief de decisão pré-safra (composição como produto)

**Status:** Aceito · **Data:** 2026-06-24 · **Marco:** V2.0

## Contexto
A V2.0 acumulou peças de inteligência pré-safra independentes — produtividade
regional (±), janela ZARC oficial, melhor data (otimizador), preço CEPEA e custo
CONAB. Isoladas, exigem que o produtor visite várias telas e faça a conta de
cabeça. O **pilar do produto é o pré-safra**: decidir *se* plantar, *quando* e com
*qual margem esperada* — antes do plantio.

## Decisão
Criar um **serviço de composição** (`SeasonPlanningService`) e um endpoint
(`GET /planning/season-brief`) que sintetizam as peças num **único brief de
decisão**, e uma tela "Planejar a Safra". Princípios:

1. **Composição, não recálculo.** O serviço apenas orquestra serviços existentes;
   nenhum número novo é inventado. A síntese de margem (`domain/planning/season`)
   é pura e reusa o Cost Engine (cenários + ponto de equilíbrio).
2. **Margem como decisão honesta.** Projeta lucro/ha por cenário de produtividade
   ao preço observado, sobre o custo **de referência** CONAB, e o ponto de
   equilíbrio por conceito de custo (COE/COT/CT). É apoio à decisão, não promessa.
3. **Degradação graciosa por seção.** Produtividade é a âncora (obrigatória);
   ZARC, melhor data, preço e custo são opcionais — se faltarem, o brief informa o
   que falta em vez de quebrar. A margem só aparece com preço **e** custo.
4. **Proveniência sempre.** Cada brief lista as fontes oficiais usadas e mantém os
   disclaimers (produtividade é probabilística; preço é observado; custo é referência).

## Justificativa
- Entrega o pilar (apoio à decisão pré-safra) reaproveitando 100% do que já existe
  — máximo valor, mínimo código novo e risco.
- Mantém o determinismo (ADR-0002/0003): o brief é uma visão composta de números
  auditáveis, não uma geração.

## Consequências
- (+) Uma resposta única para "vale plantar, quando e com que margem?".
- (+) Base natural para, no futuro, um **briefing redigido por LLM** estritamente
  *grounded* nesses números (sem inventar) e para a personalização por fazenda.
- (−) Endpoint de agregação sem `response_model` rígido (serializado via
  `jsonable_encoder`) — escolha pragmática dado o payload composto; tipado no front.
- (−) Acopla um serviço aos demais (composição) — aceitável num *composition root*.

## Próximos passos
Integrar os mesmos serviços ao Assistente conversacional; gerar o briefing textual
*grounded*; cruzar a data recomendada com o nível de risco ZARC na própria recomendação.
