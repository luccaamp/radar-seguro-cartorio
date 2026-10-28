# Dicionário de dados

Tabelas do banco local `data/radar.duckdb` (cópia em Parquet em `data/silver/` e `data/gold/`).
Escrito à mão e conferido contra o banco em 2026-10-21; a geração por script está prevista na E1. Nenhuma tabela silver ou gold tem nome, CPF ou contato de titular (SPEC §6).

## Silver

### `silver.serventia` — uma linha por CNS (Justiça Aberta)
| Coluna | Tipo | Descrição |
|---|---|---|
| cns | texto | Código Nacional de Serventia (chave) |
| uf | texto | UF da serventia |
| cidade_fonte | texto | nome do município como veio da fonte |
| cod_ibge | inteiro | código IBGE de 7 dígitos (junção por nome normalizado + `config/apelidos_municipios.yaml`) |
| status | texto | Ativo / Inativo / Extinto |
| tipo_cartorio | texto | PRIVATIZADO / OFICIALIZADO / PUBLICO |
| situacao_juridica | texto | PROVIDO / VAGO / SOB INTERVENÇÃO / CONVERSÃO EM DILIGÊNCIA (vazio nas inativas) |
| data_situacao | data | data da decisão da situação jurídica |
| atribuicoes | texto | atribuições separadas por " \| " |
| n_atribuicoes | inteiro | quantidade de atribuições |
| notas, rcpn, ri, rtd, rcpj, protesto, maritimo, distribuicao, interdicoes_tutelas | booleano | uma coluna por atribuição |

Descartados no silver: responsável, substitutos, telefone, e-mail, site, endereço e denominação fantasia.

### `silver.serventia_colaboradores` — uma linha por CNS ativo
| Coluna | Tipo | Descrição |
|---|---|---|
| cns | texto | chave |
| informado | booleano | a rota respondeu com as contagens |
| clt, estatutarios, estagiarios, terceirizados, total_declarado | inteiro | contagens declaradas pela serventia (sem data por serventia) |
| informatizada | texto | S/N |
| data_coleta | texto | data da coleta |

### `silver.serventia_arrecadacao` — uma linha por CNS × período × versão
| Coluna | Tipo | Descrição |
|---|---|---|
| cns | texto | serventia |
| ano, semestre | inteiro | semestre 1 (jan–jun), 2 (jul–dez) ou vazio para períodos anuais antigos |
| periodo_inicio, periodo_fim | data | período declarado |
| informado | booleano | falso quando a fonte diz "NÃO INFORMADO" |
| arrecadacao | decimal | R$ no período ("receita bruta" no Justiça Aberta) |
| valor_fonte | texto | texto original quando não numérico |
| atos_praticados | inteiro | atos no período |
| versoes_fonte | inteiro | quantas versões diferentes a fonte traz para o mesmo período |
| conflito_fonte | booleano | verdadeiro quando há mais de uma versão com valores diferentes |
| versao | inteiro | 1, 2, ... (ordem em que a fonte entregou) |

### `silver.rais_vinculo` — uma linha por vínculo da RAIS (CNAE 6912-5/00)
| Coluna | Tipo | Descrição |
|---|---|---|
| id_vinculo | inteiro | identificador sequencial (sem relação com pessoa) |
| ano_base | inteiro | ano da RAIS |
| ativo_31_12 | booleano | vínculo ativo em 31/12 |
| tipo_vinculo | inteiro | código do layout RAIS 2020 |
| prazo_indeterminado | booleano | tipo em {10, 15, 20, 25} (D-009) |
| tipo_estabelecimento | texto | CNPJ / CAEPF / CEI |
| rem_dezembro, rem_media | decimal | remuneração nominal de dezembro e média anual (R$) |
| tempo_emprego_meses | decimal | tempo no emprego em 31/12 (meses) |
| horas_contratadas | decimal | horas semanais |
| mes_admissao, mes_desligamento | inteiro | 0 = não houve no ano |
| cbo | texto | ocupação |
| cod_ibge | inteiro | município (7 dígitos; a RAIS traz 6) |

### `silver.cnpj_estabelecimento` — estabelecimentos com CNAE 6912-5/00 (conferência)
cnpj_basico, matriz_filial, uf, mun_rfb (código da Receita), municipio_fonte, cod_ibge, situacao (ativa, baixada...), cnae_principal, natureza_juridica, data_inicio. Sem razão social, nome fantasia ou contato.

