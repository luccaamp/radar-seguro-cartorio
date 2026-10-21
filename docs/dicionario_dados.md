# Dicionário de dados

Tabelas do banco local `data/radar.duckdb` (cópia em Parquet em `data/silver/` e `data/gold/`).
Gerado a partir de `uv run pipeline.py`. Nenhuma tabela silver ou gold tem nome, CPF ou contato de titular (SPEC §6).

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
cod_ibge (chave), cod_ibge6, uf, nome, nome_norm, microrregiao, mesorregiao, regiao_imediata, populacao, ano_populacao.

### `silver.susep_garantia` — SES, ramos 0775 (setor público) e 0776 (setor privado)
ano_mes, cod_entidade, cod_grupo, ramo e os valores mensais em R$ (premio_direto, premio_emitido2, premio_ganho, sinistro_ocorrido, desp_com etc.), como no `Ses_seguros.csv`.

### `silver.indice_preco`
indice (IPCA / INPC), ano_mes, numero_indice (base dez/1993 = 100).

### `silver.fonte_metadados` — uma linha por arquivo do bronze lido
fonte, arquivo, sha256, bytes, url, coletado_em, **data_referencia** (exibida no painel), observacao.

## Gold

Calculado por `src/motor.py` com a versão vigente das premissas. Níveis: `min`, `base`, `max` (todas as premissas no mesmo nível). Regras de classe: `v2` (R$ 300 mil, base) e `v1` (R$ 100 mil). Valores em R$ por ano.

### Públicas (lidas pelo painel)
| Tabela | Grão | Colunas principais |
|---|---|---|
| `gold.fato_mercado_uf` | UF × nível × regra × cenário do STF | n_serventias_ativas, clt, passivo_todas, n_universo, passivo_universo, n_deficit, valor_descoberto, bens_proprios, fianca, `mercado_*` e `seguradora_*` (importancia_segurada, premio_emitido, sinistro_esperado, comissao, despesa_administrativa, resultado_tecnico) |
| `gold.fato_mercado_municipio_publico` | município × nível × regra | n_serventias, clt, passivo_todas, n_universo, passivo_universo, n_deficit, valor_descoberto; municípios com menos de 3 serventias somados numa linha (`agregado_lgpd`, `n_municipios_agregados`) |
| `gold.fato_passivo_municipio` | município × nível | origem_distribuicao (municipio/estado), n_vinculos_rais, passivo_medio_vinculo |
| `gold.sensibilidade_rateio` | método de rateio | os mesmos totais de `fato_mercado_uf` (base, v2, mantém) |
| `gold.diferenca_regra_classe` | nível | universo, passivo, IS e prêmio em v2 e v1 |
| `gold.dim_municipio` | município | nome, mesorregião, população, n_serventias, clt |
| `gold.execucao` | regra | versao_premissas, executado_em, peso_classe_indeterminada_base, fator_inpc, mes_inpc_final, metodo_rateio, limiar_lgpd |

### Internas (nunca exibidas por serventia, SPEC §6)
- `gold.interno_serventia`: serventia × nível × regra, com passivo, classe, peso_universo, motivo, n_deficit e valor_descoberto. O painel só mostra agregados.
- `gold.interno_dim_serventia`: receita de referência de 2025, origem_receita, classe_v1 e classe_v2.

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
