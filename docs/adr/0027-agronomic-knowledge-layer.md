# ADR-0027 — Camada de conhecimento agronômico citável (o "guia")

**Status:** Aceito · **Data:** 2026-06-24 · **Marco:** V2.0 (insights / fundação de RAG)

## Contexto
O FADA já liga manejo → efeito em produtividade e lucro, mas explicava o "porquê"
com uma frase curta sem **fonte**. O agricultor incerto pede um **guia**: *por que*
essa variável pesa e *o que* fazer — com credibilidade. O Guia de Execução e o dono
perguntaram explicitamente onde cabe **RAG/LLM**.

## Decisão
Adotar uma **camada de conhecimento curada e citável** (determinística), como
**primeiro passo do RAG** — sem embeddings/LLM ainda:

- `domain/agronomy/knowledge.py`: uma `KnowledgeEntry` por fator/tema
  (fungicida/ferrugem, inoculação, calagem, P, K, ZARC, cultivar, rotação,
  nematoides, textura, plantio direto, MIP, daninhas; temas: veranico, geada), cada
  uma com **explicação + nota prática + fontes** (Embrapa Soja, CQFS-RS/SC, Consórcio
  Antiferrugem, ZARC/MAPA, Agrofit).
- Enriquece o catálogo de fatores (`GET /agronomic/factors`) com `explanation` +
  `sources`; novo `GET /agronomic/knowledge` (guia completo).
- UI: "Por quê (fonte)" em cada fator do Perfil + página **Guia Agronômico**
  (buscável).

**Princípio mantido (ADR-0002):** o LLM/conhecimento **explica e cita**; **nunca
gera número**. Honestidade: citamos **instituições/referências reais**, não números
de portaria/página não verificáveis; o texto é educativo e deve ser confirmado com
o agrônomo.

## Justificativa
- Entrega o "poder de obter insights / guia" pedido, **de forma racional** (barata,
  determinística, sem dependência de LLM), com credibilidade (fonte citada).
- É a **fundação do RAG**: quando valer, uma busca vetorial + LLM citando estas (e
  novas) fontes assenta sobre esta base — sem reescrever o produto.

## Consequências
- (+) Toda recomendação/variável passa a ter um "porquê" com fonte; aumenta confiança.
- (+) Conteúdo versionado no código, auditável e testável (todo verbete tem fonte).
- (−) Curadoria manual (não escala sozinha); o passo seguinte (RAG com LLM) amplia a
  cobertura para perguntas livres do produtor.

## Próximos passos
RAG completo (opcional): indexar boletins Embrapa/Agrofit/ZARC num vetor e um
assistente que responde perguntas livres **citando a fonte** (LLM explica, domínio
decide número). Captura por voz/foto (LLM estrutura entrada). Ambos com a regra dura
do ADR-0002.
