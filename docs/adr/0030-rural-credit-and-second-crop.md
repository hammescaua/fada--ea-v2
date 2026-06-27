# ADR-0030 — Crédito rural (Plano Safra) e decisão de 2ª safra

**Status:** Aceito · **Data:** 2026-06-27 · **Marco:** V2.0 (decisões financeiras da safra)

## Contexto
O produtor não decide só o que/quando plantar — decide **como financiar** (custeio,
investimento) e **o que fazer no inverno/2ª safra** (trigo, milho 2ª, cobertura). O
dono pediu trazer crédito rural, Plano Safra e simulação dessas decisões. A V2 já
tem a economia da soja (custo, break-even, margem); faltava a camada financeira do
financiamento e a comparação entre culturas.

## Decisão
Adicionar um domínio financeiro **puro e determinístico** + um catálogo de crédito
**de referência, datado e citado** — sem inventar taxa nem conceder crédito:

- `domain/finance/credit.py`: `simulate_financing(principal, taxa, prazo, sistema)`
  com **Price** (parcela fixa) e **SAC** (decrescente); taxa mensal por juros
  compostos; trata 0% (linha subsidiada). Retorna parcela, juros totais, custo total.
- `domain/finance/rotation.py`: `compare_options(...)` ordena por **margem/ha** as
  opções de 2ª safra a partir de produtividade/preço/custo informados.
- `data/credit/plano_safra.json`: catálogo **de referência** com as taxas reais
  pesquisadas do **Plano Safra 2025/2026** (Pronaf custeio 2–4% e investimento ~3–5%;
  Pronamp 10%; custeio demais ~12,5–14%; investimento empresarial 12,5%; Moderfrota
  13,5%; RenovAgro/ABC+ e PCA 10%; Proirriga 12,5%), com finalidade, público e
  **limite** por linha — datado (vigência 01/07/2025–30/06/2026), citado
  (MAPA/MDA, MCR/Bacen) e com **disclaimer forte**: confirme a taxa vigente; o FADA
  não concede crédito. Connector `CreditStore` (runtime leve).
- Rotas: `GET /credit/lines`, `POST /credit/simulate`, `POST /credit/compare-crops`.
- UI: página **Crédito & 2ª safra** — simulador (taxas de referência clicáveis
  preenchem o campo) + tabela comparativa de margem por hectare.

**Honestidade (pilar):** a matemática é determinística e auditável; as **taxas são
do produtor** (ou referências que ele confirma), nunca número inventado nem oferta
de crédito. A comparação de 2ª safra é a *conta* das opções, não uma previsão de
produtividade dessas culturas (que não temos modelo calibrado para elas).

## Justificativa
- Cobre uma decisão real e recorrente (financiar a safra) com uma ferramenta simples
  e correta, no espírito determinístico-first (ADR-0002).
- Reaproveita o padrão de artefato datado (ADR-0018) e a linguagem de honestidade.
- Não promete o que não pode sustentar: sem modelo de trigo/milho, comparamos a
  *margem* com números do produtor — útil e honesto.

## Consequências
- (+) O produtor simula parcela/juros/custo total e compara opções de inverno na
  mesma plataforma onde já vê custo/margem da soja.
- (+) Domínio puro, 100% testável; sem dependência externa nova no runtime.
- (−) O catálogo de taxas precisa de atualização por safra (manual, datado). Não há
  integração ao vivo com bancos (fora de escopo e de risco regulatório).

## Próximos passos
Integrar o custeio simulado ao break-even do talhão (margem líquida já com o custo do
financiamento). Referências de produtividade/custo de trigo/milho 2ª safra (CONAB/
Emater) como defaults a confirmar. Atualização anual do catálogo junto dos demais
artefatos.
