# Capítulo 3 — Conceitos de IA, modelos e previsão (sem matemática pesada)

Este capítulo é importante porque a palavra "IA" hoje virou bagunça. Vou separar o que
o FADA **faz** do que ele **não faz** — e por quê.

## O que é um "modelo"?

Um **modelo** é uma "fórmula aprendida a partir de dados" que serve para **prever**
algo. Analogia: imagine que você anotou, por muitos anos, quanto choveu na época da
florada da soja e quanto colheu. Com o tempo, você percebe um padrão: *"quando chove
pouco na florada, eu colho menos"*. Esse padrão, transformado em fórmula, é um modelo.

No FADA, o modelo principal foi "treinado" com **787 observações reais** de
produtividade de soja (20 municípios × ~45 anos), cada uma combinada com o clima
daquele ano. A partir disso, ele aprendeu a relação entre **clima** e **produtividade**.

> **"Treinar" um modelo** = mostrar muitos exemplos passados (clima do ano X →
> produtividade do ano X) para ele descobrir o padrão. Depois, dado o clima de um novo
> ano, ele **prevê** a produtividade.

## Por que o FADA usa um modelo SIMPLES (e isso é proposital)

Existem modelos super complexos hoje (as famosas "redes neurais profundas", *deep
learning*). O FADA **escolheu não usar** isso. Por três motivos, todos pensados:

1. **Pouco dado.** Modelos complexos precisam de milhões de exemplos. O FADA tem ~800.
   Com pouco dado, um modelo simples e interpretável **funciona igual ou melhor** e não
   "decora" bobagem.
2. **Transparência.** O modelo do FADA é uma **regressão linear** — basicamente uma
   soma ponderada de fatores ("o déficit de água pesa tanto, a tendência tecnológica
   pesa assim"). Dá para abrir e ver **exatamente** por que ele deu aquele número. Um
   modelo complexo é uma "caixa-preta" que ninguém explica.
3. **Honestidade.** Para um produtor confiar e decidir com dinheiro real, ele precisa
   poder auditar. "Caixa-preta" não combina com decisão financeira.

> O FADA testou três modelos (regressão linear, "floresta aleatória" e "XGBoost") num
> teste justo. Os três deram praticamente o **mesmo erro**. Então escolheu-se o mais
> simples e transparente. Isso está documentado no projeto (ADR-0006).

## A regra mais importante: **incerteza sempre visível**

O FADA **nunca** dá um número seco. Ele sempre diz a **faixa**. Por quê?

Porque a produtividade de soja depende fortemente do **clima do ano**, que é
**imprevisível**. Ninguém sabe se o ano que vem será de seca ou de chuva boa. Então o
honesto é dizer: *"o esperado é 51 sacas/ha, mas pode ir de 40 (ano ruim) a 62 (ano
bom)"*. Essa faixa se chama **intervalo de confiança** (ou intervalo de incerteza).

Uma previsão confiante e errada **destrói a confiança** do usuário. Uma previsão
honesta com margem **constrói** confiança. Esse é um princípio de ouro do projeto.

## Calibração: "as faixas são realmente honestas?"

Aqui o FADA faz algo que poucos sistemas fazem. Não basta mostrar uma faixa — a faixa
precisa ser **verdadeira**. Se o FADA diz "intervalo de 80%", isso deveria significar
que, na vida real, a colheita cai dentro dessa faixa em **80% das vezes**.

O FADA **verifica isso** com os dados históricos (um "teste de volta no tempo"). E o
resultado é honesto: o intervalo de 80% conteve a produtividade real em **~79%** das
safras. Ou seja, a faixa é **calibrada** — quando ele diz 80%, é 80% mesmo, não 60%
disfarçado. Isso está no Capítulo 8 e na documentação (ADR-0013).

> Pense num médico que diz "90% de chance de cura". Se, dos pacientes que ele disse
> isso, só 60% se curaram, ele é **mal calibrado** (otimista demais). O FADA mede a
> própria calibração para não cair nisso.

## E o tal do "LLM" / ChatGPT? Onde entra?

**LLM** significa *Large Language Model* (Modelo de Linguagem Grande). É a tecnologia
por trás do ChatGPT — programas que **escrevem texto** de forma fluente. O FADA usa um
LLM (o **Claude**, da empresa Anthropic) em **apenas dois papéis muito limitados**:

1. **Entender a pergunta** que o usuário digita no Assistente (ex.: "qual a melhor data
   para plantar?") e decidir **qual conta chamar**.
2. **Explicar em português** um resultado que **já foi calculado** pelas contas.

A regra de ferro, repetida no projeto inteiro: **o LLM NUNCA inventa um número.** Todos
os números vêm das contas determinísticas do backend. O LLM só "conversa" e "explica".

> **Por quê?** Porque LLMs podem "alucinar" (inventar fatos com cara de verdade). Para
> um sistema de decisão agrícola, deixar um LLM chutar "você vai colher 60 sacas" seria
> irresponsável. Então ele é mantido na coleira: roteia e explica, nunca calcula.
> (Documentado em ADR-0002 e ADR-0010.)

E mais: se não houver uma "chave" de acesso ao Claude configurada, o FADA **continua
funcionando** — ele usa uma explicação em texto montada por uma regra fixa, em vez do
LLM. Ou seja, a inteligência de verdade **não depende** do LLM.

## Determinístico × probabilístico

Dois termos que aparecem muito:

- **Determinístico**: as mesmas entradas **sempre** dão o mesmo resultado. 2 + 2 é
  sempre 4. As contas do FADA são determinísticas — por isso são auditáveis e testáveis.
- **Probabilístico**: lida com chances e incerteza. A previsão de produtividade é
  probabilística (vem com faixa e cenários), mas é **calculada de forma determinística**
  (rodar de novo dá a mesma faixa).

## Resumo do capítulo

- **Modelo** = fórmula aprendida de dados, usada para prever. O do FADA é **simples e
  transparente** de propósito (pouco dado + necessidade de auditar).
- **Incerteza sempre visível**: nunca um número seco, sempre uma **faixa**.
- **Calibração**: o FADA **verifica** que suas faixas são honestas (e elas são: ~79%
  para o intervalo de 80%).
- **LLM (ChatGPT-like)**: usado **só** para entender perguntas e explicar — **nunca**
  para inventar números. O sistema funciona mesmo sem ele.

➡️ Próximo: **[Capítulo 4 — Arquitetura geral](04-arquitetura-geral.md)**.
