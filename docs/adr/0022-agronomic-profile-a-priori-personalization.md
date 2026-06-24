# ADR-0022 — Personalização a priori por Perfil Agronômico (diverge no dia 1)

**Status:** Aceito · **Data:** 2026-06-24 · **Marco:** V2.0 (pilar pré-safra)

## Contexto
A V1 tinha **duas** camadas de personalização, com um buraco entre elas:
- **Regional** (Ridge, só clima+tendência): idêntica para todo o município — duas
  fazendas vizinhas com solo/manejo opostos recebiam a **mesma** previsão.
- **Shrinkage bayesiano** (ADR-0012): diverge por fazenda, mas **só após anos de
  colheita registrada**. Com 0 fazendas, não atua.

Resultado: no dia 1 — exatamente quando o produtor decide se/quando/como plantar —
não havia personalização. O pilar do produto é o pré-safra; faltava a previsão
personalizada *antes* do plantio.

## Decisão
Introduzir um **terceiro nível**: personalização **a priori** por **Perfil
Agronômico FADA** — um questionário **padronizado** dos fatores que movem a
produtividade, convertido num **ajuste transparente** sobre a estimativa regional.

1. **Matriz padronizada** (`domain/agronomy/profile.py`): ~20 fatores com efeito
   relativo documentado por opção (textura/profundidade/drenagem do solo; P, K,
   acidez, MO; cultivar; janela ZARC; população; inoculação; tratamento de semente;
   fungicida/ferrugem; pragas; daninhas; rotação; plantio direto; compactação;
   nematoides; irrigação). Fonte: Embrapa Soja / CQFS-RS-SC / literatura.
2. **Referência = fazenda típica do município.** O nível "típico/adequado" tem
   efeito 0; desvios ajustam para cima/baixo. Assim o ajuste é *relativo* ao que o
   modelo regional já embute, sem dupla contagem.
3. **Transparência total** (estilo ADR-0016): o ajuste é a soma auditável de efeitos
   **nomeados** (fator, resposta, %, justificativa, confiança) — não um score. O
   multiplicador agregado é **limitado** a [0,50; 1,25] e o clamp é sinalizado.
4. **Honestidade da incerteza** (ADR-0003/0012): o ajuste **alarga** o intervalo
   (incerteza a priori), nunca o estreita. Fatores omitidos = nível típico (sem
   punição por omissão).
5. **Modelo de 3 camadas convergentes:** regional (clima) → **a priori (perfil)** →
   a posteriori (shrinkage, quando houver colheita). O perfil atua no dia 1; o
   shrinkage assume conforme o dado real chega.

Exposto por `GET /agronomic/factors` (catálogo do questionário) e
`POST /agronomic/estimate` (estimativa personalizada com o detalhamento dos fatores).

## Justificativa
- Faz a previsão **divergir de fazenda para fazenda no dia 1** — diferencial central
  pedido para o produto — usando conhecimento agronômico consolidado.
- Preserva os princípios: determinístico, auditável, com incerteza honesta. Os
  efeitos são **estimativas técnicas rotuladas como tal**, não calibração local — e
  o produto deixa isso explícito ("ajuste a priori, a confirmar pela sua colheita").

## Consequências
- (+) Duas fazendas vizinhas recebem previsões distintas e **explicadas** fator a
  fator — base para recomendação de manejo ("o que mais te limita é X").
- (+) Caminho natural para personalizar custo/rentabilidade (fungicida, irrigação,
  calagem entram como custo) e para alimentar o brief de safra (ADR-0021).
- (−) Os efeitos são médios de literatura, não calibrados ao talhão; mitigado pelo
  alargamento do intervalo, pelos rótulos de confiança por fator e pela convergência
  ao shrinkage com dado real.
- (−) Coleta depende do produtor responder o perfil (atrito); mitigado por omissão
  permitida (nível típico) e por puxar parte dos fatores de fontes oficiais no futuro
  (solo via EMBRAPA Solos, janela via ZARC já integrado).

## Próximos passos
Persistir o perfil por talhão e **alimentar o brief de safra** com a produtividade
personalizada (margem por talhão). Pré-preencher fatores a partir de fontes oficiais
(EMBRAPA Solos → textura/profundidade; ZARC → janela; análise de solo → P/K/acidez).
Quando houver colheitas, combinar a priori (perfil) e a posteriori (shrinkage).
