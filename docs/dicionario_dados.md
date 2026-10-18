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

## Qualidade

### `qualidade.checagens`
tabela, checagem, severidade (erro / aviso), violacoes, detalhe, camada. Erro interrompe o pipeline.
