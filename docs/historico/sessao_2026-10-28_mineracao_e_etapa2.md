# Sessão de 2026-10-28: fim da mineração (notebooks 07 e 09), Etapa 2 e as decisões dela

Relatório da sessão com a IA, pedida por `leticia-ribeirom`. Os detalhes de cada passo estão no `docs/diario.md` (entradas de 2026-10-28), as decisões na D-043 e na D-044 (`docs/decisoes.md`) e os erros da IA no `docs/erros_ia.md`.

**Resumo:**
- A mineração terminou: o notebook 07 foi revisado e o 09 foi criado.
- O pipeline passou a gravar 8 tabelas `gold.analise_*` com o que a mineração provou.
- As quatro questões da Etapa 2 foram decididas pela colaboradora e implementadas.
- Tudo foi rodado e conferido numa **cópia** do banco. Os 10 números não mudaram em nenhuma checagem.
- A carga oficial no banco real e a regeração do `data/publico/` **esperam o pedido do autor** (regra do `CLAUDE.md`).

## 1. Pedidos da sessão
1. **Concluir a mineração e executar a Etapa 2:**
   - Fase A: notebooks 07 e 09, com revisão de cientista de dados.
   - Fase B: Etapa 2 do `plano_projeto.md`, levando ao pipeline o que a mineração provou.
   - Regras: tudo numa cópia do banco; nenhum nome nem CPF; nenhum commit; parar se um dos 10 números mudasse.
2. **Tomar as quatro decisões recomendadas no fim**, explicar a falha do teste com dados reais e entregar este relatório.

## 2. Fase A: notebooks 07 e 09
- **Notebook 07 (previsão):** já estava feito. Rodado do zero, deu as mesmas saídas do commit. Cinco PNGs regravados pela rodada foram restaurados do original; um deles diferia só no anti-aliasing.
- **Notebook 09 (conclusões e lacunas), novo:**
  - Os 10 números oficiais lidos do banco.
  - **10 achados**, cada um com número, gráfico, frase e limitação.
  - Tabela de **8 lacunas**, com a fonte que resolveria cada uma.
  - Recomendação de achado × gráfico × página para o painel.
  - 10 PNGs `docs/qa/analises/09_*`.
  - Rodado duas vezes do zero numa cópia: saídas e PNGs idênticos.
- **Código reutilizável:**
  - `src/analise/tabelas.py`: uma função por tabela `gold.analise_*`, que repete os notebooks com a mesma semente.
  - `src/analise/conclusoes.py`: as contas do 09.
  - `src/analise/grupos.py`: `nomes_grupos`, com os nomes em `config/analise.yaml`.
- **Achados principais do 09:**
  - O prêmio base (R$ 368,7 mil) é 7,7% do teto teórico.
  - A faixa P5–P95 do Monte Carlo, de R$ 206 a 736 mil, é 5,2 vezes mais estreita que os cantos.
  - A taxa e a adesão ao seguro dominam a incerteza.
  - Os 10% maiores cartórios têm 53,5% do passivo das obrigadas.
  - O grupo "providas grandes" tem 67% do passivo das obrigadas.
  - A receita líquida do repasse tira 20% do universo.
  - Em 2027, o universo fica entre 1.124 e 1.244 obrigadas (projeção).
  - Os saltos grosseiros pesam 10% do total de 2026-1.
  - O CLT estimado pela receita erra pouco em MG inteiro (−2,5%), mas 7 das 13 regiões passam de ±10%.

## 3. Fase B: Etapa 2 (pipeline)
- **Etapa nova `pipeline.etapa_analise`**, depois do gold. Grava as tabelas `gold.analise_*` com as funções de `src/analise/tabelas.py`: o mesmo cálculo dos notebooks, conferido igual. A carga leva cerca de 6 minutos a mais.
- **Pipeline do zero numa cópia** (`--a-partir-de silver`): as 25 tabelas antigas com o mesmo hash de conteúdo e os 10 números iguais.
- **`scripts/gerar_publico.py`** ganhou `--banco` e `--destino`, para conferir o conjunto público numa cópia sem tocar no `data/publico/`.
- **Determinismo:**
  - A previsão da floresta aleatória passou a ser sequencial (antes variava no 14º dígito entre execuções).
  - Os valores sim/não da `analise_tornado` viraram 1/0 (a mistura de tipos parou a primeira carga; a troca atômica protegeu o banco).

