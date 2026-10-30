# Latência do chat — depois dos ajustes (2026-10-28 23:59)

Modelo `gemini-3.8-flash` (reserva `gemini-3.5-flash-lite`), raciocínio `low`, prompt v3, banco de demonstração (`data/publico`). Medido por `scripts/medir_latencia_chat.py` no WSL, com a API real. As chamadas ao modelo medem até a resposta começar a chegar (cabeçalhos HTTP); com streaming, o resto do texto chega depois, dentro do total.

## Etapas fixas (uma vez por sessão)

| Etapa | Tempo |
|---|---|
| Dados: montar e abrir o banco de demonstração (já montado no disco) | 0.03 s |
| Criar o cliente HTTP do Gemini | 47 ms |

## Por pergunta

| Pergunta | Chamadas ao modelo | Ferramentas | Esperas (429, erro, tempo-limite) | Montar | Primeiro texto | Total |
|---|---|---|---|---|---|---|
| quantos cartórios de protesto tem em MG? | 2 × (0.9 + 0.7 s) | 1 (437 ms) | 1 (0.5 s) | 0.2 ms | 2.7 s | 3.0 s |
| qual o prêmio anual do cartório de CNS 048256? | 2 × (0.7 + 0.8 s) | 1 (17 ms) | 0 (0.0 s) | 0.0 ms | 1.6 s | 1.9 s |
| quais são os seis tipos de cartório? | 2 × (0.7 + 1.2 s) | 1 (24 ms) | 0 (0.0 s) | 0.0 ms | 2.1 s | 2.6 s |
| qual a data de referência dos dados da RAIS? | 2 × (1.9 + 0.7 s) | 1 (21 ms) | 0 (0.0 s) | 0.0 ms | 2.7 s | 3.0 s |
| qual artigo fala do regime especial? | 2 × (0.7 + 2.8 s) | 1 (20 ms) | 0 (0.0 s) | 0.0 ms | 3.7 s | 4.1 s |

**Medianas** (perguntas sem erro, 5 de 5): primeiro texto 2.7 s; resposta completa 3.0 s.

Modelos que responderam: gemini-3.5-flash-lite.

## Respostas

- **quantos cartórios de protesto tem em MG?** — Minas Gerais possui 305 cartórios de protesto ativos, que contam com 1.373 empregados em regime CLT.  Fonte: gold.mercado_filtro_uf (CNJ/Justiça Aberta, RAIS/PDET e SUSEP SES; estimativa de mercado com premissas públicas) · referência: carga 2026-10-28 · premissas: v3
- **qual o prêmio anual do cartório de CNS 048256?** — O prêmio anual estimado para o cartório de CNS 048256 (Uberaba, Classe 3) é de **R$ 2,3 mil**.   Vale notar que os valores apresentados para cartórios específicos são estimativas do modelo estatístico do painel e não uma avaliação oficial ou contábil da serventia.  Fonte: gold.serventia_publico (CNJ
- **quais são os seis tipos de cartório?** — Os seis tipos de cartório definidos pelo modelo do painel (agrupados por receita, empregados CLT, número de atribuições e situação) são:  1. **Vagas pequenas** (Grupo 1) 2. **Providas pequenas (Notas e RCPN)** (Grupo 2) 3. **Providas médias de uma atribuição** (Grupo 3) 4. **Registro completo (RI, R
- **qual a data de referência dos dados da RAIS?** — A data de referência dos dados da RAIS (Relação Anual de Informações Sociais) é 31 de dezembro de 2025.  Fonte: silver.fonte_metadados, qualidade.reconciliacoes e qualidade.checagens (CNJ/Justiça Aberta, RAIS/PDET e SUSEP SES; estimativa de mercado com premissas públicas) · referência: 2026-10-28 · 
- **qual artigo fala do regime especial?** — O regime especial de acompanhamento fiscalizatório está previsto principalmente no **Artigo 16 do Provimento CNJ 227/2026**. Ele se aplica quando é verificada a insolvência trabalhista da serventia, caracterizada pela manutenção do déficit de cobertura sem a apresentação de garantia no prazo regulam