### `silver.municipio_ibge`
cod_ibge (chave), cod_ibge6, uf, nome, nome_norm, microrregiao, mesorregiao, regiao_imediata, regiao_intermediaria, populacao, ano_populacao, nome_regiao_corrigido_por.

### `silver.malha_municipio` — uma linha por município (malha do IBGE)
uf, ordem, cod_ibge, feature_json (a geometria do município em GeoJSON). Fica no silver para o gold se recalcular só com o silver (D-029).

### `silver.susep_garantia` — SES, ramos 0775 (setor público) e 0776 (setor privado)
ano_mes, cod_entidade, cod_grupo, ramo e os valores mensais em R$ (premio_direto, premio_emitido2, premio_ganho, sinistro_ocorrido, desp_com etc.), como no `Ses_seguros.csv`.

### `silver.indice_preco`
indice (IPCA / INPC), ano_mes, numero_indice (base dez/1993 = 100).

### `silver.fonte_metadados` — uma linha por arquivo do bronze lido
fonte, arquivo, sha256, bytes, url, coletado_em, **data_referencia** (exibida no painel), observacao.

## Gold

Calculado por `src/motor.py` com a versão vigente das premissas. Níveis: `min`, `base`, `max` (todas as premissas no mesmo nível). Regras de classe: `v2` (R$ 300 mil, base) e `v1` (R$ 100 mil). Valores em R$ por ano.

O gold tem 26 tabelas do modelo (21 sem o prefixo `interno_`, entre elas a `serventia_publico` da D-048, e 5 internas) e, a partir da Etapa 2 (2026-10-28), mais 13 tabelas `analise_*` da mineração (6 da D-043, 2 da D-044 e 5 das melhorias de confiança, D-045 e D-046): 39 no total. "Pública" = está no conjunto público (`config/publico.yaml`, `data/publico/`) e o painel lê; as 18 públicas passaram pelo auditor de ataque por diferença e pelos contratos de LGPD (D-026 a D-030). Conferido contra o banco em 2026-10-21; as `analise_*`, contra um pipeline do zero numa cópia em 2026-10-28.

### Totais, sensibilidades e execução
| Tabela | Grão | Colunas principais | Pública? |
|---|---|---|---|
| `gold.fato_mercado_uf` | UF × nível × regra × cenário do STF (18 linhas) | n_serventias_ativas, clt, passivo_todas, n_universo, n_indeterminadas_universo, passivo_universo, n_deficit, valor_descoberto, bens_proprios, fianca, `mercado_*` e `seguradora_*` (importancia_segurada, premio_emitido, sinistro_esperado, comissao, despesa_administrativa, resultado_tecnico) | sim |
| `gold.sensibilidade_rateio` | método de rateio (4) | os mesmos totais de `fato_mercado_uf` (base, v2, mantém) | sim |
| `gold.serventia_publico` | serventia ativa (2.525) | cns, uf, cod_ibge, municipio, regiao_imediata, regiao_intermediaria, situacao_juridica, tipo_cartorio, atribuicoes, clt, receita_ref, origem_receita, semestres_validos, classe (regra base), classe_v1, classificacao_aproximada, motivo, peso_universo, passivo, passivo_medio_vinculo, n_deficit, valor_descoberto, importancia_segurada, premio_emitido (nível base, STF mantém). Somada, dá o `fato_mercado_uf` (contrato do gold). Sem nome de pessoa | sim (D-038, D-048) |
| `gold.sensibilidade_premissas` | variação (6): base, INPC, reserva da distribuição = MG, três leituras do art. 16, § 1º (D-023) | chave, variacao, providos_acima_limite, peso_classe_indeterminada_base e os mesmos totais de `fato_mercado_uf` | sim |
| `gold.diferenca_regra_classe` | nível | universo, passivo, IS e prêmio em v2 e v1 | sim |
| `gold.execucao` | regra (v1, v2) | regra_classe, peso_classe_indeterminada_base, versao_premissas, executado_em, fator_inpc e mes_inpc_final (a correção pelo INPC saiu da base na D-020; os dois campos continuam e alimentam só a linha "INPC" da sensibilidade e o texto do Início), ano_enquadramento, metodo_rateio, limiar_lgpd | sim |
| `gold.dim_municipio` | município (853) | cod_ibge, municipio, mesorregiao, populacao, n_serventias, clt (a coluna `clt` não vai para o conjunto público, D-029) | sim, sem `clt` |