## 4. Decisões tomadas pela colaboradora (D-044)
| Decisão | O que foi feito | Resultado conferido na cópia |
|---|---|---|
| Aprovar a D-043 e pedir a carga oficial | D-043 aprovada pela colaboradora. Carga oficial **não rodada**: exige pedido do autor | Carga completa numa cópia: 10 números iguais, 25 de 25 tabelas antigas iguais |
| Linhas da D-042 numa tabela `analise_*` nova | `gold.analise_sensibilidade_metodo`, 5 linhas; `sensibilidade_premissas` intacta | Receita líquida: universo 893,6 (−20,3%), prêmio R$ 337,4 mil (−8,5%). T5: +0,6%. T6: −1,6%. Reserva no estado inteiro: +5,9%. Iguais ao notebook 08 |
| Arredondar a `qualidade.reconciliacoes` a 10 casas | `valor_a`, `valor_b` e `indicador` arredondados em `src/quality/reconciliacao.py`; o status (ok/aviso) usa o valor sem arredondar | Tabela da cópia = tabela do banco real arredondada, com os mesmos status |
| No público, só o perfil agregado dos grupos | `gold.analise_grupos_perfil`, 6 linhas sem CNS; as tabelas por serventia ficam no gold da equipe | Grupos de 91 a 688 serventias; auditor e LGPD sem problema |

**Conjunto público da próxima carga.** Seis tabelas agregadas estão listadas em `config/publico.yaml`, na chave `tabelas_da_proxima_carga`:
- `analise_regras`
- `analise_grupos_perfil`
- `analise_previsao`
- `analise_tornado`
- `analise_monte_carlo`
- `analise_sensibilidade_metodo`

Gerado numa pasta temporária: 31 arquivos e 0,63 MB. O auditor de ataque por diferença achou 0 vazamentos em 989 células, a busca de CNS e de nomes do cadastro não achou nada, e as travas de LGPD passaram.

## 5. Por que um teste com dados reais falhava
O teste é `tests/test_pipeline.py::test_a_partir_do_silver_parquet_reproduz_o_conjunto_publico`. Ele refaz o gold a partir do silver em Parquet e compara o **hash exato** de cada tabela pública com o manifesto do `data/publico/`. A tabela `qualidade.reconciliacoes` saía com outro hash, por estes motivos:
- **Ordem sem garantia:** a consulta que cruza CNJ, CNPJ e RAIS por município não tem `ORDER BY`. Por isso, a ordem das linhas depende de como o DuckDB executa as junções e de como o silver foi lido (do bronze na carga de 19/10, do Parquet no teste).
- **A soma depende da ordem:** a correlação em log é uma soma em ponto flutuante, que muda no último dígito conforme a ordem dos termos. Medido: em 20 ordens sorteadas das mesmas 755 linhas, saíram 8 valores diferentes, com até 1e-15 de diferença. Entre a carga de 19/10 e o teste, a diferença foi de 2,8e-15 (0,9645209993702… nos dois casos).
- **O hash é exato:** qualquer dígito diferente muda o hash, e o teste falha, embora o valor seja o mesmo para qualquer fim prático.
- **Já existia antes desta sessão:** o código do commit `7122a28`, sem nada desta sessão, falha igual.

**Correção:** arredondar a 10 casas. **Até a carga oficial**, o teste continua falhando: o `data/publico/` versionado ainda tem o valor sem arredondar. Depois da carga e da regeração do público, os dois lados ficam arredondados e o teste passa. Os 10 números e as 25 tabelas do gold nunca foram afetados.

## 6. Números de referência
Iguais em todas as checagens: início, fim da Fase A, fim da Fase B e depois das decisões. O banco real ficou com o mesmo SHA-256 (`3e055af4…`), e os 197 arquivos de `data/`, com o mesmo md5.

