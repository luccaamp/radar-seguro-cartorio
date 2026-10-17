# Prompts por fase

Prompts prontos para usar com a IA. Abra uma sessão nova para cada fase: o SPEC, o CLAUDE.md e o diário carregam o contexto.

---

## Sessão 0: leitura e dúvidas (antes de qualquer código)

> Leia o `CLAUDE.md`, o `docs/SPEC.md` inteiro e o `docs/diario.md`. Não escreva código ainda.
> Me responda:
> 1. O que ficou ambíguo ou contraditório no SPEC?
> 2. Quais decisões você precisa que eu tome antes da Fase 0?
> 3. Que riscos você vê que o SPEC não cobre?

Depois de responder, atualize o SPEC com as decisões tomadas.

---

## Fase 0: viabilidade

> Execute só a Fase 0 do `docs/SPEC.md`.
> Para cada fonte do §1.1, teste o acesso real, baixe uma amostra pequena para `data/samples/` e me mostre os campos encontrados.
> Crie `docs/viabilidade.md` com uma linha por fonte: status (ok / parcial / bloqueada), formato, campos, cobertura, se há download em massa e o plano B.
> Ao final, recomende a fonte do universo e o armazenamento persistente, e pare para eu decidir.

---

## Fase 1: fatia vertical (MG)

> Execute só a Fase 1 do SPEC, usando as decisões registradas em `docs/viabilidade.md` e no diário.
> Antes de codar, me mostre o plano: arquivos que vai criar, tabelas silver e gold, e assinatura das funções do modelo.
> Comece pelas funções de `src/model` com testes, depois a ingestão de MG, depois as páginas Mercado e Simulador.
> Pare quando o critério de aceite da Fase 1 for cumprido.

---

## Fase 2: Brasil inteiro e qualidade

> Execute só a Fase 2 do SPEC. Expanda para todas as UFs disponíveis e implemente os contratos e as reconciliações do §4.
> Gere o relatório de qualidade e registre as divergências no diário.

---

## Fase 3: radar

> Execute só a Fase 3 do SPEC.
> Primeiro passo: me ajude a montar o gabarito em `eval/gabarito_radar.csv`. Colete os documentos candidatos, mas **eu** faço os rótulos. Não escreva o prompt do radar antes de eu congelar o gabarito.

(depois do gabarito congelado)

> O gabarito está congelado. Siga com coletores, pipeline, aprovação, resumo diário e agendamento, nessa ordem. Rode contra o gabarito e me mostre as métricas.

---

## Fase 4: agente de dúvidas

> Execute só a Fase 4 do SPEC.
> Primeiro passo: me ajude a montar `eval/gabarito_chat.csv` com perguntas dos 4 tipos. **Eu** confirmo as respostas esperadas.

(depois do gabarito congelado)

> Implemente as ferramentas da camada semântica, as 4 versões do agente e a integração na página Chat. Rode o eval e me mostre a comparação.

---

## Fase 5: entrega

> Execute a Fase 5 do SPEC: deploy, README completo e o relatório final do eval.
> Separe do `docs/erros_ia.md` os 2 ou 3 casos mais interessantes para os slides e me explique por quê.

---

## Prompts úteis a qualquer momento

- **Retomar:** "Leia o CLAUDE.md, o SPEC e o diário. Em que ponto estamos e qual é o próximo passo?"
- **Revisar:** "Revise o que foi feito nesta fase contra o critério de aceite do SPEC. O que falta ou está frágil?"
- **Fechar a sessão:** "Atualize o diário e o erros_ia.md com o que aconteceu nesta sessão."