### Mapa, áreas e filtros do Mercado (D-026, D-027)
| Tabela | Grão | Colunas principais | Pública? |
|---|---|---|---|
| `gold.geo_area_municipio` | município com serventia (851) | cod_ibge, area_id (a área do mapa a que o município pertence) | sim |
| `gold.geo_mapa_publico` | área do mapa sem filtro (385) | area_id, area_nome, tipo (`municipio` ou `regiao_agregada`), n_municipios, n_serventias, geometria (municípios com menos de 3 serventias dissolvidos por região imediata) | sim |
| `gold.geo_mapa_filtro` | visão com filtro × área (85) | area_id, geometria, visao (ex.: `classe=2`, `situacao=VAGO`, `atribuicao=ri`) | sim |
| `gold.geo_regiao_imediata` | região imediata (70) | area_id, geometria | sim |
| `gold.geo_sem_serventia` | município sem serventia no cadastro do CNJ (2) | area_id, geometria | sim |
| `gold.mercado_area_publico` | área do mapa sem filtro (385) | area_id, area_nome, tipo, n_municipios, n_serventias, clt, passivo, passivo_universo, n_universo, n_deficit, valor_descoberto (nível base, regra base) | sim |
| `gold.mercado_filtro_area` | visão com filtro × área (511) | visao, filtro, valor, area_id, area_nome, nivel_area (`regiao_imediata`, `regiao_intermediaria`, `outras`), n_regioes e os totais da área; só o que o auditor aprovou | sim |
| `gold.mercado_filtro_regiao` | visão × região imediata (768) | visao, regiao_imediata, area_id (a área publicada que contém a região naquela visão; vazio quando a área foi suprimida) | sim |
| `gold.mercado_filtro_uf` | visão × regra × nível (78) | visao, filtro, valor, regra_classe, nivel, publicado (falso quando o auditor suprimiu) e os totais de `fato_mercado_uf` | sim |
| `gold.ranking_municipio_publico` | município × métrica (1.276) | cod_ibge, municipio, metrica (`n_serventias`, `clt`, `passivo`, `valor_descoberto`), valor, posicao, n_municipios, pct_mg; só municípios com 3 ou mais serventias | sim |

### Simulador por totais (modo demonstração, D-029)
| Tabela | Grão | Colunas principais | Pública? |
|---|---|---|---|
| `gold.simulador_variantes` | variante (80): regra × rateio × uma premissa do passivo por vez | variante_id, regra_classe, metodo_rateio, premissa_variada, fap, fracao_ferias_vencidas_pendentes, inss_aviso_previo, limiar_vinculos_distribuicao_municipal, base_remuneracao_rais e os totais do passivo e do universo | sim |
| `gold.simulador_base_classe` | variante × faixa de déficit (160) | variante_id, faixa (`classe_2`, `classe_3`), peso_com_passivo, passivo_ponderado | sim |

### Por município, fora do conjunto público
| Tabela | Grão | Colunas principais | Pública? |
|---|---|---|---|
| `gold.fato_mercado_municipio_publico` | município × nível × regra (hoje só base, v2; 320 linhas) | cod_ibge, municipio, n_serventias, clt, passivo_todas, n_universo, passivo_universo, n_deficit, valor_descoberto; municípios com menos de 3 serventias somados numa linha (`agregado_lgpd`, `n_municipios_agregados`) | não (o painel não lê; contrato de LGPD no `src/quality/reconciliacao.py`) |
| `gold.fato_passivo_municipio` | município com 3 ou mais serventias × nível (319 municípios, 957 linhas) | cod_ibge, municipio, origem_distribuicao, n_vinculos_rais, passivo_medio_vinculo | não (o painel não lê) |

`origem_distribuicao` (D-022): `municipio` (o município tem 20 ou mais vínculos na RAIS) → `regiao` (a região imediata do IBGE tem 20 ou mais) → `estado` (MG inteiro). Na carga atual só aparecem `municipio` e `regiao`.

### Análises da mineração (Etapa 2, D-043 e D-044)
Gravadas pela etapa `etapa_analise` do `pipeline.py`, depois do gold, com as funções de `src/analise/tabelas.py` (o mesmo cálculo dos notebooks, conferido igual). Nenhuma muda as 25 tabelas acima nem os 10 números. As 6 agregadas estão no conjunto público desde a carga 2026-10-28; as 2 por serventia ficam só no gold da equipe (D-044: no público, só o perfil agregado dos grupos).

