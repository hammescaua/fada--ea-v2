# Capítulo 1 — O que é o FADA (sem nenhum jargão)

## O problema do produtor

Imagine um agricultor que planta **soja** no Rio Grande do Sul. Todo ano ele toma
decisões que valem muito dinheiro:

- *Quanto vou colher nesta safra?* (uma safra = um ciclo de plantio até a colheita)
- *Quanto vou gastar* com adubo, sementes, defensivos, combustível?
- *Quanto vou lucrar* no final?
- *Qual a melhor data para plantar?* (plantar cedo ou tarde demais muda o resultado)
- *Qual o risco de seca* estragar a safra?
- *Qual dos meus talhões (pedaços de terra) precisa de mais atenção?*

Hoje, ele toma essas decisões muitas vezes "no feeling", olhando planilhas soltas ou
a experiência dos anos anteriores. Existe **muita informação pública** que poderia
ajudar (histórico de produtividade da região, dados de clima de satélite), mas ela é
difícil de juntar e interpretar.

## A ideia do FADA

O **FADA** é um programa de computador (que roda no navegador, como um site) que faz
esse trabalho pesado por ele. Ele:

1. **Junta dados públicos** — produtividade histórica da região (do IBGE, o instituto
   de geografia e estatística do Brasil) e dados de clima (de satélites da NASA e de
   serviços meteorológicos).
2. **Junta os dados da fazenda** — o que o produtor registra: quais operações fez,
   quanto gastou, quanto colheu.
3. **Transforma tudo em respostas** — números claros para as perguntas acima.

O nome FADA significa **F**arm **A**I **D**ecision **A**gent — em português, algo como
"Agente de Decisão Agrícola com Inteligência Artificial". Mas atenção: a palavra "IA"
aqui é usada com muito cuidado (veja o Capítulo 3). O FADA **não é** um "ChatGPT que
dá palpite". É um sistema que faz **contas determinísticas** (as mesmas entradas
sempre dão o mesmo resultado) e mostra a **margem de erro** de cada resposta.

## Uma analogia: o FADA é como um bom contador + agrônomo de bolso

Pense no FADA como dois profissionais juntos:

- Um **agrônomo** que conhece o histórico da região e te diz "olha, com esse clima,
  o esperado é colher tanto, com esse risco".
- Um **contador** que soma seus gastos, calcula seu custo por hectare, e te mostra a
  partir de quanto você começa a lucrar.

E o mais importante: esse "profissional digital" é **honesto**. Ele nunca diz um
número com falsa certeza. Sempre diz algo como *"o esperado é 51 sacas por hectare,
mas pode variar entre 40 e 62 dependendo do clima do ano"*. Essa **faixa** (40 a 62)
é o que chamamos de **intervalo de incerteza** — e ela é fundamental, porque uma
previsão confiante e errada é pior do que uma previsão honesta com margem.

## O que o FADA responde, na prática

| Pergunta do produtor | Como o FADA responde |
|---|---|
| Quanto vou colher? | Uma estimativa em **sacas por hectare** + a faixa de incerteza + 3 cenários (ruim, normal, bom) |
| Qual a melhor data de plantio? | Testa várias datas e mostra as 5 melhores, priorizando **estabilidade** (menos risco) |
| Como está minha safra? | Uma tela só com resumo, plano vs. gasto real, custos e alertas |
| Estou gastando demais? | Compara o **planejado** com o **realizado** |
| Quanto vou lucrar? | Receita esperada − custo, e a produtividade mínima para "empatar" |
| Onde devo olhar primeiro? | Marca os talhões com **alertas nomeados** (ex.: "custo 35% acima da média") |
| Minha fazenda produz acima da média? | Compara seu histórico com a expectativa da região |

## A grande estratégia: o "flywheel" (volante de dados)

Existe uma sacada por trás de tudo. Quanto **mais o produtor registra** sua safra
(operações, custos, quanto colheu), **mais o FADA aprende** sobre aquela fazenda
específica e melhora as previsões para ela. Isso cria um **círculo virtuoso**:

```
produtor registra dados → FADA aprende a "personalidade" da fazenda →
previsões ficam melhores → produtor confia e registra mais → repete, melhorando a cada safra
```

Esse círculo se chama, em inglês, **flywheel** (um volante pesado que, uma vez girando,
mantém o movimento). É por isso que o projeto dá tanta importância a **facilitar o
registro de dados** — quanto menos cliques, mais o produtor usa, mais o sistema melhora.

## Resumo do capítulo

- O FADA ajuda o produtor de soja a **decidir** com base em dados, não no "feeling".
- Ele junta **dados públicos** + **dados da fazenda** e dá **respostas com números honestos**.
- Ele é **determinístico** (sem chute) e **mostra a incerteza** sempre.
- A estratégia de longo prazo é o **flywheel**: registrar dados faz o sistema melhorar.

➡️ Próximo: **[Capítulo 2 — Conceitos de software](02-conceitos-de-software.md)**, onde
explico o que é backend, frontend, API e banco de dados — a base para entender o resto.
