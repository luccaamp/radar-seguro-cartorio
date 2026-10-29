# Latência do chat — antes dos ajustes (2026-10-28 23:11)

Modelo `gemini-3.8-flash` (reserva `gemini-3.5-flash-lite`), raciocínio `low`, prompt v2, banco de demonstração (`data/publico`). Medido por `scripts/medir_latencia_chat.py` no WSL, com a API real. As chamadas ao modelo medem até a resposta começar a chegar (cabeçalhos HTTP); com streaming, o resto do texto chega depois, dentro do total.

## Etapas fixas (uma vez por sessão)

| Etapa | Tempo |
|---|---|
| Dados: montar e abrir o banco de demonstração (já montado no disco) | 0.03 s |
| Criar o cliente HTTP do Gemini | 54 ms |

## Por pergunta

| Pergunta | Chamadas ao modelo | Ferramentas | Esperas (429/erro) | Montar | Primeiro texto | Total |
|---|---|---|---|---|---|---|
| quantos cartórios de protesto tem em MG? | 2 × (2.3 + 1.3 s) | 1 (418 ms) | 1 (0.7 s) | 0.0 ms | 4.8 s | 4.8 s |
| qual o prêmio anual do cartório de CNS 048256? | 2 × (3.5 + 1.6 s) | 1 (19 ms) | 0 (0.0 s) | 0.0 ms | 5.2 s | 5.2 s |
| quais são os seis tipos de cartório? | 2 × (2.3 + 2.2 s) | 1 (25 ms) | 0 (0.0 s) | 0.0 ms | 4.6 s | 4.6 s |
| qual a data de referência dos dados da RAIS? | 2 × (1.9 + 1.4 s) | 1 (20 ms) | 0 (0.0 s) | 0.0 ms | 3.4 s | 3.4 s |
| qual artigo fala do regime especial? | 2 × (1.5 + 2.2 s) | 1 (25 ms) | 0 (0.0 s) | 0.0 ms | 3.8 s | 3.8 s |

**Medianas** (perguntas sem erro, 5 de 5): primeiro texto 4.6 s; resposta completa 4.6 s.

Modelos que responderam: gemini-3.5-flash-lite.

## Respostas

- **quantos cartórios de protesto tem em MG?** — Minas Gerais possui 305 serventias ativas de protesto, que contam com 1.373 empregados em regime CLT.  Fonte: gold.mercado_filtro_uf (CNJ/Justiça Aberta, RAIS/PDET e SUSEP SES; estimativa de mercado com premissas públicas) · referência: carga 2026-10-28 · premissas: v3
- **qual o prêmio anual do cartório de CNS 048256?** — O prêmio anual estimado para o cartório de CNS 048256 (Uberaba, MG) é de **R$ 2,3 mil**.   Vale lembrar que os valores exibidos para cartórios específicos são estimativas do modelo estatístico do painel, e não uma avaliação contábil oficial da própria serventia.  Fonte: gold.serventia_publico (CNJ/J
- **quais são os seis tipos de cartório?** — Os seis grupos de cartórios (definidos por porte, receita, número de empregados e atribuições) são:  1. **Vagas pequenas**: 688 serventias (28,15% do total), majoritariamente vagas (interinas) e de menor receita. 2. **Providas pequenas (Notas e RCPN)**: 634 serventias (25,94% do total), focadas em n
- **qual a data de referência dos dados da RAIS?** — A data de referência dos dados da RAIS (Relação Anual de Informações Sociais) é 31 de dezembro de 2025.   Esses dados trazem o registro dos vínculos empregatícios formais até o final daquele ano.  Fonte: silver.fonte_metadados, qualidade.reconciliacoes e qualidade.checagens · referência: 2025-12-31 
- **qual artigo fala do regime especial?** — O regime especial de acompanhamento fiscalizatório é tratado no Artigo 16 do Provimento CNJ 227/2026, que pode ser aplicado caso seja verificada a insolvência trabalhista do delegatário e mantido o déficit de cobertura sem a garantia no prazo regulamentar. (Lembre-se de que esta é uma explicação da 
