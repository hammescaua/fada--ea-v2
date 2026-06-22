# Capítulo 2 — Conceitos básicos de software (a base de tudo)

Antes de olhar o FADA por dentro, você precisa de uns poucos conceitos. Vou usar uma
analogia que funciona o tempo todo: **um restaurante**.

## A analogia do restaurante

Quando você vai a um restaurante, existem partes que você **vê** e partes que você
**não vê**:

- O **salão** (mesas, cardápio, garçom) — é o que você vê e com o que interage.
- A **cozinha** — onde a comida é realmente preparada. Você não entra lá.
- O **garçom** — leva seu pedido do salão para a cozinha e traz a comida de volta.
- A **despensa/estoque** — onde ficam guardados os ingredientes.

No mundo dos programas, a correspondência é:

| Restaurante | Software | No FADA |
|---|---|---|
| Salão (o que você vê) | **Frontend** | As telas no navegador (pasta `frontend/`) |
| Cozinha (faz o trabalho) | **Backend** | O "cérebro" que faz as contas (pasta `backend/`) |
| Garçom (leva e traz pedidos) | **API** | A "ponte" entre frontend e backend |
| Despensa (guarda as coisas) | **Banco de dados** | Onde ficam as fazendas, safras, custos |

Vamos ver cada um.

---

## 1. Frontend — "a cara" do sistema (o salão)

O **frontend** é tudo que você **vê e clica**: botões, formulários, gráficos, menus.
Ele roda **no seu navegador** (Chrome, Firefox, etc.). No FADA, o frontend mostra as
telas: Início, Minha Lavoura, Financeiro, Assistente…

O frontend, sozinho, **não sabe fazer as contas**. Ele é como o garçom mostrando o
cardápio: bonito e organizado, mas a comida vem da cozinha. Quando você clica em
"calcular estimativa", o frontend **pede** o resultado para o backend e depois
**mostra** o que recebeu.

## 2. Backend — "o cérebro" (a cozinha)

O **backend** é onde o trabalho de verdade acontece: as contas de produtividade, de
custo, de risco. Ele roda em um **servidor** (um computador, que pode estar na nuvem
ou na sua própria máquina enquanto você desenvolve).

O backend recebe pedidos ("me dá a estimativa de Horizontina para a safra 2026/27"),
faz as contas e devolve a resposta. Ele **guarda e busca** dados no banco de dados.

## 3. API — "a ponte" (o garçom)

**API** significa *Application Programming Interface* (Interface de Programação de
Aplicações). Não se assuste com o nome — é simplesmente o **conjunto de "endereços"**
pelos quais o frontend conversa com o backend.

Pense em cada endereço como um item do cardápio. Por exemplo:

- `GET /api/v1/farms` → "me dê a lista de fazendas" (o `GET` significa "buscar")
- `POST /api/v1/quick-log` → "registre esta operação" (o `POST` significa "enviar/criar")

Esses endereços se chamam **endpoints** ("pontos de chegada"). O frontend faz uma
**requisição** (request) para um endpoint, e o backend devolve uma **resposta**
(response). A conversa acontece pela internet, usando um formato de texto chamado
**JSON** (explicado abaixo).

> **Por que existe essa separação (frontend ↔ API ↔ backend)?** Porque permite trocar
> ou melhorar uma parte sem mexer na outra. Você pode redesenhar todas as telas
> (frontend) sem tocar nas contas (backend), desde que continue "pedindo" pelos mesmos
> endereços (API). É como reformar o salão do restaurante sem mexer na cozinha.

## 4. Banco de dados — "a memória" (a despensa)

O **banco de dados** é onde o sistema **guarda informação de forma permanente**: as
fazendas cadastradas, os talhões, as safras, os custos registrados. Se você desligar
o computador e ligar de novo, os dados continuam lá.

No FADA, durante o desenvolvimento, usa-se um banco simples chamado **SQLite** — que é
literalmente **um único arquivo** no disco (`data/fada.db`). Em produção (uso real em
larga escala), pode-se trocar por um banco mais robusto chamado **PostgreSQL**. O
legal é que o FADA foi feito para funcionar com os dois sem mudar o código.

## Termos que você vai encontrar muito

### JSON — o "idioma" da conversa
**JSON** é um formato de texto para representar dados de forma organizada. Exemplo de
uma resposta do FADA em JSON:

```json
{
  "municipality": "Horizontina",
  "estimated_yield_sc_ha": 51.2,
  "confidence_interval_sc_ha": [39.6, 62.0]
}
```

Lê-se: "o município é Horizontina, a produtividade estimada é 51,2 sacas/hectare, e a
faixa de incerteza vai de 39,6 a 62,0". O frontend recebe esse texto e o transforma em
números bonitos na tela. JSON é só uma forma padronizada de empacotar informação.

### Servidor e cliente
- **Servidor**: o computador que **serve** (responde) os pedidos — aqui, o backend.
- **Cliente**: quem **faz** os pedidos — aqui, o frontend no seu navegador.

### "localhost" e portas
Quando você roda tudo na sua máquina, o endereço do backend é `http://localhost:8000`.
- `localhost` = "este computador aqui mesmo".
- `8000` = a **porta**, como o número de uma sala num prédio. O backend "atende" na
  porta 8000; o frontend, na porta 3000. (Por isso, no Capítulo sobre rodar o projeto,
  você abre dois terminais: um para cada porta.)

### Requisição (request) e resposta (response)
Toda conversa é um par: o cliente manda uma **requisição** ("quero X"), o servidor
devolve uma **resposta** ("aqui está X" ou "deu erro Y").

### Código de status (200, 404, 422, 500…)
Junto com cada resposta vem um **número de status** que diz se deu certo:
- **200/201** = deu certo. ✅
- **404** = "não encontrado" (você pediu algo que não existe). ❓
- **422** = "você mandou os dados errados" (ex.: faltou preencher um campo).
- **500/503** = "deu erro do lado do servidor" / "serviço indisponível". ❌

## Resumo do capítulo

- **Frontend** = a cara (telas no navegador). **Backend** = o cérebro (as contas).
- **API** = a ponte/cardápio de endereços (**endpoints**) entre os dois.
- **Banco de dados** = a memória permanente (no FADA dev: o arquivo SQLite).
- A conversa acontece pela internet, em **JSON**, com **requisições** e **respostas**,
  cada uma com um **código de status**.

➡️ Próximo: **[Capítulo 3 — Conceitos de IA e modelos](03-conceitos-de-ia-e-modelos.md)**.
