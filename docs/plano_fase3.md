# Fase 3: código por estado (plano)

> Plano proposto pela IA em 2026-11-07 e **aprovado pelo autor no mesmo dia**, com as 3 recomendações do fim (D-081). Fase 3 do [`plano_projeto.md`](plano_projeto.md).

## Objetivo
Tirar do código o que só vale para MG e levar para a configuração por estado, para que um estado novo seja "só dado novo" (objetivo do autor, 2026-10-31).

**Pronto quando** (critério do `plano_projeto.md`): com `ufs: [MG]`, o resultado é **idêntico** ao de hoje (as 33 tabelas do gold com o mesmo hash de conteúdo e os 10 números iguais) e um teste com **dois estados sintéticos** passa.

## Onde o código supõe MG hoje (levantado em 2026-11-07)

| Camada | O que está fixo em MG | Onde |
|---|---|---|
| Coleta | pacote da RAIS por UF (`RAIS_VINC_PUB_MG_ES_RJ.7z`), código IBGE da UF, UF padrão `"MG"` nos coletores | `src/ingest/rais.py`, `ibge.py`, `cnj_serventias.py`, `cnj_complementares.py`, `cnj_arrecadacoes.py` |
| Escopo | `ufs: [MG]`, `cod_uf_ibge: {MG: 31}`, snapshots | `config/escopo.yaml` (já é config: só passa a ser lido em todo lugar) |
| Contratos | totais de controle da arrecadação (`controle_arrecadacao_mg`), `uf = 'MG'` no SQL | `src/quality/contratos.py`, `config/qualidade.yaml` |
| Reconciliações | rótulos e totais "(MG)", reserva da distribuição "MG inteiro" (D-022) | `src/quality/reconciliacao.py`, `src/model/distribuicao.py` |
| Gold | `"uf": "MG"` na `fato_mercado_uf`; visões e ranking sem a coluna `uf` | `src/transform/gold.py` |
| Análises | "fator de MG" e série de MG na previsão; "parte de MG" nos grupos | `src/analise/previsao.py`, `grupos.py`, `tabelas.py` |
| Painel | `uf: str = "MG"` em 41 lugares, textos "de MG" | `src/painel/analises.py`, `app/` |
| Chat | `UFS_COM_DADOS = ("MG",)`, textos e prompt | `src/agent/ferramentas.py`, `config/prompts/` |

## Desenho proposto

1. **`config/estados.yaml` (novo)**, uma entrada por UF, com fonte em cada valor:
   - código IBGE, nome, pacote da RAIS (o arquivo do PDET que contém a UF);
   - totais de controle da arrecadação (os de MG saem de `config/qualidade.yaml` para cá);
   - normas locais da corregedoria (MG: nenhuma a mais hoje), apelidos de municípios (hoje `config/apelidos_municipios.yaml`);
   - premissas: MG usa as da versão vigente; outro estado herda as de MG com `fonte: suposição` até a calibração (Fase 6).
2. **Coleta:** os coletores leem a UF e o pacote de `estados.yaml`; o padrão continua a lista `ufs` do escopo.
3. **Silver:** já tem `uf` nas tabelas do CNJ; a RAIS e o IBGE ganham `uf` (derivada do código do município) se ainda não tiverem.
4. **Gold:** cada tabela por UF ou por município ganha a coluna `uf`; o motor roda por UF (o modelo é o mesmo, as premissas vêm do estado); a reserva da distribuição salarial passa de "MG inteiro" para "a UF inteira". Totais nacionais (visão "Brasil") só como soma das UFs, na Fase 4.
5. **Contratos e reconciliações:** parametrizados pela UF; os totais de controle vêm de `estados.yaml`; UF sem controle definido gera aviso, não erro.
6. **Análises:** previsão, grupos, tornado e Monte Carlo recebem a UF (a série e o "fator" passam a ser da UF).
7. **Painel e chat:** `uf` vira parâmetro com padrão vindo da config (não mais `"MG"` literal); textos com o nome da UF; seletor de estado e visão "Brasil" ficam para depois do primeiro estado novo (itens 3 da Fase 3 e 5 da Fase 4).

## Ordem de execução (uma branch e um PR por bloco)
1. `config/estados.yaml` e leitura nos coletores e contratos (sem mudar nenhum resultado). **Feito em 2026-11-10** (branch `fase-3-bloco-1-estados`; silver refeito do bronze idêntico ao do banco real; detalhes no `diario.md`).
2. Coluna `uf` no gold e o motor por UF; conferir na cópia: 33 tabelas com o mesmo conteúdo (fora a coluna `uf` nova) e os 10 números iguais. **Feito em 2026-11-10** (branch `fase-3-bloco-2-gold-uf`): as 20 tabelas do `gold.construir` com `uf`; as 13 `analise_*` sem a coluna até o bloco 3.
3. Análises por UF; mesma conferência.
4. Painel e chat sem `"MG"` literal; testes do painel e do chat iguais.
5. Teste com dois estados sintéticos (dados inventados, marcados como sintéticos, em `tests/`): pipeline do zero, contratos, gold com as duas UFs separadas e somas por UF corretas.
6. Carga oficial (pedido do autor) só se alguma tabela mudar de conteúdo; senão, só os pacotes, se o esquema mudar (coluna `uf`).

## Questões para o autor (respondidas em 2026-11-07: as 3 recomendações, D-081)
1. **Coluna `uf` nas tabelas públicas:** acrescentar já (muda o esquema do `data/publico` e do `data/completo`, com carga oficial) ou só quando entrar o segundo estado? **Recomendação:** já, para o critério "idêntico" ser conferido uma vez só, com o esquema final.
2. **Premissas de um estado sem calibração:** herdar as de MG com `fonte: suposição` (recomendação) ou bloquear a publicação do modelo daquele estado até a Fase 6? A camada 1 (Fase 4) não usa o modelo, então a questão só pesa na Fase 6.
3. **Apelidos e normas locais:** mover para `estados.yaml` (recomendação: um arquivo só por estado) ou manter arquivos separados por tema?
