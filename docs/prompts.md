# Pedidos por fase

Pedidos prontos para usar com a IA. Abra uma conversa nova para cada fase: o SPEC, o CLAUDE.md e o diário carregam o contexto.

---

## Fase 0: viabilidade (testar se os dados existem)

> Leia @CLAUDE.md, @docs/SPEC.md e @docs/diario.md e execute só a Fase 0.
> Explique em linguagem simples o que vai fazer antes de cada etapa.
> 1. Instale o uv e o Python 3.12 pelo uv.
> 2. Veja a RAM e a GPU do computador e me diga qual modelo do Ollama você recomenda. Se eu precisar instalar o Ollama, me diga como.
> 3. Baixe os Provimentos 227, 213 e 243 e confirme os pontos listados na Fase 0.
> 4. Teste cada fonte do §1.1, salve uma amostra pequena em data/samples/ e me mostre os campos encontrados.
> 5. Crie docs/viabilidade.md com uma linha por fonte.
> Pare e me mostre o resultado antes de qualquer decisão que mude o SPEC.

---

## Fase 1: painel de MG

> Execute só a Fase 1 do SPEC, usando as decisões de docs/viabilidade.md e do diário.
> Antes de codar, me mostre o plano: arquivos que vai criar, tabelas e funções do modelo.
> Comece pelas funções de src/model com testes, depois a ingestão de MG, depois as páginas Mercado, Simulador e Qualidade dos dados.
> Pare quando o critério de aceite da Fase 1 for cumprido e me diga como abrir o painel.

---

## Fase 2: Brasil inteiro e qualidade

> Execute só a Fase 2 do SPEC. Expanda para todas as UFs disponíveis e implemente as reconciliações do §4.
> Me mostre as divergências encontradas entre as fontes.

---

## Fase 3: chat

> Execute só a Fase 3 do SPEC.
> Primeiro passo: me ajude a montar eval/gabarito_chat.csv com perguntas dos 4 tipos. Eu confirmo as respostas esperadas. Não ajuste o prompt do chat antes de eu congelar o gabarito.

(depois do gabarito congelado)

> O gabarito está congelado. Implemente as ferramentas, a integração com o Ollama e a página Chat. Rode o eval das versões e me mostre a comparação.

---

## Fase 4: radar (opcional)

> Execute só a Fase 4 do SPEC, começando pela versão simples sem IA.

---

## Fase 5: entrega

> Execute a Fase 5 do SPEC: README completo e relatório final do eval.
> Separe do docs/erros_ia.md os 2 ou 3 casos mais interessantes para os slides e me explique por quê.

---

## Pedidos úteis a qualquer momento

- **Retomar:** "Leia o CLAUDE.md, o SPEC e o diário. Em que ponto estamos e qual é o próximo passo?"
- **Entender:** "Me explique em linguagem simples o que você acabou de fazer e por quê."
- **Revisar:** "Revise o que foi feito nesta fase contra o critério de aceite do SPEC. O que falta ou está frágil?"
- **Fechar a sessão:** "Atualize o diário e o erros_ia.md com o que aconteceu nesta sessão. Não faça commit."