| Tabela | Grão | Colunas principais | Notebook | Pública? |
|---|---|---|---|---|
| `gold.analise_regras` | regra (10) | posicao, se, entao (`obrigada`), n_itens_se, serventias_com_se, serventias_com_se_e_entao, suporte, confianca, lift, referencia, ganho_sobre_referencia, melhoria, reamostragens_com_a_regra | 03 | proposta (agregada) |
| `gold.analise_grupos` | serventia agrupada (2.444) | cns, grupo, nome_grupo, grupo_alvo, k, semente | 04 | sim (por serventia, D-048) |
| `gold.analise_grupos_perfil` | grupo (6) | grupo, nome_grupo, grupo_alvo, n_serventias, receita_mediana, clt_mediano, atribuicoes_medianas, pct_vagas, obrigadas, passivo, passivo_obrigadas, com_deficit, deficit, pct_obrigadas, pct_deficit_mg, deficit_por_obrigada, pct_<atribuição> (6), pct_serventias, pct_obrigadas_mg, pct_passivo_obrigadas_mg | 04 e 09 | proposta (agregada, D-044) |
| `gold.analise_clt_modelo` | serventia do recorte do T1 (2.444) | cns, cod_ibge, regiao_intermediaria, receita_ref, n_atribuicoes, clt_declarado, clt_previsto_floresta, clt_previsto_poisson, clt_previsto_referencia, residuo_floresta, validacao | 06a | sim (por serventia, D-048) |
| `gold.analise_previsao` | bloco × período × variante × cenário do limite × medida (107) | bloco (`arrecadacao_mg`: semestres de 2026–27, 5 variantes; `mercado`: anos 2026–27, 2 variantes × 2 cenários do limite × 11 medidas), p10, central, p90, realizado, rotulo (sempre `projeção`) | 07 | proposta (agregada) |
| `gold.analise_tornado` | premissa (11) | suposicao, rotulo, grupo, valor_min, valor_base, valor_max (sim/não como 1/0), premio_no_min, premio_base, premio_no_max, amplitude, ordem | 08 | proposta (agregada) |
| `gold.analise_monte_carlo` | variante × medida (6) | variante (`independentes`, `patrimônio junto`), medida (deficit, importancia_segurada, premio), media, p05, p25, p50, p75, p95, canto_min, valor_base, canto_max, n_sorteios, semente, distribuicao | 08 | proposta (agregada) |
| `gold.analise_sensibilidade_metodo` | leitura alternativa (6) | chave (`base`, `receita_liquida`, `sem_saltos` (D-046: semestre de 2025 com salto grosseiro trocado pela média sem o salto), `t5_salario_estimado`, `t6_encolhimento`, `sem_regiao`), bloco, rotulo, n_universo, passivo_todas, passivo_universo, valor_descoberto, mercado_importancia_segurada, mercado_premio_emitido e `var_` de cada uma (variação sobre a base) | 08 | proposta (agregada, D-042 e D-044) |
| `gold.analise_capacidade_faixas` | faixa de meses de saldo (5) | faixa_meses (< 3 meses, 3 a 12 meses, > 12 meses, saldo ≤ 0, sem dado), serventias, obrigadas, passivo_obrigadas, deficit_modelo, pct_obrigadas, pct_deficit_modelo | 10 (M1) | proposta (agregada, D-045) |
| `gold.analise_capacidade_calibracao` | faixa de déficit (classe_2, classe_3, total) × horizonte de 6, 12 e 24 meses (9) | faixa_deficit, horizonte_meses, obrigadas, com_dado_bi, prob_deficit_modelo, prob_deficit_m1, pct_descoberto_modelo, pct_descoberto_m1, deficit_modelo, deficit_m1, premio_modelo, premio_m1 | 10 (M1) | proposta (agregada, D-045) |
| `gold.analise_sinistro` | leitura (sem e com a M1) × nível da P(fim) (6) | leitura, nivel_p_fim, p_fim, severidade_q, premio, sinistro_esperado, sinistralidade, indice_combinado, resultado_tecnico, apolices, premio_medio, sinistralidade_ses_base | 10 (M2) | proposta (agregada, D-045) |
| `gold.analise_premio_cenarios` | cenário do STF (3) | cenario, fracao_exigida, premio_base, premio_p05, premio_p50, premio_p95, descricao | 10 (M7) | proposta (agregada, D-045) |
| `gold.analise_premio_grade` | taxa × adesão (9) | taxa, adesao, premio (déficit da base) | 10 (M8) | proposta (agregada, D-045) |