| Nº | Número | Valor |
|---|---|---|
| 1 | Serventias ativas | 2.525 |
| 2 | Empregados CLT | 12.134 |
| 3 | Obrigadas | 1.121,31 |
| 4 | Passivo (todas) | R$ 311.866.725 |
| 5 | Passivo (obrigadas) | R$ 238.104.261 |
| 6 | Com déficit | 486,02 |
| 7 | Déficit | R$ 36.873.874 |
| 8 | IS do mercado | R$ 18.436.937 |
| 9 | Prêmio anual | R$ 368.738,74 |
| 10 | Teto teórico | R$ 4.762.085 |

## 7. Testes
- **Suíte padrão:** 237 aprovados, 2 ignorados e 85 fora da suíte padrão (`dados_reais`, painel e afins). Inclui `test_notebooks.py`, que procura CPF nos notebooks.
- **Testes com dados reais** (`test_pipeline.py`, `test_analise_tabelas.py`, `test_analise_previsao.py`, numa cópia): 5 aprovados (inclui o novo `test_sensibilidade_metodo_repete_o_notebook_08`) e 1 falha esperada, `test_a_partir_do_silver_parquet_reproduz_o_conjunto_publico`. A falha continua só na `qualidade.reconciliacoes`: o lado novo agora sai arredondado, e o manifesto do `data/publico/` ainda tem o valor sem arredondar. Ela some com a regeração do público na carga oficial (seção 5). O teste não foi mudado nem desativado. Duração: 23 minutos.
- **ruff:** sem erro no código mudado.

## 8. Erros da IA nesta sessão (registrados no `docs/erros_ia.md`)
- O diário dizia que a `analise_previsao` tinha 99 linhas; são 107.
- O título de um gráfico do 09 dizia "na maioria até ±10%", mas 7 das 13 regiões passam disso.
- A previsão da floresta aleatória não dava o mesmo resultado em duas execuções.
- A `analise_tornado` tinha tipo misto, o que parou a primeira carga da cópia.
- Um documento (`plano_mineracao.md`) foi editado por script de substituição, e não pela ferramenta de edição.

## 9. O que falta (para o autor)
1. **Carga oficial**, nesta ordem:
   1. guardar uma cópia do banco atual fora do repositório;
   2. rodar `uv run pipeline.py --a-partir-de silver`;
   3. no `config/publico.yaml`, passar as 6 linhas de `tabelas_da_proxima_carga` para `tabelas`;
   4. rodar `uv run python scripts/gerar_publico.py`;
   5. rodar `uv run python scripts/linha_de_base.py <pasta fora do repositório>`;
   6. rodar `uv run pytest -m dados_reais`.
2. **Etapa 3 (painel):** começar pelo inventário de achados, a partir da seção 4 do notebook 09.
3. **Pendências do autor:** aprovar a D-042 (como mostrar a faixa do prêmio) e decidir sobre as melhorias M1 a M10. A M1 e a M2 responderiam à pergunta 9, sobre o lucro da seguradora; quando uma delas entrar, o 09 é rodado de novo.

## 10. Arquivos alterados (sem commit)
- **Novos:**
  - `notebooks/09_conclusoes_lacunas.ipynb`
  - 10 PNGs `docs/qa/analises/09_*.png`
  - `src/analise/tabelas.py`
  - `src/analise/conclusoes.py`
  - `tests/test_analise_tabelas.py`
  - este relatório
- **Modificados:**
  - Código: `pipeline.py`, `scripts/gerar_publico.py`, `src/analise/grupos.py`, `src/analise/regressao.py`, `src/analise/sensibilidade.py`, `src/quality/reconciliacao.py`
  - Config: `config/analise.yaml`, `config/publico.yaml`
  - Docs: `docs/ESTADO_ATUAL.md`, `docs/diario.md`, `docs/erros_ia.md`, `docs/decisoes.md`, `docs/dicionario_dados.md`, `docs/SPEC.md`, `docs/plano_projeto.md`, `docs/plano_mineracao.md`, `docs/historico/INDICE.md`
