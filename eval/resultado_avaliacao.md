# Avaliação do chat (2026-10-28)

Modelo `gemini-3.8-flash` (Gemini, nível gratuito; reserva `gemini-3.5-flash-lite`), raciocínio `low`, temperatura 0, prompt do agente v2. Gabarito `eval/gabarito_chat.csv` congelado (SHA-256 7f7f471d713c…, 5 perguntas). Dados do conjunto público (`data/publico`). Correção automática (`src/agent/avaliacao.py`): número a até 1% do esperado, palavras obrigatórias, recusa sem valor em R$; resposta com número sem apoio nas ferramentas, na pergunta ou no prompt conta como alucinação e como erro.

**Meta (fixada antes da primeira rodada, D-065):** versão (c) com acerto ≥ 85% e nenhum número inventado nas armadilhas.

## Resumo

| Medida | (c) com ferramentas |
|---|---|
| Respondidas | 5/5 |
| Acertos | 5/5 (100%) |
| Com número inventado | 0/5 (0%) |
| Sem a linha "Fonte" | 0/5 (0%) |
| "Não sei" corretos | — |
| Latência média | 6.6 s |

**Meta cumprida:** (c) acertou 100% (meta 85%); armadilhas com número inventado: nenhuma.

## Acerto por tipo

| Tipo | (c) com ferramentas |
|---|---|
| numeros | 5/5 (100%) |

## Pergunta a pergunta

| # | Tipo | Pergunta | Esperado | (c) com ferramentas |
|---|---|---|---|---|
| 1 | numeros | Quantas serventias (cartórios) ativas há em Minas Gerais? | 2525 | ✅ Minas Gerais possui 2.525 serventias ativas, que empregam 12.134 funcionários pelo regime da CLT.  Fonte: gold.fato_mercado_uf (CNJ/Justiça Aberta, RAIS/PDET e  |
| 2 | numeros | Quantos empregados CLT os cartórios de MG declaram ao CNJ? | 12134 | ✅ Os cartórios de Minas Gerais declaram um total de 12.134 empregados sob o regime CLT.  Esse número engloba o total de serventias ativas no estado (2.525 unidade |
| 3 | numeros | Quantas serventias de MG são obrigadas pelo Provimento 227, no cenário base? | 1121.3 | ✅ No cenário base, cerca de 1.121 serventias de Minas Gerais são obrigadas a contratar o seguro-garantia pelo Provimento 227 (com faixa provável entre 1.103 e 1.1 |
| 4 | numeros | Qual o passivo trabalhista estimado das serventias obrigadas em MG? | 238104261 | ✅ O passivo trabalhista estimado das serventias obrigadas em Minas Gerais é de R$ 238,1 milhões no cenário base, com uma faixa provável que vai de R$ 216,4 milhõe |
| 5 | numeros | Qual o déficit de cobertura estimado em MG, com a regra do Provimento 227 mantida? | 34106244 | ✅ Com a regra do Provimento 227 mantida, o déficit de cobertura estimado para os cartórios de Minas Gerais é de R$ 34,1 milhões, com faixa provável (P5–P95) entre |