As tabelas da M1 e da M2 usam o CSV do BI do CNJ no bronze, que é opcional: sem ele, o pipeline segue e essas tabelas ficam de fora, com aviso. Desde a D-046, nas tabelas da M1, as colunas `*_modelo` são as das premissas v3, que já vêm da M1 (por isso o déficit do modelo e o da M1 ficam quase iguais). A `analise_previsao_atualizada` (D-045) saiu na D-046, junto com a coleta de 28/10 de que ela dependia; as tabelas acima são publicadas desde a carga 2026-10-28 (tarde).

### Internas (nunca exibidas por serventia; só no pipeline, D-030)
- `gold.interno_serventia`: serventia × nível × regra, com passivo, classe, classe_faixa, peso_universo, motivo, n_deficit e valor_descoberto. O painel só mostra agregados.
- `gold.interno_dim_serventia`: receita de referência de 2025, origem_receita, semestres_validos, classe_v1 e classe_v2.
- `gold.interno_passivo_municipio`: o passivo médio por vínculo de todos os 851 municípios com serventia (o `fato_passivo_municipio` é o recorte com 3 ou mais serventias).
- `gold.interno_celulas_publicadas`: quais serventias compõem cada célula publicada (insumo do auditor).
- `gold.interno_auditoria`: iterações e células do auditor de ataque por diferença.

## Estado do pipeline (`estado.*`, só o pipeline grava)
- `premissas_versoes`: versao, criada_em, autor, origem, diff_json, conteudo_json. Uma versão por semente YAML (v001, v002); desde a D-034, o painel não cria versão.
- `cenarios_salvos`: id, nome, versao_premissas, cenario_stf, regra_classe, metodo_rateio, nivel, ajustes_json, resultado_json. Tabela antiga, vazia e não usada pelo painel desde a D-034; o pipeline não a cria mais, e ela some na próxima carga.
- `log_decisoes`: id (D-NNN), titulo, data, texto (espelho de `docs/decisoes.md`).

## Cenários salvos do painel (`data/painel_estado.json`, D-034)
- JSON `{"formato": 1, "cenarios": [...]}`; cada cenário: id, nome, criado_em, versao_premissas (a vigente no banco), premissas_alteradas (diff `{premissa: {de, para}}`), ajustes, cenario_stf, regra_classe, metodo_rateio, nivel, resultado. Fora do git, dos pacotes e do conjunto público (`src/cenarios.py`).

## Qualidade

### `qualidade.checagens`
tabela, checagem, severidade (erro / aviso), violacoes, detalhe, camada (silver / gold). Erro interrompe o pipeline. Desde a D-046, um aviso conta os semestres do ano de enquadramento com salto grosseiro (10 vezes acima ou abaixo da mediana dos 4 semestres anteriores da serventia); a classe continua com o valor declarado. Desde a D-048, outro aviso conta as serventias cuja classe mudaria se a receita de 2025 viesse do BI do CNJ, e não da API (10 na carga de 2026-10-28, entre elas a 035030); a classe continua pela API (D-010). Sem o CSV do BI no bronze, esse aviso sai com 0 e o motivo.

### `qualidade.reconciliacoes`
checagem, fonte_a, valor_a, fonte_b, valor_b, indicador (diferença % ou valor), tolerancia (`config/qualidade.yaml`), status (ok / aviso), detalhe. Valores arredondados a 10 casas a partir de 2026-10-28 (D-044), para o hash não mudar com a ordem das linhas; o status usa o valor sem arredondar.

### `qualidade.rec_municipio`
Por município: n_cnj, n_cnpj, clt_cnj, vinc_rais, dif_serventias, dif_empregados.

## Conjunto público (`data/publico/`, D-029)
- 39 Parquet com as tabelas públicas (19 do gold, entre elas a `serventia_publico`; 13 `analise_*`, duas delas por serventia desde a D-048; 2 do silver, 4 da qualidade e a versão vigente das premissas, `estado.premissas_vigente`), mais o `manifesto.json`. Versionado no git; gerado por `scripts/gerar_publico.py` (auditor, contratos de "sem dado pessoal" e de limiar, limite de tamanho).
- `manifesto.json`: carga, data e hora da execução, versão das premissas, limiar de LGPD, commit, fontes (data de referência, data de coleta e SHA-256 do bronze), exceções ao limiar e, por tabela, o arquivo, as linhas, o SHA-256 do arquivo e o **hash de conteúdo** (linhas ordenadas, sem os carimbos de execução). O `tests/test_publico.py` compara o gold local com esse hash.
- Sem banco local, o painel monta um banco temporário a partir desses arquivos (modo demonstração).
