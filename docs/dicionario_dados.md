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

O gold tem 25 tabelas: 20 sem o prefixo `interno_` e 5 internas. "Pública" = está no conjunto público (`config/publico.yaml`, `data/publico/`) e o painel lê; as 18 públicas passaram pelo auditor de ataque por diferença e pelos contratos de LGPD (D-026 a D-030). Conferido contra o banco em 2026-10-21.

### Totais, sensibilidades e execução
| Tabela | Grão | Colunas principais | Pública? |
|---|---|---|---|
| `gold.fato_mercado_uf` | UF × nível × regra × cenário do STF (18 linhas) | n_serventias_ativas, clt, passivo_todas, n_universo, n_indeterminadas_universo, passivo_universo, n_deficit, valor_descoberto, bens_proprios, fianca, `mercado_*` e `seguradora_*` (importancia_segurada, premio_emitido, sinistro_esperado, comissao, despesa_administrativa, resultado_tecnico) | sim |
| `gold.sensibilidade_rateio` | método de rateio (4) | os mesmos totais de `fato_mercado_uf` (base, v2, mantém) | sim |
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
tabela, checagem, severidade (erro / aviso), violacoes, detalhe, camada (silver / gold). Erro interrompe o pipeline.

### `qualidade.reconciliacoes`
checagem, fonte_a, valor_a, fonte_b, valor_b, indicador (diferença % ou valor), tolerancia (`config/qualidade.yaml`), status (ok / aviso), detalhe.

### `qualidade.rec_municipio`
Por município: n_cnj, n_cnpj, clt_cnj, vinc_rais, dif_serventias, dif_empregados.

## Conjunto público (`data/publico/`, D-029)
- 25 Parquet com as tabelas públicas (18 do gold, 2 do silver, 4 da qualidade e a versão vigente das premissas, `estado.premissas_vigente`), mais o `manifesto.json`. Versionado no git; gerado por `scripts/gerar_publico.py` (auditor, contratos de "sem dado pessoal" e de limiar, limite de tamanho).
- `manifesto.json`: carga, data e hora da execução, versão das premissas, limiar de LGPD, commit, fontes (data de referência, data de coleta e SHA-256 do bronze), exceções ao limiar e, por tabela, o arquivo, as linhas, o SHA-256 do arquivo e o **hash de conteúdo** (linhas ordenadas, sem os carimbos de execução). O `tests/test_publico.py` compara o gold local com esse hash.
- Sem banco local, o painel monta um banco temporário a partir desses arquivos (modo demonstração).
